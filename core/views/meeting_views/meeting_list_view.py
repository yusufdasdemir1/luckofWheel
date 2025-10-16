from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings
from core.serializers.meeting_serializers.meeting_serializers import MeetingListSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class MeetingListView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["MEETINGS"])
    def get(self,request):
        user=request.user

        if not user.is_admin:
            return Response({"error":"bu işlem sadece admin kullanıcılar içindir."},
                            status=status.HTTP_403_FORBIDDEN
                            )

        meetings_list=Meetings.objects.filter(company=user.company).select_related("company","user").order_by('-date', '-time')

        if not meetings_list:
            return Response({"message":"firmanıza ait randevu bulunmamakta."},status=status.HTTP_200_OK)

        serializer=MeetingListSerializer(meetings_list,many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)
