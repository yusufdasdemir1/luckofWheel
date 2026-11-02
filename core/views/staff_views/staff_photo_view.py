from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import Staff
from core.permissions import owner_only_response
from core.serializers.staff_serializers.staff_serializers import StaffSerializer
from core.services.staff_photo import PhotoError, delete_staff_photo, save_staff_photo


class StaffPhotoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def _get_staff(self, request, staff_id):
        try:
            return Staff.objects.select_related("user").get(
                id=staff_id, company=request.user.company
            )
        except Staff.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="📷 Çalışan fotoğrafı yükle (sadece firma sahibi)",
        operation_description=(
            "`photo` alanında png/jpg/webp görsel gönderilir (en fazla 5 MB). "
            "Görsel kareye kırpılıp 600x600 webp olarak kaydedilir; eski fotoğraf varsa silinir."
        ),
        manual_parameters=[
            openapi.Parameter("photo", openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
        ],
        responses={200: StaffSerializer, 400: "Geçersiz görsel", 403: "Yetkisiz", 404: "Çalışan bulunamadı"},
        tags=["STAFF"],
    )
    def post(self, request, staff_id):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        staff = self._get_staff(request, staff_id)
        if not staff:
            return Response({"error": "Çalışan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        uploaded = request.FILES.get("photo")
        if not uploaded:
            return Response({"error": "Fotoğraf dosyası gerekli."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_photo = save_staff_photo(uploaded)
        except PhotoError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        old_photo = staff.photo
        staff.photo = new_photo
        staff.save(update_fields=["photo", "updated_at"])
        delete_staff_photo(old_photo)

        return Response(StaffSerializer(staff).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="🗑️ Çalışan fotoğrafını kaldır (sadece firma sahibi)",
        responses={200: StaffSerializer, 403: "Yetkisiz", 404: "Çalışan bulunamadı"},
        tags=["STAFF"],
    )
    def delete(self, request, staff_id):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        staff = self._get_staff(request, staff_id)
        if not staff:
            return Response({"error": "Çalışan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        old_photo = staff.photo
        staff.photo = ""
        staff.save(update_fields=["photo", "updated_at"])
        delete_staff_photo(old_photo)

        return Response(StaffSerializer(staff).data, status=status.HTTP_200_OK)
