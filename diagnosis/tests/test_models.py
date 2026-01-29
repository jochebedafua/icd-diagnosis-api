from django.test import TestCase
from django.db import IntegrityError
from diagnosis.models import DiagnosisCategory, DiagnosisCode

"""
Model Tests

Why test models?
- Ensure database constraints work (unique_together, PROTECT)
- Validate relationships
- Test edge cases
- Documentation of expected behavior
"""


class DiagnosisCategoryModelTest(TestCase):
    """Test DiagnosisCategory model"""
    
    def setUp(self):
        """
        Run before each test method
        Why setUp? Creates clean test data for each test
        """
        self.category = DiagnosisCategory.objects.create(
            code="C21",
            title="Malignant neoplasm of anus and anal canal",
            icd_version="ICD-10"
        )
    
    def test_category_creation(self):
        """Test basic category creation"""
        self.assertEqual(self.category.code, "C21")
        self.assertEqual(self.category.icd_version, "ICD-10")
        self.assertIsNotNone(self.category.created_at)
        self.assertIsNotNone(self.category.id)
    
    def test_category_string_representation(self):
        """Test __str__ method"""
        expected = "ICD-10: C21 - Malignant neoplasm of anus and anal canal"
        self.assertEqual(str(self.category), expected)
    
    def test_category_unique_together(self):
        """
        Test that code+version must be unique
        Why? Prevents duplicate categories in same version
        """
        with self.assertRaises(IntegrityError):
            DiagnosisCategory.objects.create(
                code="C21",
                title="Duplicate",
                icd_version="ICD-10"  # Same code+version = error
            )
    
    def test_category_same_code_different_version(self):
        """
        Test same code can exist in different versions
        Why? ICD-9 C21 ≠ ICD-10 C21
        """
        category_v9 = DiagnosisCategory.objects.create(
            code="C21",
            title="ICD-9 version",
            icd_version="ICD-9"  # Different version = OK
        )
        self.assertIsNotNone(category_v9.id)
        self.assertEqual(DiagnosisCategory.objects.filter(code="C21").count(), 2)


class DiagnosisCodeModelTest(TestCase):
    """Test DiagnosisCode model"""
    
    def setUp(self):
        self.category = DiagnosisCategory.objects.create(
            code="A0",
            title="Test Category",
            icd_version="ICD-10"
        )
        self.code = DiagnosisCode.objects.create(
            category=self.category,
            diagnosis_code="1234",
            full_code="A01234",
            abbreviated_description="Test abbrev",
            full_description="Test full description",
            icd_version="ICD-10"
        )
    
    def test_code_creation(self):
        """Test basic code creation"""
        self.assertEqual(self.code.full_code, "A01234")
        self.assertEqual(self.code.icd_version, "ICD-10")
        self.assertTrue(self.code.is_active)  # Default value
        self.assertIsNotNone(self.code.created_at)
    
    def test_code_unique_together(self):
        """Test full_code+version must be unique"""
        with self.assertRaises(IntegrityError):
            DiagnosisCode.objects.create(
                category=self.category,
                diagnosis_code="1234",
                full_code="A01234",  # Duplicate full_code
                abbreviated_description="Duplicate",
                full_description="Duplicate",
                icd_version="ICD-10"  # Same version = error
            )
    
    def test_code_same_code_different_version(self):
        """Test same full_code can exist in different versions"""
        code_v9 = DiagnosisCode.objects.create(
            category=self.category,
            diagnosis_code="1234",
            full_code="A01234",  # Same code
            abbreviated_description="ICD-9 version",
            full_description="ICD-9 version",
            icd_version="ICD-9"  # Different version = OK
        )
        self.assertIsNotNone(code_v9.id)
    
    def test_code_category_relationship(self):
        """Test ForeignKey relationship"""
        self.assertEqual(self.code.category.code, "A0")
        self.assertEqual(self.category.diagnosis_codes.count(), 1)
        self.assertEqual(self.category.diagnosis_codes.first(), self.code)
    
    def test_code_category_protect_on_delete(self):
        """
        Test PROTECT constraint prevents category deletion
        Why? Data integrity - can't orphan codes
        """
        from django.db.models import ProtectedError
        
        with self.assertRaises(ProtectedError):
            self.category.delete()  # Should fail - codes reference it