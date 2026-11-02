from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from core.models import EarnedWins
from core.pagination import paginated_response, wants_page
from core.permissions import scope_for, NO_ACCESS_MESSAGE
from core.serializers.company_serializers.company_serializers import EarnedWinsSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CompanySpinHistoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🎡 Spin geçmişi (filtreli, sadece admin)",
        tags=["ADMIN ACTIONS"],
        operation_description=(
            "Admin kendi şirketine ait spin geçmişini görüntüler.\n\n"
            "Opsiyonel query parametreleri:\n"
            "- `user_id`: Belirli bir kullanıcıya ait kayıtları getirir.\n"
            "- `is_used`: True/False — Kullanılmış veya kullanılmamış ödüller.\n\n"
            "Filtreler birlikte de kullanılabilir."
        ),
        responses={200: "Başarılı listeleme", 403: "Yetkisiz erişim"},
        manual_parameters=[
            openapi.Parameter(
                "user_id",
                openapi.IN_QUERY,
                description="Kullanıcı ID’si (opsiyonel)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter("q", openapi.IN_QUERY, description="Müşteri adı/soyadı veya hediye adı; kelime BAŞLANGICINA göre arar (içinde geçmesi yetmez)", type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, description="Sayfa numarası (page/page_size/q verilirse sayfalı yanıt)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("page_size", openapi.IN_QUERY, description="Sayfa başına kayıt (en fazla 50)", type=openapi.TYPE_INTEGER),
            openapi.Parameter(
                "is_used",
                openapi.IN_QUERY,
                description="Kullanım durumu (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False,
            ),
        ],
    )
    def get(self, request):
        user=request.user

        role, staff = scope_for(user)
        if role is None:
            return Response({"error": NO_ACCESS_MESSAGE},status=status.HTTP_403_FORBIDDEN)

        #Kendi firmasına ait veriler
        queryset=EarnedWins.objects.filter(company=user.company)
        if role == "staff":
            # çalışan: kendisinden randevu alan müşterilerin hediyeleri
            queryset=queryset.filter(user__meetings__staff=staff).distinct()
        queryset=queryset.select_related("user","meeting").order_by('-created_at')

        user_id=request.query_params.get('user_id')
        is_used=request.query_params.get('is_used')

        if user_id:
            queryset=queryset.filter(user_id=user_id)

        if is_used is not None:
            if is_used.lower() == "true":
                queryset = queryset.filter(is_used=True)
            elif is_used.lower() == "false":
                queryset = queryset.filter(is_used=False)

        query=request.query_params.get('q','').strip()
        # kelime başlangıcına göre ara: "ali" -> Ali, Alizade; "salih" gelmez (içinde geçmesi yetmez)
        for word in query.split():
            queryset=queryset.filter(
                Q(user__name__istartswith=word)
                |Q(user__surname__istartswith=word)
                |Q(gift_title__istartswith=word)
                |Q(gift_title__icontains=f" {word}")
            )

        if wants_page(request, ("q",)):
            return paginated_response(request, queryset, EarnedWinsSerializer)

        if not queryset.exists():
            return Response(
                {"message": "Belirtilen filtrelere göre eşleşen kayıt bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer=EarnedWinsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)





