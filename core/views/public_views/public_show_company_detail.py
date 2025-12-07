from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from core.serializers.public_serializers.public_serializers import PublicCompanySerializer
from core.models import Companies

class PublicCompanyDetailView(APIView):

    @swagger_auto_schema(tags=["PUBLIC"])
    def get(self, request, slug):
        company = get_object_or_404(Companies, slug=slug)

        serializer = PublicCompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
