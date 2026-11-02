from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import WorkingHours
from core.permissions import owner_only_response
from core.serializers.staff_serializers.staff_serializers import (
    WorkingHoursSerializer,
    WorkingHoursUpdateSerializer,
)
from core.services.working_hours import hours_for_company


class CompanyWorkingHoursView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🕘 Firmanın haftalık çalışma saatleri (sadece firma sahibi)",
        operation_description="Her zaman 7 günü döner. weekday: 0=Pazartesi ... 6=Pazar.",
        responses={200: WorkingHoursSerializer(many=True), 403: "Yetkisiz"},
        tags=["WORKING HOURS"],
    )
    def get(self, request):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        hours = hours_for_company(request.user.company)
        return Response(WorkingHoursSerializer(hours, many=True).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="💾 Çalışma saatlerini kaydet (sadece firma sahibi)",
        operation_description="Haftanın 7 günü birlikte gönderilir: `{\"hours\": [{weekday, is_closed, opens, closes}, ...]}`.",
        request_body=WorkingHoursUpdateSerializer,
        responses={200: WorkingHoursSerializer(many=True), 400: "Geçersiz veri", 403: "Yetkisiz"},
        tags=["WORKING HOURS"],
    )
    def put(self, request):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        serializer = WorkingHoursUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = request.user.company

        with transaction.atomic():
            for item in serializer.validated_data["hours"]:
                WorkingHours.objects.update_or_create(
                    company=company,
                    weekday=item["weekday"],
                    defaults={
                        "is_closed": item["is_closed"],
                        "opens": item["opens"],
                        "closes": item["closes"],
                    },
                )

        hours = hours_for_company(company)
        return Response(WorkingHoursSerializer(hours, many=True).data, status=status.HTTP_200_OK)
