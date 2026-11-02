from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Companies, Meetings, MeetingStatus, Users
from core.serializers.public_serializers.public_serializers import PublicSpinSerializer
from core.services.spin import cooldown_message, spin_status, spin_wheel


def _cooldown_response(status_info):
    return Response(
        {
            "error": cooldown_message(status_info["remaining_seconds"]),
            "remaining_seconds": status_info["remaining_seconds"],
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


class PublicSpinView(APIView):
    @swagger_auto_schema(
        operation_summary="🎡 Public: Çark çevir (müşteri butona basınca)",
        operation_description=(
            "Müşteri çark butonuna basınca çağrılır; iki modda da çalışır.\n\n"
            "- `wheel_mode=before`: `meeting_id` gönderilmez. Hediye bağsız kaydedilir, "
            "müşteri randevu oluşturunca o randevuya bağlanır.\n"
            "- `wheel_mode=after`: `meeting_id` zorunludur (`phone` eşleşmeli). Bir randevu için yalnızca "
            "bir kez çevrilir, iptal edilmiş randevuda çevrilemez. Hediye doğrudan o randevuya bağlanır.\n\n"
            "Spin bekleme süresi (`spin_cooldown_hours`) iki modda da geçerlidir; hak yoksa "
            "400 ile `remaining_seconds` döner."
        ),
        request_body=PublicSpinSerializer,
        responses={
            201: "Çark çevrildi",
            400: "Çark çevrilemez veya bekleme süresi dolmadı",
            404: "Firma, müşteri veya randevu bulunamadı",
        },
        tags=["PUBLIC"],
    )
    def post(self, request, slug):
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicSpinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        meeting_id = serializer.validated_data.get("meeting_id")

        if company.wheel_mode == Companies.WHEEL_NONE:
            return Response(
                {"error": "Bu firmada çark kullanılmıyor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if company.wheel_mode == Companies.WHEEL_AFTER and not meeting_id:
            return Response(
                {"error": "Çark için randevu bilgisi gerekli."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            meeting = None
            if company.wheel_mode == Companies.WHEEL_AFTER:
                meeting = (
                    Meetings.objects.select_for_update()
                    .select_related("user")
                    .filter(id=meeting_id, company=company, user__phone=phone)
                    .first()
                )
                if not meeting:
                    return Response({"error": "Randevu bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

                if meeting.status == MeetingStatus.CANCELED:
                    return Response(
                        {"error": "İptal edilmiş randevu için çark çevrilemez."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if meeting.wins.exists():
                    return Response(
                        {"error": "Bu randevu için çark zaten çevrildi."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = meeting.user
            else:
                user = Users.objects.select_for_update().filter(phone=phone, company=company).first()
                if not user:
                    return Response(
                        {"error": "Bu telefon numarasına ait kullanıcı bulunamadı."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            info = spin_status(user, company)
            if not info["can_spin"]:
                return _cooldown_response(info)

            win = spin_wheel(user, company, meeting=meeting)
            if not win:
                return Response({"error": "Bu firmada aktif hediye yok."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"{win.gift_description}",
                "gift_views": win.gift_title,
                "company": company.title,
                "can_spin": False,
                "remaining_seconds": int(company.spin_cooldown_hours * 3600),
                "next_spin_available_in_hours": company.spin_cooldown_hours,
            },
            status=status.HTTP_201_CREATED,
        )
