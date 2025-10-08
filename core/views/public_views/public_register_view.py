from django.db import models, IntegrityError
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Companies, Users, Gifts, EarnedWins
from core.serializers import PublicRegisterSerializer
import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class PublicRegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="🎡 Müşteri formu doldur + spin çevir (public endpoint)",
        operation_description=(
            "Bu endpoint müşterinin form doldurup çark çevirmesini sağlar.\n\n"
            "1️⃣ Firma slug’ına göre firma bulunur.\n"
            "2️⃣ Aynı firmada aynı e-posta veya telefon kayıtlıysa hata döner.\n"
            "3️⃣ 48 saat dolmadan spin çevirmeye çalışılırsa kalan süre belirtilir.\n"
            "4️⃣ Rastgele bir hediye seçilir ve `EarnedWins` tablosuna kaydedilir.\n\n"
            "**Not:** Şifre alanı otomatik olarak `guest_user` olarak hash'lenir."
        ),
        request_body=PublicRegisterSerializer,
        responses={
            201: openapi.Response(
                description="Spin sonucu başarıyla döndürüldü.",
                examples={
                    "application/json": {
                        "message": "Tebrikler! %20 indirim kazandınız 🎉",
                        "gift_views": "%20 indirim",
                        "company": "Beauty of Yusuf",
                        "next_spin_available_in_hours": 48,
                    }
                },
            ),
            400: openapi.Response(
                description="Hatalı istek veya spin süresi dolmadı.",
                examples={
                    "application/json": {
                        "error": "Henüz spin hakkınız yenilenmedi. 1 gün 3 saat sonra tekrar deneyin."
                    }
                },
            ),
            403: openapi.Response(
                description="Çark admin tarafından kapatıldı.",
                examples={
                    "application/json": {
                        "error": "Bu kullanıcı için çark geçici olarak kapatılmış. Lütfen firma ile iletişime geçin."
                    }
                },
            ),
            404: openapi.Response(
                description="Firma bulunamadı.",
                examples={"application/json": {"error": "Firma bulunamadı."}},
            ),
        },
    )
    def post(self, request, slug):
        # Firma kontrolü
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        name = serializer.validated_data["name"]
        surname = serializer.validated_data["surname"]
        email = serializer.validated_data["email"]
        phone = serializer.validated_data["phone"]

        # ❗ 1️⃣ Email veya phone çakışma kontrolü
        duplicate_user = Users.objects.filter(company=company).filter(
            models.Q(email=email) | models.Q(phone=phone)
        ).first()

        if duplicate_user:
            if duplicate_user.email == email and duplicate_user.phone == phone:
                # ✅ Aynı kişi — spin süresi kontrol edilecek
                user = duplicate_user
            elif duplicate_user.email == email:
                return Response(
                    {"error": "Bu e-posta adresi bu firmada zaten kayıtlı. Lütfen farklı bir e-posta girin."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif duplicate_user.phone == phone:
                return Response(
                    {"error": "Bu telefon numarası bu firmada zaten kayıtlı. Lütfen farklı bir numara girin."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # ✅ Yeni kullanıcı oluştur
            user = Users.objects.create(
                name=name,
                surname=surname,
                email=email,
                phone=phone,
                password=make_password("guest_user"),
                company=company,
                is_admin=False,
            )

        # ❌ Eğer admin çarkı kapattıysa
        if not company.is_show_wheel:
            return Response(
                {"error": "Bu şirket için çark geçici olarak kapatılmış. Lütfen firma ile iletişime geçin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 🔄 Son spin kontrolü (48 saat)
        last_spin = EarnedWins.objects.filter(user=user).order_by("-created_at").first()
        if last_spin:
            elapsed_hours = (timezone.now() - last_spin.created_at).total_seconds() / 3600
            if elapsed_hours < 48:
                remaining_hours = 48 - elapsed_hours
                days = int(remaining_hours // 24)
                hours = int(remaining_hours % 24)
                if days > 0 and hours > 0:
                    msg = f"Henüz spin hakkınız yenilenmedi. {days} gün {hours} saat sonra tekrar deneyin."
                elif days > 0:
                    msg = f"Henüz spin hakkınız yenilenmedi. {days} gün sonra tekrar deneyin."
                else:
                    msg = f"Henüz spin hakkınız yenilenmedi. {hours} saat sonra tekrar deneyin."
                return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        # 🎁 Rastgele ödül seçimi
        gifts = Gifts.objects.filter(company=company)
        if not gifts.exists():
            return Response({"error": "Bu firmaya ait hediye tanımlı değil."}, status=status.HTTP_400_BAD_REQUEST)

        total_chance = sum(g.chance for g in gifts)
        rand = random.uniform(0, total_chance)
        cumulative = 0
        selected_gift = None
        for gift in gifts:
            cumulative += gift.chance
            if rand <= cumulative:
                selected_gift = gift
                break

        if not selected_gift:
            selected_gift = random.choice(gifts)

        # 🧾 Kaydet
        EarnedWins.objects.create(user=user, gift=selected_gift,company=company)

        return Response(
            {
                "message": f"Tebrikler! {selected_gift.title} kazandınız 🎉",
                "gift_views": selected_gift.title,
                "company": company.title,
                "next_spin_available_in_hours": 48,
            },
            status=status.HTTP_201_CREATED,
        )
