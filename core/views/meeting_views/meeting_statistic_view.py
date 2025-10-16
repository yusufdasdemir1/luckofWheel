from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings
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

        # 🧾 Temel sayısal istatistikler
        total_meetings = Meetings.objects.filter(company=company).count()
        active_meetings = Meetings.objects.filter(company=company, is_active=True).count()
        cancelled_meetings = Meetings.objects.filter(company=company, is_active=False).count()

        # 💈 En çok tercih edilen hizmet
        top_service = (
            Meetings.objects.filter(company=company)
            .values("service_title")
            .annotate(count=Count("service_title"))
            .order_by("-count")
            .first()
        )

        # 👤 En çok randevu alan müşteri
        top_user = (
            Meetings.objects.filter(company=company)
            .values("user__name", "user__surname")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )

        # 💰 Toplam gelir (sadece aktif randevulardan)
        total_income = (
            Meetings.objects.filter(company=company, is_active=True)
            .aggregate(total=Sum("service_price"))["total"] or 0
        )

        # ✅ Response
        data = {
            "total_meetings": total_meetings,
            "active_meetings": active_meetings,
            "cancelled_meetings": cancelled_meetings,
            "total_income": f"{total_income} ₺",
            "top_service": top_service["service_title"] if top_service else None,
            "top_service_count": top_service["count"] if top_service else 0,
            "top_user": (
                f"{top_user['user__name']} {top_user['user__surname']}"
                if top_user else None
            ),
            "top_user_meeting_count": top_user["total"] if top_user else 0,
        }

        return Response(data, status=status.HTTP_200_OK)
