import re
from decimal import Decimal

from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import Meetings, MeetingStatus
from core.permissions import NO_ACCESS_MESSAGE, scope_for

# Fiyat metin alanıdır ("200.00", "2000-3000"): sadece tek bir sayı olanlar toplanabilir
NUMERIC_PRICE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*$")


def _income(arrived_meetings):
    """(toplam gelir, toplanamayan randevu sayısı). "2000-3000" gibi aralıklar toplama katılmaz."""
    total = Decimal("0")
    skipped = 0
    for price in arrived_meetings.values_list("service_price", flat=True):
        match = NUMERIC_PRICE.match(price or "")
        if match:
            total += Decimal(match.group(1).replace(",", "."))
        else:
            skipped += 1
    return total, skipped


class MeetingStatisticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="📊 Randevu istatistikleri (firma sahibi: tüm firma, çalışan: sadece kendisi)",
        operation_description=(
            "Firma sahibi tüm firmanın rakamlarını ve çalışan bazlı dağılımı (`by_staff`) görür. "
            "Çalışan sadece kendi randevularının rakamlarını görür.\n\n"
            "`total_income` yalnızca gelen müşterilerin tek rakamlı fiyatlarını toplar; "
            "\"2000-3000\" gibi aralıklar toplanamaz ve `income_skipped_count` içinde sayılır."
        ),
        responses={200: "İstatistikler başarıyla getirildi.", 403: "Yetkisiz"},
        tags=["MEETINGS"],
    )
    def get(self, request):
        user = request.user

        role, staff = scope_for(user)
        if role is None:
            return Response({"error": NO_ACCESS_MESSAGE}, status=status.HTTP_403_FORBIDDEN)

        meetings = Meetings.objects.filter(company=user.company)
        if role == "staff":
            meetings = meetings.filter(staff=staff)

        # Temel sayısal istatistikler
        total_meetings = meetings.count()
        waiting_meetings = meetings.filter(status=MeetingStatus.WAITING).count()
        arrived_meetings = meetings.filter(status=MeetingStatus.ARRIVED).count()
        cancelled_meetings = meetings.filter(status=MeetingStatus.CANCELED).count()

        # En çok tercih edilen hizmet
        top_service = (
            meetings.values("service_title")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first()
        )

        # Toplam gelir (sadece gelen müşterilerin randevularından)
        total_income, income_skipped = _income(meetings.filter(status=MeetingStatus.ARRIVED))

        data = {
            "scope": "staff" if role == "staff" else "company",
            "total_meetings": total_meetings,
            "waiting_meetings": waiting_meetings,
            "arrived_meetings": arrived_meetings,
            "cancelled_meetings": cancelled_meetings,
            "total_income": f"{total_income:.2f}".rstrip("0").rstrip(".") + " ₺",
            "income_skipped_count": income_skipped,
            "top_service": top_service["service_title"] if top_service else None,
            "top_service_count": top_service["count"] if top_service else 0,
        }

        # Firma sahibi için çalışan bazlı dağılım (çalışanı olmayan eski randevular "Atanmamış")
        if role == "owner":
            by_staff = (
                meetings.values("staff_id", "staff__user__name", "staff__user__surname")
                .annotate(
                    total=Count("id"),
                    arrived=Count("id", filter=Q(status=MeetingStatus.ARRIVED)),
                    waiting=Count("id", filter=Q(status=MeetingStatus.WAITING)),
                )
                .order_by("-total")
            )
            data["by_staff"] = [
                {
                    "staff_id": row["staff_id"],
                    "name": (
                        f"{row['staff__user__name']} {row['staff__user__surname']}".strip()
                        if row["staff_id"]
                        else "Atanmamış"
                    ),
                    "total": row["total"],
                    "arrived": row["arrived"],
                    "waiting": row["waiting"],
                }
                for row in by_staff
            ]

        return Response(data, status=status.HTTP_200_OK)
