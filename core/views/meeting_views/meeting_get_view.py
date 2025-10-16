from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Companies, Users, Meetings, Services
from core.serializers import MeetingListSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class MeetingDetailView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["MEETINGS"])
    def get(self,request,meeting_id):
        user=request.user

        if not user.is_admin:
            return Response({"error":"bu işlem sadece admin kullanıcılar içindir."},
                            status=status.HTTP_403_FORBIDDEN
                            )

        meeting=Meetings.objects.filter(id=meeting_id,company=user.company).select_related("company","user").first()

        if not meeting:
            return Response(
                {"message":f"meeting id {meeting_id} not exist"},
            )

        serializer=MeetingListSerializer(meeting)

        return Response(serializer.data,status=status.HTTP_200_OK)