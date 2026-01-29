from rest_framework import serializers
from .models import DiagnosisCategory, DiagnosisCode


class DiagnosisCategorySerializer(serializers.ModelSerializer):
    """Serializer for DiagnosisCategory model"""
    class Meta:
        model = DiagnosisCategory
        fields = [
            'id',
            'code',
            'title',
            'icd_version',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DiagnosisCodeSerializer(serializers.ModelSerializer):
    """Full serializer for DiagnosisCode - used for detail views and create/update"""
    category_details = DiagnosisCategorySerializer(source='category', read_only=True)
    
    class Meta:
        model = DiagnosisCode
        fields = [
            'id',
            'category',              # ID for POST/PUT (write)
            'category_details',      # Full object for GET (read)
            'diagnosis_code',
            'full_code',
            'abbreviated_description',
            'full_description',
            'icd_version',
            'is_active',
            'valid_from',
            'valid_to',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """
        Ensure category.icd_version matches code.icd_version
        """
        category = data.get("category")
        icd_version = data.get("icd_version")

        # Only validate if both are provided
        if category and icd_version:
            if category.icd_version != icd_version:
                raise serializers.ValidationError({
                    "icd_version": "Category icd_version must match diagnosis code icd_version"
                })

        return data


class DiagnosisCodeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    category_code = serializers.CharField(source='category.code', read_only=True)
    
    class Meta:
        model = DiagnosisCode
        fields = [
            'id',
            'full_code',
            'abbreviated_description',
            'icd_version',
            'category_code',
            'is_active'
        ]
