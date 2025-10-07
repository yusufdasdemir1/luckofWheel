from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify
from django.contrib.auth.hashers import make_password
from drf_yasg.utils import swagger_auto_schema
from core.serializers import RegisterSerializer
from core.models import Users, Companies


class RegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="Yeni admin kullanıcı (ve şirket) oluşturur",
        request_body=RegisterSerializer,
        responses={201: "Kullanıcı ve şirket oluşturuldu", 400: "Geçersiz veri"},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        email = data.get('company_email')

        if Companies.objects.filter(email=email).exists():
            return Response(
                {"error": "Bu e-posta adresine sahip bir şirket zaten kayıtlı."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Şirket oluştur
        company = Companies.objects.create(
            title=data["company_title"],
            description=data.get("company_description", ""),
            email=data["company_email"],
            phone=data.get("company_phone", ""),
            show_before_meeting=data.get("show_before_meeting", False),
            slug=slugify(data["company_title"]),
        )

        # Kullanıcı oluştur (is_admin=True)
        user = Users.objects.create(
            name=data["name"],
            surname=data["surname"],
            email=data["company_email"],
            password=make_password(data["password"]),
            company=company,
            is_admin=True,
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
