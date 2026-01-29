from django.db import models


class DiagnosisCategory(models.Model):
    """
    ICD Category codes across all versions
    Categories are version-specific (ICD-9 categories ≠ ICD-10 categories)
    """
    code = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=255)
    icd_version = models.CharField(max_length=10, db_index=True)  # "ICD-9", "ICD-10", "ICD-11"
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Diagnosis Categories"
        unique_together = ("code", "icd_version")
        indexes = [
            models.Index(fields=['icd_version', 'code']),
        ]
        ordering = ['icd_version', 'code']
    
    def __str__(self):
        return f"{self.icd_version}: {self.code} - {self.title}"


class DiagnosisCode(models.Model):
    """
    Individual ICD diagnosis codes across all versions
    Each code belongs to exactly one version
    """
    category = models.ForeignKey(
        DiagnosisCategory,
        on_delete=models.PROTECT,
        related_name="diagnosis_codes",
        null=True,  # Some versions might not use categories
        blank=True
    )
    
    # Core fields
    diagnosis_code = models.CharField(max_length=20, db_index=True)  # The sub-code part
    full_code = models.CharField(max_length=20, db_index=True)  # Complete code
    abbreviated_description = models.CharField(max_length=255)
    full_description = models.TextField()
    
    # Version - CRITICAL for multi-version support
    icd_version = models.CharField(max_length=10, db_index=True)  # "ICD-9", "ICD-10", "ICD-11"
    
    # Status tracking
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateField(blank=True, null=True)
    valid_to = models.DateField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Diagnosis Codes"
        unique_together = ("full_code", "icd_version")
        indexes = [
            models.Index(fields=['icd_version', 'full_code']),
            models.Index(fields=['icd_version', 'is_active']),
            models.Index(fields=['category', 'icd_version']),
        ]
        ordering = ['icd_version', 'full_code']
    
    def __str__(self):
        return f"{self.icd_version}: {self.full_code} - {self.abbreviated_description}"