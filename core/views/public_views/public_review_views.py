from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Companies, Meetings, Review, ReviewStatus
from core.pagination import paginated_response
from core.serializers.review_serializers import PublicReviewSerializer, ReviewCreateSerializer
from core.services.review_service import (
    STATE_CANCELED,
    STATE_DONE,
    STATE_OPEN,
    STATE_TOO_EARLY,
    review_state,
)

STATE_MESSAGES = {
    STATE_TOO_EARLY: "Randevunuz tamamlandıktan sonra değerlendirme yapabilirsiniz.",
    STATE_CANCELED: "Bu randevu iptal edildiği için değerlendirilemez.",
    STATE_DONE: "Bu randevu için değerlendirmeniz alındı, teşekkür ederiz.",
}


def _get_meeting(token):
    return get_object_or_404(
        Meetings.objects.select_related("company", "user", "staff__user"),
        review_token=token,
    )


class PublicReviewView(APIView):
    """Maildeki link: randevu özeti + yorum bırakma."""

    @swagger_auto_schema(
        operation_summary="⭐ Değerlendirme sayfası verisi (token ile)",
        operation_description=(
            "Maildeki linkin token'ına göre randevu özetini ve durumunu döner. "
            "`state`: `open` (yorum yazılabilir), `too_early` (randevu bitmedi), "
            "`canceled` (iptal), `done` (zaten yorum yapılmış)."
        ),
        tags=["PUBLIC"],
        responses={200: "Randevu özeti", 404: "Geçersiz bağlantı"},
    )
    def get(self, request, token):
        meeting = _get_meeting(token)
        state = review_state(meeting)
        staff = meeting.staff
        return Response(
            {
                "state": state,
                "message": STATE_MESSAGES.get(state, ""),
                "company": {
                    "title": meeting.company.title,
                    "slug": meeting.company.slug,
                    "logo": meeting.company.logo,
                },
                "meeting": {
                    "service_title": meeting.service_title,
                    "date": meeting.date,
                    "time": meeting.time.strftime("%H:%M"),
                    "staff": f"{staff.user.name} {staff.user.surname}".strip() if staff else None,
                },
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_summary="⭐ Randevuyu değerlendir (token ile)",
        operation_description=(
            "Randevu bittikten sonra 1-5 puan ve isteğe bağlı yorum bırakılır. "
            "Randevu başına tek yorum; yorum salon onayına düşer."
        ),
        request_body=ReviewCreateSerializer,
        tags=["PUBLIC"],
        responses={
            201: "Değerlendirme alındı",
            400: "Randevu henüz bitmedi, iptal edilmiş veya geçersiz veri",
            404: "Geçersiz bağlantı",
            409: "Bu randevu zaten değerlendirilmiş",
        },
    )
    def post(self, request, token):
        meeting = _get_meeting(token)

        state = review_state(meeting)
        if state != STATE_OPEN:
            code = status.HTTP_409_CONFLICT if state == STATE_DONE else status.HTTP_400_BAD_REQUEST
            return Response({"error": STATE_MESSAGES[state], "state": state}, status=code)

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                Review.objects.create(
                    meeting=meeting,
                    company=meeting.company,
                    rating=serializer.validated_data["rating"],
                    comment=serializer.validated_data["comment"],
                )
        except IntegrityError:
            # aynı anda iki istek gelirse OneToOne ikincisini reddeder
            return Response(
                {"error": STATE_MESSAGES[STATE_DONE], "state": STATE_DONE},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"message": "Değerlendirmeniz alındı, teşekkür ederiz.", "state": STATE_DONE},
            status=status.HTTP_201_CREATED,
        )


class PublicReviewListView(APIView):
    """Salon sayfasında gösterilen onaylı yorumlar ve puan dağılımı."""

    @swagger_auto_schema(
        operation_summary="⭐ Salonun onaylı yorumları (public)",
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("page_size", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        tags=["PUBLIC"],
        responses={200: "Yorumlar, ortalama ve dağılım", 404: "Firma bulunamadı"},
    )
    def get(self, request, slug):
        company = get_object_or_404(Companies, slug=slug)

        approved = (
            Review.objects.filter(company=company, status=ReviewStatus.APPROVED)
            .select_related("meeting__user")
            .order_by("-created_at", "-id")
        )

        counts = dict(approved.values_list("rating").annotate(n=Count("id")))
        distribution = {str(star): counts.get(star, 0) for star in range(5, 0, -1)}

        return paginated_response(
            request,
            approved,
            PublicReviewSerializer,
            extra={
                "rating_avg": company.rating_avg,
                "rating_count": company.rating_count,
                "distribution": distribution,
            },
        )
