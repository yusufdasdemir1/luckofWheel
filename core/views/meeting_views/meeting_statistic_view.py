from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings,MeetingStatus
from django.db.models import Count, Sum


class MeetingStatisticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="📊 Şirkete ait randevu istatistikleri (sadece admin)",
        responses={200: "İstatistikler başarıyla getirildi."},
        tags=["MEETINGS"]
    )
    def get(self, request):
        user = request.user

        # 🔒 Sadece admin erişebilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        company = user.company

        #Temel sayısal istatistikler
        total_meetings = Meetings.objects.filter(company=company).count()
        waiting_meetings = Meetings.objects.filter(
            company=company,
            status=MeetingStatus.WAITING
        ).count()

        cancelled_meetings = Meetings.objects.filter(
            company=company,
            status=MeetingStatus.CANCELED
        ).count()

        arrived_meetings = Meetings.objects.filter(
            company=company,
            status=MeetingStatus.ARRIVED
        ).count()

        #En çok tercih edilen hizmet
        top_service = (
            Meetings.objects.filter(company=company)
            .values("service_title")
            .annotate(count=Count("service_title"))
            .order_by("-count")
            .first()
        )

        #Toplam gelir (sadece aktif randevulardan)
        total_income = (
            Meetings.objects.filter(company=company, status=MeetingStatus.ARRIVED)
            .aggregate(total=Sum("service_price"))["total"] or 0
        )

        #Response
        data = {
            "total_meetings": total_meetings,
            "waiting_meetings": waiting_meetings,
            "arrived_meetings": arrived_meetings,
            "cancelled_meetings": cancelled_meetings,
            "total_income": f"{total_income} ₺",

            "top_service": top_service["service_title"] if top_service else None,
            "top_service_count": top_service["count"] if top_service else 0,
        }

        return Response(data, status=status.HTTP_200_OK)
