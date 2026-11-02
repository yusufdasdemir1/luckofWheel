from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import Review, ReviewStatus
from core.pagination import paginated_response
from core.permissions import owner_only_response
from core.serializers.review_serializers import PanelReviewSerializer, ReviewUpdateSerializer
from core.services.review_service import recalculate_rating


def _company_reviews(user):
    return Review.objects.filter(company=user.company).select_related("meeting__user", "meeting__staff__user")


class ReviewListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="⭐ Yorum listesi (panel, sadece firma sahibi)",
        manual_parameters=[
            openapi.Parameter("status", openapi.IN_QUERY, description="pending | approved | hidden", type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("page_size", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        tags=["REVIEWS"],
    )
    def get(self, request):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        reviews = _company_reviews(request.user)

        # sekme sayaçları: filtreden bağımsız, firmanın tüm yorumları
        counts = {value: 0 for value in ReviewStatus.values}
        for value in reviews.values_list("status", flat=True):
            counts[value] += 1

        status_param = request.query_params.get("status", "").strip()
        if status_param in ReviewStatus.values:
            reviews = reviews.filter(status=status_param)

        return paginated_response(
            request,
            reviews.order_by("-created_at", "-id"),
            PanelReviewSerializer,
            extra={"counts": counts},
        )


class ReviewDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="⭐ Yorumu onayla / gizle / cevapla (panel, sadece firma sahibi)",
        request_body=ReviewUpdateSerializer,
        tags=["REVIEWS"],
        responses={200: "Güncellendi", 403: "Yetkisiz", 404: "Yorum bulunamadı"},
    )
    def patch(self, request, review_id):
        denied = owner_only_response(request.user)
        if denied:
            return denied

        review = _company_reviews(request.user).filter(id=review_id).first()
        if not review:
            return Response({"error": "Yorum bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "status" in data:
            review.status = data["status"]
        if "reply" in data:
            review.reply = data["reply"].strip()
            review.replied_at = timezone.now() if review.reply else None
        review.save()

        # onay/gizleme puan önbelleğini etkiler
        recalculate_rating(review.company)

        return Response(PanelReviewSerializer(review).data, status=status.HTTP_200_OK)
