from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Companies, Staff
from core.serializers.staff_serializers.staff_serializers import (
    StaffPublicSerializer,
    WorkingHoursSerializer,
)
from core.services.working_hours import hours_for_company


class PublicStaffListView(APIView):
    @swagger_auto_schema(
        operation_summary="💇 Firmanın aktif çalışanları (public)",
        operation_description="Müşteri randevu alırken kuaför seçebilsin diye sadece ad ve soyad döner.",
        responses={200: StaffPublicSerializer(many=True), 404: "Firma bulunamadı"},
        tags=["PUBLIC"],
    )
    def get(self, request, slug):
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        staff = (
            Staff.objects.filter(company=company, is_active=True)
            .select_related("user")
            .order_by("user__name", "user__surname")
        )
        return Response(StaffPublicSerializer(staff, many=True).data, status=status.HTTP_200_OK)


class PublicWorkingHoursView(APIView):
    @swagger_auto_schema(
        operation_summary="🕘 Firmanın çalışma saatleri (public)",
        operation_description="Her zaman 7 gün döner. weekday: 0=Pazartesi ... 6=Pazar.",
        responses={200: WorkingHoursSerializer(many=True), 404: "Firma bulunamadı"},
        tags=["PUBLIC"],
    )
    def get(self, request, slug):
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        hours = hours_for_company(company)
        return Response(WorkingHoursSerializer(hours, many=True).data, status=status.HTTP_200_OK)
