from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.serializers import CompanyUpdateSerializer
from core.models import Companies, Users
from django.utils.text import slugify

class CompanyUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🏢 Şirket bilgilerini güncelle (slug bazlı, sadece admin)",
        tags=["ADMIN ACTIONS"],
        request_body=CompanyUpdateSerializer,
        responses={
            200: "Güncelleme başarılı",
            403: "Yetkisiz kullanıcı",
            404: "Firma bulunamadı"
        },
    )
    def patch(self, request, company_slug):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔎 Firma slug'ına göre getir
        try:
            company = Companies.objects.get(slug=company_slug)
        except Companies.DoesNotExist:
            return Response(
                {"error": "Firma bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🧩 Sadece kendi firmasını güncelleyebilsin
        if company != user.company:
            return Response(
                {"error": "Kendi firmanız dışında işlem yapamazsınız."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ Verileri işle
        serializer = CompanyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(company, field, value)

        if "title" in serializer.validated_data:
            company.slug = slugify(serializer.validated_data["title"])

        company.save()

        # 🔁 Eğer e-posta değiştiyse admin kullanıcının e-postasını da güncelle
        if "email" in serializer.validated_data:
            new_email = serializer.validated_data["email"]
            Users.objects.filter(company=company, is_admin=True).update(email=new_email)



        return Response(
            {
                "message": "Şirket bilgileri başarıyla güncellendi.",
                "company": {
                    "title": company.title,
                    "description": company.description,
                    "email": company.email,
                    "phone": company.phone,
                    "is_show_wheel": company.is_show_wheel,
                    "show_before_meeting": company.show_before_meeting,
                    "spin_cooldown_hours": company.spin_cooldown_hours,
                }
            },
            status=status.HTTP_200_OK
        )
