from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import EarnedWins
from core.permissions import NO_ACCESS_MESSAGE, scope_for

TOP_GIFTS_LIMIT = 5
RECENT_DAYS = 30


class SpinStatisticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🏆 Kazanılan hediye istatistikleri (firma sahibi: tüm firma, çalışan: kendi müşterileri)",
        operation_description=(
            "Kazanılan hediyelerin özetini döner: toplam, kullanılan/kullanılmayan, kullanım oranı, "
            "tekil müşteri sayısı, son 30 gün ve en çok kazanılan hediyeler (`top_gifts`).\n\n"
            "Kapsam `/spin_history` listesiyle aynıdır: çalışan sadece kendisinden randevu alan "
            "müşterilerin hediyelerini görür."
        ),
        responses={200: "İstatistikler başarıyla getirildi.", 403: "Yetkisiz"},
        tags=["ADMIN ACTIONS"],
    )
    def get(self, request):
        user = request.user

        role, staff = scope_for(user)
        if role is None:
            return Response({"error": NO_ACCESS_MESSAGE}, status=status.HTTP_403_FORBIDDEN)

        wins = EarnedWins.objects.filter(company=user.company)
        if role == "staff":
            wins = wins.filter(user__meetings__staff=staff).distinct()

        total = wins.count()
        used = wins.filter(is_used=True).count()
        recent = wins.filter(created_at__gte=timezone.now() - timedelta(days=RECENT_DAYS)).count()
        customers = wins.values("user_id").distinct().count()

        # aynı hediyenin farklı yazımları tek satırda toplansın (büyük/küçük harf ve boşluk)
        grouped = {}
        rows = (
            wins.values("gift_title")
            .annotate(count=Count("id", distinct=True), used=Count("id", filter=Q(is_used=True), distinct=True))
            .order_by("-count", "gift_title")
        )
        for row in rows:
            title = (row["gift_title"] or "").strip()
            key = title.casefold()
            entry = grouped.setdefault(key, {"title": title, "count": 0, "used": 0})
            entry["count"] += row["count"]
            entry["used"] += row["used"]

        top_gifts = sorted(grouped.values(), key=lambda g: (-g["count"], g["title"]))[:TOP_GIFTS_LIMIT]
        for gift in top_gifts:
            gift["percent"] = round(gift["count"] * 100 / total, 1) if total else 0

        return Response(
            {
                "scope": "company" if role == "owner" else "staff",
                "total_wins": total,
                "used_wins": used,
                "unused_wins": total - used,
                "usage_rate": round(used * 100 / total, 1) if total else 0,
                "unique_customers": customers,
                "recent_wins": recent,
                "recent_days": RECENT_DAYS,
                "top_gift": top_gifts[0] if top_gifts else None,
                "top_gifts": top_gifts,
            },
            status=status.HTTP_200_OK,
        )
