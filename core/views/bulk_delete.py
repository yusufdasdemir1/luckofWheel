from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import EarnedWins, Meetings

MAX_BULK_IDS = 100

BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["ids"],
    properties={
        "ids": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_INTEGER),
            description=f"Silinecek kayıtların ID listesi (en fazla {MAX_BULK_IDS})",
        )
    },
)


def _clean_ids(raw):
    """[1, '2', 2] -> [1, 2]; geçersizse None."""
    if not isinstance(raw, list) or not raw:
        return None
    ids = []
    for value in raw:
        if isinstance(value, bool):
            return None
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            return None
    ids = list(dict.fromkeys(ids))  # tekrarlananları at, sırayı koru
    return ids if len(ids) <= MAX_BULK_IDS else None


class _BulkDeleteView(APIView):
    """Firma sahibi, kendi firmasına ait kayıtları tek istekte siler (hepsi ya da hiçbiri)."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    label = ""

    def post(self, request):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ids = _clean_ids(request.data.get("ids"))
        if ids is None:
            return Response(
                {"error": f"`ids`, en fazla {MAX_BULK_IDS} adet sayıdan oluşan boş olmayan bir liste olmalı."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            queryset = self.model.objects.filter(company=user.company, id__in=ids)
            found = set(queryset.values_list("id", flat=True))
            queryset.delete()

        return Response(
            {
                "message": f"{len(found)} {self.label} silindi.",
                "deleted": len(found),
                "not_found": [i for i in ids if i not in found],
            },
            status=status.HTTP_200_OK,
        )


class MeetingBulkDeleteView(_BulkDeleteView):
    model = Meetings
    label = "randevu"

    @swagger_auto_schema(
        operation_summary="🗑️ Randevuları toplu sil (sadece admin)",
        request_body=BODY,
        responses={200: "Silinen sayısı ve bulunamayan ID'ler", 400: "Geçersiz liste", 403: "Yetkisiz"},
        tags=["MEETINGS"],
    )
    def post(self, request):
        return super().post(request)


class EarnedWinsBulkDeleteView(_BulkDeleteView):
    model = EarnedWins
    label = "kazanılan hediye"

    @swagger_auto_schema(
        operation_summary="🗑️ Kazanılan hediyeleri toplu sil (sadece admin)",
        request_body=BODY,
        responses={200: "Silinen sayısı ve bulunamayan ID'ler", 400: "Geçersiz liste", 403: "Yetkisiz"},
        tags=["ADMIN ACTIONS"],
    )
    def post(self, request):
        return super().post(request)
