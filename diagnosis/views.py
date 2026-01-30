from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import DiagnosisCode, DiagnosisCategory
from .serializers import (
    DiagnosisCodeSerializer,
    DiagnosisCodeListSerializer,
    DiagnosisCategorySerializer
)



@extend_schema(
    request=DiagnosisCategorySerializer,
    responses={200: OpenApiResponse(response=DiagnosisCodeListSerializer(many=True))}
)
@api_view(['GET', 'POST'])
def diagnosis_category_list_create(request):
    """
    List all diagnosis categories or create a new one
    """
    if request.method == 'GET':
        queryset = DiagnosisCategory.objects.all()
        icd_version = request.query_params.get('icd_version')
        if icd_version:
            queryset = queryset.filter(icd_version=icd_version)
        queryset = queryset.order_by('icd_version', 'code')
        paginator = DiagnosisCodePagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = DiagnosisCategorySerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method == 'POST':
        serializer = DiagnosisCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=DiagnosisCategorySerializer,
    responses=OpenApiResponse(
        response=DiagnosisCategorySerializer(many=True))
)
@api_view(['GET', 'PUT', 'DELETE'])
def diagnosis_category_detail(request, pk):
    """
    Retrieve, update, or delete a diagnosis category
    """
    category = get_object_or_404(DiagnosisCategory, pk=pk)
    if request.method == 'GET':
        serializer = DiagnosisCategorySerializer(category)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = DiagnosisCategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        try:
            category.delete()
            return Response({"message": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"error": "Cannot delete category with associated diagnosis codes"}, status=status.HTTP_400_BAD_REQUEST)


class DiagnosisCodePagination(PageNumberPagination):
    """
    Custom pagination for DiagnosisCode views
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(
    request=DiagnosisCodeSerializer,
    responses={200: OpenApiResponse(response=DiagnosisCodeListSerializer(many=True))}
)
@api_view(['GET', 'POST'])
def diagnosis_code_list_create(request):
    """
    List all diagnosis codes or create a new one
    """
    if request.method == 'GET':
        queryset = DiagnosisCode.objects.select_related('category').all()
        icd_version = request.query_params.get('icd_version')
        if icd_version:
            queryset = queryset.filter(icd_version=icd_version)
        include_inactive = request.query_params.get('include_inactive', 'false')
        if include_inactive.lower() != 'true':
            queryset = queryset.filter(is_active=True)
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_code__icontains=search) |
                Q(abbreviated_description__icontains=search) |
                Q(full_description__icontains=search)
            )
        queryset = queryset.order_by('icd_version', 'full_code')
        paginator = DiagnosisCodePagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = DiagnosisCodeListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = DiagnosisCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=DiagnosisCodeSerializer,
    responses=OpenApiResponse(
        response=DiagnosisCategorySerializer(many=True))
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def diagnosis_code_detail(request, pk):
    """
    Retrieve, update, or delete a diagnosis code
    """
    diagnosis_code = get_object_or_404(DiagnosisCode, pk=pk)
    if request.method == 'GET':
        serializer = DiagnosisCodeSerializer(diagnosis_code)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = DiagnosisCodeSerializer(diagnosis_code, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PATCH':
        serializer = DiagnosisCodeSerializer(diagnosis_code, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        diagnosis_code.delete()
        return Response({"message": "Diagnosis code deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


