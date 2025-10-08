from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.serializers import RegisterSerializer
from core.models import Users, Companies
from django.db import IntegrityError, transaction
from django.contrib.auth.hashers import make_password

class RegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="Yeni şirket ve admin kaydı oluşturur",
        operation_description=(
            "Yeni bir firma kaydı oluşturur ve otomatik olarak admin kullanıcı atar.\n\n"
            "**company_email** ve **phone** alanları unique (benzersiz) olmalıdır."
        ),
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="Şirket ve admin başarıyla oluşturuldu.",
                examples={
                    "application/json": {
                        "message": "Şirket ve admin başarıyla oluşturuldu.",
                        "user": {
                            "id": 1,
                            "name": "Yusuf",
                            "surname": "Kaytan",
                            "email": "admin@kuafor.com",
                            "is_admin": True
                        },
                        "company": {
                            "id": 1,
                            "title": "Yusuf'un Kuaförü",
                            "slug": "yusufun-kuaforu"
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Eksik veya geçersiz veri gönderildi.",
                examples={
                    "application/json": {
                        "error": "Bu telefon veya e-posta adresi zaten kullanımda."
                    }
                },
            ),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        email = data.get("company_email")
        phone = data.get("company_phone")

        if Companies.objects.filter(email=email).exists():
            return Response(
                {"error": "Bu e-posta adresine sahip bir şirket zaten kayıtlı."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Companies.objects.filter(phone=phone).exists():
            return Response(
                {"error": "Bu telefon numarasına sahip bir şirket zaten kayıtlı."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                company = Companies.objects.create(
                    title=data["company_title"],
                    description=data.get("company_description", ""),
                    email=email,
                    phone=phone,
                    show_before_meeting=data.get("show_before_meeting", False),
                    slug=slugify(data["company_title"]),
                )

                user = Users.objects.create(
                    name=data["name"],
                    surname=data["surname"],
                    email=email,
                    password=make_password(data["password"]),
                    company=company,
                    is_admin=True,
                )
        except IntegrityError as e:
            return Response(
                {"error": "Bu telefon veya e-posta adresi zaten kullanımda."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "message": "Şirket ve admin başarıyla oluşturuldu.",
            "user": {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "is_admin": user.is_admin,
            },
            "company": {
                "id": company.id,
                "title": company.title,
                "slug": company.slug,
            }
        }, status=status.HTTP_201_CREATED)