from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Companies
from core.serializers.public_serializers.public_serializers import ShowCompaniesSerializer


class ShowCompaniesView(APIView):
    @swagger_auto_schema(tags=["PUBLIC"])
    def get(self,request):
        try:
            companies = Companies.objects.all()
            serializer = ShowCompaniesSerializer(companies, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)