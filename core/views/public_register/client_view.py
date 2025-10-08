from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Companies, Users
from core.serializers import PublicRegisterSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class PublicRegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="Müşteri kayıt formu (şifresiz, public endpoint)",
        operation_description=(
            "Firma slug'ına göre şirket bulunur. "
            "Formdan gelen 'name', 'surname' ve 'email' bilgileriyle müşteri kaydedilir. "
            "Aynı firmada aynı email varsa yeni kayıt oluşturulmaz, mevcut kullanıcı döndürülür."
        ),
        request_body=PublicRegisterSerializer,
        responses={
            201: openapi.Response(
                description="Yeni müşteri başarıyla oluşturuldu.",
                examples={
                    "application/json": {
                        "message": "Yeni kayıt oluşturuldu.",
                        "user": {
                            "id": 12,
                            "name": "Ahmet",
                            "surname": "Yılmaz",
                            "email": "ahmet@example.com",
                            "company": "Yusuf's Kuaför",
                            "company_id": 5
                        }
                    }
                },
            ),
            200: openapi.Response(
                description="Müşteri zaten kayıtlı, mevcut kullanıcı döndürüldü.",
                examples={
                    "application/json": {
                        "message": "Kayıt zaten mevcut, devam edebilirsiniz.",
                        "user": {
                            "id": 12,
                            "name": "Ahmet",
                            "surname": "Yılmaz",
                            "email": "ahmet@example.com",
                            "company": "Yusuf's Kuaför",
                            "company_id": 5
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Eksik veya geçersiz veri gönderildi.",
                examples={
                    "application/json": {"error": {"email": ["Bu alan gereklidir."]}}
                },
            ),
            404: openapi.Response(
                description="Firma bulunamadı.",
                examples={"application/json": {"error": "Firma bulunamadı."}},
            ),
        },
    )
    def post(self, request, slug):
        # 🔍 Firma kontrolü
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response(
                {"error": "Firma bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        name = serializer.validated_data.get('name')
        surname = serializer.validated_data.get('surname')
        email = serializer.validated_data.get('email')

        # 🔹 Kullanıcı oluştur veya mevcut olanı getir
        user, created = Users.objects.get_or_create(
            email=email,
            company=company,
            defaults={
                "name": name,
                "surname": surname,
                # Şifre zorunlu ama kullanılmayacak; hash'li sahte şifre oluşturuyoruz
                "password": make_password("guest_user"),
                "is_admin": False,
                "is_show_wheel": True,
            }
        )

        msg = "Yeni kayıt oluşturuldu." if created else "Kayıt zaten mevcut, devam edebilirsiniz."

        return Response({
            "message": msg,
            "user": {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "company": company.title,
                "company_id": company.id,
            }
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
