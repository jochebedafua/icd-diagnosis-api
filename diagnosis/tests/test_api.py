from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from diagnosis.models import DiagnosisCategory, DiagnosisCode
import time

"""
API Tests

Why test APIs?
- Verify all endpoints work correctly
- Test CRUD operations
- Validate pagination
- Ensure <100ms response time
- Test error handling
"""


class DiagnosisCodeAPITest(TestCase):
    """Test DiagnosisCode API endpoints"""
    
    def setUp(self):
        """Create test data before each test"""
        self.client = APIClient()
        
        # Create test category
        self.category = DiagnosisCategory.objects.create(
            code="C21",
            title="Malignant neoplasm of anus and anal canal",
            icd_version="ICD-10"
        )
        
        # Create 25 test codes (to test pagination beyond 20)
        for i in range(25):
            DiagnosisCode.objects.create(
                category=self.category,
                diagnosis_code=f"{i:04d}",
                full_code=f"C21{i:04d}",
                abbreviated_description=f"Test code {i}",
                full_description=f"Full description for test code {i}",
                icd_version="ICD-10",
                is_active=True
            )
    
    # ==================== LIST ENDPOINT TESTS ====================
    
    def test_list_codes_pagination(self):
        """
        Test: List returns 20 codes per page
        Requirement: List diagnosis codes in batches of 20
        """
        url = reverse('diagnosis-code-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)  # First page: 20 items
        self.assertIsNotNone(response.data['next'])  # Has next page
        self.assertEqual(response.data['count'], 25)  # Total count
    
    def test_list_codes_second_page(self):
        """Test pagination to second page"""
        url = reverse('diagnosis-code-list-create')
        response = self.client.get(url, {'page': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # Remaining 5 items
        self.assertIsNone(response.data['next'])  # No next page
        self.assertIsNotNone(response.data['previous'])  # Has previous page
    
    def test_list_codes_empty_page(self):
        """Test requesting page that doesn't exist"""
        url = reverse('diagnosis-code-list-create')
        response = self.client.get(url, {'page': 999})
        
        # DRF returns 404 for invalid page
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ==================== RETRIEVE ENDPOINT TESTS ====================
    
    def test_retrieve_code_by_id(self):
        """
        Test: Retrieve specific code by ID
        Requirement: Retrieve diagnosis codes by ID
        """
        code = DiagnosisCode.objects.first()
        url = reverse('diagnosis-code-detail', kwargs={'pk': code.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_code'], code.full_code)
        self.assertEqual(response.data['id'], code.id)
        # Should include nested category details
        self.assertIn('category_details', response.data)
    
    def test_retrieve_nonexistent_code(self):
        """Test retrieving code that doesn't exist"""
        url = reverse('diagnosis-code-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ==================== CREATE ENDPOINT TESTS ====================
    
    def test_create_code(self):
        """
        Test: Create new diagnosis code
        Requirement: Create a new diagnosis code record
        """
        url = reverse('diagnosis-code-list-create')
        data = {
            'category': self.category.id,
            'diagnosis_code': '9999',
            'full_code': 'C219999',
            'abbreviated_description': 'New test code',
            'full_description': 'New test code full description',
            'icd_version': 'ICD-10',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['full_code'], 'C219999')
        # Verify database record created
        self.assertEqual(
            DiagnosisCode.objects.filter(full_code='C219999').count(), 
            1
        )
    
    def test_create_code_invalid_data(self):
        """Test creating code with invalid/missing data"""
        url = reverse('diagnosis-code-list-create')
        data = {
            'category': self.category.id,
            # Missing required fields
            'icd_version': 'ICD-10',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('full_code', response.data)  # Error for missing field
    
    def test_create_code_duplicate(self):
        """Test creating duplicate code (same full_code + icd_version)"""
        existing_code = DiagnosisCode.objects.first()
        url = reverse('diagnosis-code-list-create')
        data = {
            'category': self.category.id,
            'diagnosis_code': existing_code.diagnosis_code,
            'full_code': existing_code.full_code,  # Duplicate
            'abbreviated_description': 'Duplicate',
            'full_description': 'Duplicate',
            'icd_version': existing_code.icd_version,  # Same version
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        # Should fail due to unique_together constraint
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ==================== UPDATE ENDPOINT TESTS ====================
    
    def test_update_code_full(self):
        """
        Test: Full update (PUT)
        Requirement: Edit an existing diagnosis code record
        """
        code = DiagnosisCode.objects.first()
        url = reverse('diagnosis-code-detail', kwargs={'pk': code.id})
        data = {
            'category': self.category.id,
            'diagnosis_code': code.diagnosis_code,
            'full_code': code.full_code,
            'abbreviated_description': 'Updated description',
            'full_description': 'Updated full description',
            'icd_version': code.icd_version,
            'is_active': False  # Changed
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        code.refresh_from_db()
        self.assertEqual(code.abbreviated_description, 'Updated description')
        self.assertFalse(code.is_active)
    
    def test_update_code_partial(self):
        """
        Test: Partial update (PATCH)
        Requirement: Edit an existing diagnosis code record
        """
        code = DiagnosisCode.objects.first()
        original_full_code = code.full_code
        url = reverse('diagnosis-code-detail', kwargs={'pk': code.id})
        data = {
            'is_active': False,  # Only update this field
            'abbreviated_description': 'Partially updated'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        code.refresh_from_db()
        self.assertEqual(code.abbreviated_description, 'Partially updated')
        self.assertFalse(code.is_active)
        # Other fields should remain unchanged
        self.assertEqual(code.full_code, original_full_code)
    
    # ==================== DELETE ENDPOINT TESTS ====================
    
    def test_delete_code(self):
        """
        Test: Delete code by ID
        Requirement: Delete a diagnosis code by ID
        """
        code = DiagnosisCode.objects.first()
        code_id = code.id
        url = reverse('diagnosis-code-detail', kwargs={'pk': code_id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify code is deleted from database
        self.assertEqual(DiagnosisCode.objects.filter(id=code_id).count(), 0)
    
    def test_delete_nonexistent_code(self):
        """Test deleting code that doesn't exist"""
        url = reverse('diagnosis-code-detail', kwargs={'pk': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ==================== FILTERING TESTS ====================
    
    def test_filter_by_version(self):
        """Test filtering codes by version"""
        # Create ICD-9 code
        DiagnosisCode.objects.create(
            category=self.category,
            diagnosis_code="TEST",
            full_code="ICD9TEST",
            abbreviated_description="ICD-9 test",
            full_description="ICD-9 test description",
            icd_version="ICD-9",
            is_active=True
        )
        
        url = reverse('diagnosis-code-list-create')
        response = self.client.get(url, {'icd_version': 'ICD-10'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All results should be ICD-10
        for code in response.data['results']:
            self.assertEqual(code['icd_version'], 'ICD-10')
    
    def test_filter_by_active_status(self):
        """Test filtering active/inactive codes"""
        # Create inactive code
        DiagnosisCode.objects.create(
            category=self.category,
            diagnosis_code="INACTIVE",
            full_code="INACTIVE01",
            abbreviated_description="Inactive code",
            full_description="Inactive code",
            icd_version="ICD-10",
            is_active=False
        )
        
        url = reverse('diagnosis-code-list-create')
        
        # Default: only active codes
        response = self.client.get(url)
        self.assertTrue(all(code['is_active'] for code in response.data['results']))
        
        # Include inactive
        response = self.client.get(url, {'include_inactive': 'true'})
        # Should now include the inactive code
        self.assertEqual(response.data['count'], 26)  # 25 + 1 inactive
    
    def test_search_codes(self):
        """Test search functionality"""
        url = reverse('diagnosis-code-list-create')
        response = self.client.get(url, {'search': 'C210000'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        # Should find the code with full_code=C210000
    
    # ==================== PERFORMANCE TEST ====================
    
    def test_response_time_under_100ms(self):
        """
        Test: API responds within 100ms
        Requirement: All API endpoints should respond within 100ms
        """
        url = reverse('diagnosis-code-list-create')
        
        # Warm up query (first query might be slower due to Django setup)
        self.client.get(url)
        
        # Actual test - measure response time
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(
            response_time_ms, 100,
            f"Response time {response_time_ms:.2f}ms exceeds 100ms limit"
        )


class DiagnosisCategoryAPITest(TestCase):
    """Test DiagnosisCategory API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.category_data = {
            'code': 'C21',
            'title': 'Malignant neoplasm of anus and anal canal',
            'icd_version': 'ICD-10'
        }
    
    def test_create_category(self):
        """Test creating a category"""
        url = reverse('diagnosis-category-list-create')
        response = self.client.post(url, self.category_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'C21')
    
    def test_list_categories(self):
        """Test listing categories"""
        DiagnosisCategory.objects.create(**self.category_data)
        url = reverse('diagnosis-category-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)