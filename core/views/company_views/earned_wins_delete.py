from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import EarnedWins
from core.serializers.company_serializers.company_serializers import EarnedWinDeleteSerializer

class EarnedWinsDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["ADMIN ACTIONS"])
    def delete(self, request, earned_wins_id):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            earned_wins = EarnedWins.objects.get(id=earned_wins_id,company=user.company)

        except EarnedWins.DoesNotExist:
            return Response(
                {"error": f"Bu şirketin {earned_wins_id} ID'ye sahip bir earned wins i bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )


        serializer=EarnedWinDeleteSerializer(earned_wins)
        deleted_data = serializer.data

        earned_wins.delete()

        return Response(
            {
                "message": "Kazanılan hediye başarıyla silindi.",
                "deleted_earned_win": deleted_data
            },
            status=status.HTTP_200_OK
        )