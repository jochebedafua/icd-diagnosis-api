import os
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from diagnosis.models import DiagnosisCategory, DiagnosisCode

"""
Custom Django Management Command for Importing ICD Codes

Why a management command?
- Runs via manage.py (standard Django pattern)
- Can be triggered in Docker startup
- Transactional: all-or-nothing imports
- Reusable for different ICD versions
- Can be automated in deployment scripts

Usage:
    python manage.py import_icd_codes --icd-version=ICD-10
"""


class Command(BaseCommand):
    help = "Import ICD CSV data into Diagnosis models"

    def add_arguments(self, parser):
        """
        Add command-line arguments
        
        Why --icd-version parameter?
        - Same command works for ICD-9, ICD-10, ICD-11
        - Explicit versioning prevents mistakes
        - Makes command self-documenting
        """
        parser.add_argument(
            '--icd-version',
            type=str,
            default='ICD-10',
            help='ICD version being imported (e.g., ICD-9, ICD-10, ICD-11)'
        )

    @transaction.atomic  # Why? Ensures all-or-nothing import
    def handle(self, *args, **options):
        """
        Main command logic
        
        Why @transaction.atomic?
        - If any error occurs, entire import rolls back
        - Prevents partial imports (data integrity)
        - Database stays consistent
        """
        icd_version = options['icd_version']
        
        # Construct file paths relative to management command location
        base_dir = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "data"
        )
        categories_file = os.path.join(base_dir, "categories.csv")
        codes_file = os.path.join(base_dir, "codes.csv")

        # Validate files exist before processing
        # Why check first? Better error messages than FileNotFoundError
        if not os.path.exists(categories_file):
            self.stdout.write(
                self.style.ERROR(f"Categories file not found: {categories_file}")
            )
            self.stdout.write(
                self.style.WARNING("Tip: Place CSV files in the 'data/' directory")
            )
            return

        if not os.path.exists(codes_file):
            self.stdout.write(
                self.style.ERROR(f"Codes file not found: {codes_file}")
            )
            return

        categories_count = 0
        codes_count = 0
        categories_updated = 0
        codes_updated = 0

        # ==================== IMPORT CATEGORIES ====================
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"\n Importing categories for {icd_version}...")
        )
        
        with open(categories_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                """
                Why update_or_create?
                - Idempotent: Can run command multiple times safely
                - Updates existing records if present
                - Creates new records if missing
                - Prevents duplicate errors
                """
                category, created = DiagnosisCategory.objects.update_or_create(
                    code=row["Category Code"],
                    icd_version=icd_version,
                    defaults={"title": row["Category Title"]}
                )
                
                if created:
                    categories_count += 1
                else:
                    categories_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Categories: {categories_count} new, {categories_updated} updated"
            )
        )

        # ==================== IMPORT DIAGNOSIS CODES ====================
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"\n Importing diagnosis codes for {icd_version}...")
        )
        
        with open(codes_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader, 1):
                try:
                    # Get the category for this code
                    # Why try/except? Category might not exist
                    category = DiagnosisCategory.objects.get(
                        code=row["Category Code"],
                        icd_version=icd_version
                    )

                    # Create or update diagnosis code
                    code, created = DiagnosisCode.objects.update_or_create(
                        full_code=row["Full Code"],
                        icd_version=icd_version,
                        defaults={
                            "category": category,
                            "diagnosis_code": row["Diagnosis Code"],
                            "abbreviated_description": row["Abbreviated Description"],
                            "full_description": row["Full Description"],
                            "is_active": True
                        }
                    )
                    
                    if created:
                        codes_count += 1
                    else:
                        codes_updated += 1
                    
                    # Progress indicator for large imports
                    # Why every 100? Balance between feedback and spam
                    if i % 100 == 0:
                        self.stdout.write(f"  Processed {i} codes...")

                except DiagnosisCategory.DoesNotExist:
                    # Log warning but continue processing
                    # Why not fail? Some codes might have missing categories
                    self.stdout.write(
                        self.style.WARNING(
                            f"Category not found for code {row['Full Code']}: "
                            f"{row['Category Code']}"
                        )
                    )
                    continue
                
                except KeyError as e:
                    # CSV format error
                    self.stdout.write(
                        self.style.ERROR(
                            f"CSV format error at row {i}: Missing column {e}"
                        )
                    )
                    raise  # Stop import on format errors

        # ==================== SUMMARY ====================
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\n"
                f"Import completed for {icd_version}\n"
                f"{'='*60}\n"
                f"Categories: {categories_count} new, {categories_updated} updated\n"
                f"Codes: {codes_count} new, {codes_updated} updated\n"
                f"{'='*60}\n"
            )
        )