from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.serializers.company_serializers.auth_serializers import LogoutSerializer

class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🚪 Admin logout (JWT token geçersiz kılınır)",
        operation_description=(
            "Admin kullanıcı logout olur. Refresh token geçersiz kılınır. "
            "Access token, süresi dolana kadar geçerli kalır (ama yenilenemez)."
        ),
        request_body=LogoutSerializer,
        tags=["ADMIN AUTHENTICATION"],
        responses={200: "Logout başarılı", 400: "Token eksik veya hatalı"},
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logout başarılı. Token geçersiz kılındı."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"error": "Geçersiz veya eksik token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
