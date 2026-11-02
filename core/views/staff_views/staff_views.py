from django.contrib.auth.hashers import make_password
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import Staff, Users
from core.permissions import owner_only_response
from core.services.staff_photo import delete_staff_photo
from core.serializers.staff_serializers.staff_serializers import (
    StaffCreateSerializer,
    StaffSerializer,
    StaffUpdateSerializer,
)


class StaffListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="👥 Çalışanları (kuaförleri) listele (sadece firma sahibi)",
        tags=["STAFF"],
    )
    def get(self, request):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        staff = (
            Staff.objects.filter(company=request.user.company)
            .select_related("user")
            .order_by("-is_active", "user__name")
        )
        return Response(StaffSerializer(staff, many=True).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="➕ Yeni çalışan (kuaför) oluştur (sadece firma sahibi)",
        operation_description=(
            "Çalışan; ad, soyad, e-posta ve şifreyle oluşturulur. "
            "Bu e-posta ve şifreyle panele girer, sadece kendi randevularını ve hediyelerini görür."
        ),
        request_body=StaffCreateSerializer,
        responses={201: StaffSerializer, 400: "Geçersiz veri veya e-posta kullanımda", 403: "Yetkisiz"},
        tags=["STAFF"],
    )
    def post(self, request):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        company = request.user.company
        serializer = StaffCreateSerializer(data=request.data, context={"company": company})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            user = Users.objects.create(
                name=data["name"].strip(),
                surname=data["surname"].strip(),
                email=data["email"],
                phone="",
                password=make_password(data["password"]),
                company=company,
                is_admin=False,
            )
            staff = Staff.objects.create(company=company, user=user)

        return Response(StaffSerializer(staff).data, status=status.HTTP_201_CREATED)


class StaffDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_staff(self, request, staff_id):
        try:
            return Staff.objects.select_related("user", "company").get(
                id=staff_id, company=request.user.company
            )
        except Staff.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="✏️ Çalışanı güncelle (sadece firma sahibi)",
        operation_description=(
            "Ad, soyad, e-posta, yeni şifre (boş bırakılırsa değişmez) ve aktif/pasif durumu güncellenebilir."
        ),
        request_body=StaffUpdateSerializer,
        responses={200: StaffSerializer, 400: "Geçersiz veri", 403: "Yetkisiz", 404: "Çalışan bulunamadı"},
        tags=["STAFF"],
    )
    def patch(self, request, staff_id):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        staff = self._get_staff(request, staff_id)
        if not staff:
            return Response({"error": "Çalışan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = StaffUpdateSerializer(data=request.data, context={"staff": staff})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            user = staff.user
            if "name" in data:
                user.name = data["name"].strip()
            if "surname" in data:
                user.surname = data["surname"].strip()
            if "email" in data:
                user.email = data["email"]
            if data.get("password"):
                user.password = make_password(data["password"])
            user.save()

            if "is_active" in data:
                staff.is_active = data["is_active"]
                staff.save(update_fields=["is_active", "updated_at"])

        return Response(StaffSerializer(staff).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="🗑️ Çalışanı sil (sadece firma sahibi)",
        operation_description=(
            "Randevusu olan çalışan silinemez (geçmiş kayıtlar bozulmasın), önce pasif yapılmalıdır."
        ),
        responses={204: "Silindi", 400: "Randevusu var", 403: "Yetkisiz", 404: "Çalışan bulunamadı"},
        tags=["STAFF"],
    )
    def delete(self, request, staff_id):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        staff = self._get_staff(request, staff_id)
        if not staff:
            return Response({"error": "Çalışan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        if staff.meetings.exists():
            return Response(
                {"error": "Bu çalışanın randevuları var. Silmek yerine pasif yapabilirsiniz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photo = staff.photo
        with transaction.atomic():
            user = staff.user
            staff.delete()
            user.delete()

        delete_staff_photo(photo)
        return Response(status=status.HTTP_204_NO_CONTENT)
