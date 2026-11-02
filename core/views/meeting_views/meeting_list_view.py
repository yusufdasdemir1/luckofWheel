from datetime import date, timedelta

from django.db.models import Q
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings, MeetingStatus, Staff
from core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, paginated_response, wants_page
from core.permissions import scope_for, NO_ACCESS_MESSAGE
from core.serializers.meeting_serializers.meeting_serializers import MeetingListSerializer
from core.services.working_hours import salon_now
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

FILTER_KEYS = ("q", "status", "staff_id", "when", "date", "date_from", "date_to")
WHEN_CHOICES = ("today", "tomorrow", "week", "upcoming", "past")


def _apply_search(queryset, query):
    """
    Her kelime kelime BAŞLANGICINA göre aranır ("ali" -> Ali, Alizade; "salih" gelmez):
    müşteri adı/soyadı, işlem adı (kelime başı), kuaför adı/soyadı.
    Telefon numarası istisna: "+90" ile başladığı için içinde geçen rakamlar aranır.
    """
    for word in query.split():
        queryset = queryset.filter(
            Q(user__name__istartswith=word)
            | Q(user__surname__istartswith=word)
            | Q(user__phone__icontains=word)
            | Q(service_title__istartswith=word)
            | Q(service_title__icontains=f" {word}")
            | Q(staff__user__name__istartswith=word)
            | Q(staff__user__surname__istartswith=word)
        )
    return queryset


def _apply_when(queryset, when):
    today = salon_now().date()
    if when == "today":
        return queryset.filter(date=today)
    if when == "tomorrow":
        return queryset.filter(date=today + timedelta(days=1))
    if when == "week":
        return queryset.filter(date__range=(today, today + timedelta(days=6)))
    if when == "upcoming":
        return queryset.filter(date__gte=today)
    if when == "past":
        return queryset.filter(date__lt=today)
    return queryset


class MeetingListView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="📅 Randevu listesi (sayfalı, aramalı, filtreli)",
        operation_description=(
            "Firma sahibi tüm randevuları, çalışan sadece kendi randevularını görür.\n\n"
            "Hiç parametre verilmezse eski davranış korunur (düz liste). "
            "`page`, `page_size`, `q`, `status`, `staff_id`, `when`, `date`, `date_from` veya `date_to` verilirse sayfalı yanıt döner: "
            "`count`, `page`, `page_size`, `total_pages`, `results` ve (firma sahibi için) `filters.staff`."
        ),
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY, description="Sayfa numarası (varsayılan 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter(
                "page_size", openapi.IN_QUERY,
                description=f"Sayfa başına kayıt (varsayılan {DEFAULT_PAGE_SIZE}, en fazla {MAX_PAGE_SIZE})",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter("q", openapi.IN_QUERY, description="Müşteri adı/soyadı, işlem veya kuaför adı (kelime BAŞLANGICINA göre); telefonda içinde geçen rakamlar", type=openapi.TYPE_STRING),
            openapi.Parameter("status", openapi.IN_QUERY, description="waiting | arrived | canceled", type=openapi.TYPE_STRING),
            openapi.Parameter("staff_id", openapi.IN_QUERY, description="Kuaför (sadece firma sahibi için)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("when", openapi.IN_QUERY, description="today | tomorrow | week | upcoming | past", type=openapi.TYPE_STRING),
            openapi.Parameter("date", openapi.IN_QUERY, description="Belirli gün (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter("date_from", openapi.IN_QUERY, description="Tarih aralığı başlangıcı, dahil (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter("date_to", openapi.IN_QUERY, description="Tarih aralığı bitişi, dahil (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        tags=["MEETINGS"],
    )
    def get(self,request):
        user=request.user

        role, staff = scope_for(user)
        if role is None:
            return Response({"error": NO_ACCESS_MESSAGE},
                            status=status.HTTP_403_FORBIDDEN
                            )

        meetings_list=Meetings.objects.filter(company=user.company)
        if role == "staff":
            # çalışan sadece kendi randevularını görür
            meetings_list=meetings_list.filter(staff=staff)
        meetings_list=meetings_list.select_related("company","user","staff__user")

        # eski istemciler: parametre yoksa düz liste (geriye dönük uyumluluk)
        if not wants_page(request, FILTER_KEYS):
            meetings_list=meetings_list.order_by('-created_at')
            if not meetings_list:
                return Response({"message":"firmanıza ait randevu bulunmamakta."},status=status.HTTP_404_NOT_FOUND)
            return Response(MeetingListSerializer(meetings_list,many=True).data,status=status.HTTP_200_OK)

        params = request.query_params

        query = params.get("q", "").strip()
        if query:
            meetings_list = _apply_search(meetings_list, query)

        status_param = params.get("status", "").strip()
        if status_param in MeetingStatus.values:
            meetings_list = meetings_list.filter(status=status_param)

        staff_id = params.get("staff_id", "").strip()
        if role == "owner" and staff_id.isdigit():
            meetings_list = meetings_list.filter(staff_id=int(staff_id))

        when = params.get("when", "").strip()
        if when in WHEN_CHOICES:
            meetings_list = _apply_when(meetings_list, when)

        try:
            date_param = params.get("date", "").strip()
            if date_param:
                meetings_list = meetings_list.filter(date=date.fromisoformat(date_param))

            # tarih aralığı: iki uç da dahil, biri boş bırakılabilir
            date_from = params.get("date_from", "").strip()
            date_to = params.get("date_to", "").strip()
            if date_from:
                meetings_list = meetings_list.filter(date__gte=date.fromisoformat(date_from))
            if date_to:
                meetings_list = meetings_list.filter(date__lte=date.fromisoformat(date_to))
        except ValueError:
            return Response({"error": "Tarih YYYY-AA-GG biçiminde olmalı."}, status=status.HTTP_400_BAD_REQUEST)

        # bugünden ileriye doğru yaklaşan randevular önce; diğerlerinde en yeni randevu başta
        if when in ("today", "tomorrow", "week", "upcoming"):
            meetings_list = meetings_list.order_by("date", "time", "id")
        else:
            meetings_list = meetings_list.order_by("-date", "-time", "-id")

        extra = None
        if role == "owner":
            extra = {
                "filters": {
                    "staff": [
                        {"id": s.id, "name": f"{s.user.name} {s.user.surname}".strip()}
                        for s in Staff.objects.filter(company=user.company).select_related("user").order_by("user__name")
                    ]
                }
            }

        return paginated_response(request, meetings_list, MeetingListSerializer, extra=extra)
