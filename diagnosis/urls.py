from django.urls import path
from . import views

"""
URL Configuration for Diagnosis API

Why this structure?
- Clear, predictable endpoints
- RESTful conventions (plural nouns, HTTP methods)
- Hierarchical organization (codes, categories)
"""

urlpatterns = [
    # ==================== DIAGNOSIS CODES ====================
    
    # List all codes / Create new code
    # GET  /api/codes/     -> List with pagination
    # POST /api/codes/     -> Create new code
    path(
        'codes/',
        views.diagnosis_code_list_create,
        name='diagnosis-code-list-create'
    ),
    
    # Operations on specific code by ID
    # GET    /api/codes/1/  -> Retrieve code #1
    # PUT    /api/codes/1/  -> Update code #1 (full)
    # PATCH  /api/codes/1/  -> Update code #1 (partial)
    # DELETE /api/codes/1/  -> Delete code #1
    path(
        'codes/<int:pk>/',  # <int:pk> captures integer primary key
        views.diagnosis_code_detail,
        name='diagnosis-code-detail'
    ),
    
    # ==================== DIAGNOSIS CATEGORIES ====================
    
    # List all categories / Create new category
    path(
        'categories/',
        views.diagnosis_category_list_create,
        name='diagnosis-category-list-create'
    ),
    
    # Operations on specific category by ID
    path(
        'categories/<int:pk>/',
        views.diagnosis_category_detail,
        name='diagnosis-category-detail'
    ),
]