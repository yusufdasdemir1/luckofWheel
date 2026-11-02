from django.db import models
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Companies, Users
from core.serializers.public_serializers.public_serializers import PublicRegisterSerializer
from core.services.spin import spin_status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class PublicRegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="🎡 Müşteri formu doldur (public endpoint)",
        operation_description=(
            "Bu endpoint müşteriyi kaydeder (ya da mevcut müşteriyi bulur) ve çark hakkını bildirir.\n\n"
            "1️⃣ Firma slug’ına göre firma bulunur.\n"
            "2️⃣ Aynı firmada aynı e-posta veya telefon başka biriyle kayıtlıysa hata döner.\n"
            "3️⃣ Çark burada çevrilmez; cevapta müşterinin çark hakkı (`can_spin`, `remaining_seconds`) döner. "
            "Çark `/public/spin/<slug>` ile müşteri butona basınca çevrilir.\n\n"
            "**Not:** Şifre alanı otomatik olarak `guest_user` olarak hash'lenir."
        ),
        request_body=PublicRegisterSerializer,
        responses={
            201: openapi.Response(
                description="Müşteri kaydedildi, çark hakkı döndü.",
                examples={
                    "application/json": {
                        "message": "Kayıt tamamlandı.",
                        "company": "Beauty of Yusuf",
                        "wheel_mode": "before",
                        "can_spin": False,
                        "remaining_seconds": 93600,
                    }
                },
            ),
            400: openapi.Response(
                description="Hatalı istek veya e-posta/telefon başkasına ait.",
                examples={
                    "application/json": {
                        "error": "Bu e-posta adresi bu firmada zaten kayıtlı. Lütfen farklı bir e-posta girin."
                    }
                },
            ),
            404: openapi.Response(
                description="Firma bulunamadı.",
                examples={"application/json": {"error": "Firma bulunamadı."}},
            ),
        },
        tags=["PUBLIC"]
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
        email = serializer.validated_data["email"].strip().lower()
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

        # Burada çevirme yoktur: sadece müşteri kaydı ve çark hakkı bilgisi döner.
        # Çark `/public/spin/<slug>` ile müşteri butona basınca çevrilir.
        return Response(
            {
                "message": "Kayıt tamamlandı.",
                "company": company.title,
                "wheel_mode": company.wheel_mode,
                **spin_status(user, company),
            },
            status=status.HTTP_201_CREATED,
        )
