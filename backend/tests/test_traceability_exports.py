import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Ensure backend folder is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import export_service
from traceability_service import build_traceability_matrix, _detect_ambiguity, _extract_diagram_components, _heuristic_match_requirement


class TestTraceabilityAndExport(unittest.TestCase):
    def setUp(self):
        self.mock_project = MagicMock()
        self.mock_project.id = 1
        self.mock_project.title = "Healthcare Patient Portal"
        self.mock_project.description = "A secure web portal for patients to view medical records and schedule appointments seamlessly."
        self.mock_project.analysis_json = json.dumps({
            "objectives": ["Provide secure access to patient records", "Streamline appointment scheduling"],
            "scope": "Web-based portal for clinic patients and staff.",
            "target_users": ["Patients", "Doctors", "Receptionists"],
            "functional_requirements": [
                "The system shall allow users to log in securely using email and password.",
                "The system shall provide a seamless interface for booking appointments quickly.",
                "The system shall display patient medical records and lab test results."
            ],
            "non_functional_requirements": ["99.9% uptime", "HIPAA compliant"],
            "constraints": ["PostgreSQL database", "FastAPI backend"],
            "assumptions": ["Patients have internet access"]
        })
        self.mock_project.diagrams_json = json.dumps({
            "use_case_diagram": "graph TD\nUser((Patient)) --> UC1(User Login)\nUser --> UC2(Book Appointment)",
            "class_diagram": "classDiagram\nclass User {\n+login()\n}\nclass Appointment {\n+book()\n}",
            "er_diagram": "erDiagram\nUSERS ||--o{ APPOINTMENTS : books"
        })
        self.mock_project.api_spec_json = json.dumps({
            "endpoints": [
                {"method": "POST", "path": "/api/auth/login", "description": "Authenticate user with email and password"},
                {"method": "POST", "path": "/api/appointments", "description": "Book a new appointment for patient"},
                {"method": "GET", "path": "/api/records", "description": "Retrieve medical records for patient"}
            ]
        })
        self.mock_project.tech_stack_json = json.dumps({
            "frontend": {"technology": "Angular", "reason": "Type-safe robust framework"},
            "backend": {"technology": "FastAPI", "reason": "High performance async Python"},
            "database": {"technology": "PostgreSQL", "reason": "ACID compliance for medical data"},
            "cloud_deployment": {"technology": "Docker", "reason": "Containerized deployment"},
            "third_party_integrations": []
        })
        self.mock_project.planning_json = json.dumps({
            "estimated_duration_weeks": 8,
            "phases": [{"name": "Foundation", "duration_weeks": 3, "description": "Auth and schema"}],
            "sprints": [{"name": "Sprint 1", "duration_weeks": 2, "goals": ["Auth endpoints"]}],
            "milestones": [{"name": "Alpha", "description": "Core workflows functional"}],
            "risks": [{"risk": "Data leak", "impact": "High", "mitigation": "Encryption at rest"}]
        })
        self.mock_project.traceability_json = None

    def test_ambiguity_detection(self):
        ambiguous_text = "The system shall provide a seamless and user-friendly interface that works fast."
        flags = _detect_ambiguity(ambiguous_text)
        self.assertTrue(len(flags) >= 2)

    def test_diagram_components_extraction(self):
        diagrams = json.loads(self.mock_project.diagrams_json)
        components = _extract_diagram_components(diagrams)
        self.assertTrue(any("User Login" in c for c in components))
        self.assertTrue(any("Appointment" in c for c in components))

    def test_heuristic_matching(self):
        diagrams = json.loads(self.mock_project.diagrams_json)
        components = _extract_diagram_components(diagrams)
        endpoints = json.loads(self.mock_project.api_spec_json)["endpoints"]
        req = "The system shall allow users to log in securely."
        matched_diags, matched_apis = _heuristic_match_requirement(req, components, endpoints)
        self.assertTrue(len(matched_diags) > 0 or len(matched_apis) > 0)

    @patch("traceability_service.generate_traceability_matrix_ai")
    def test_build_traceability_matrix(self, mock_ai):
        mock_ai.return_value = {
            "mappings": [
                {
                    "requirement_index": 0,
                    "diagram_elements": ["Use Case: User Login", "Class: User"],
                    "api_endpoints": ["POST /api/auth/login"],
                    "validation_notes": "Tested mapping"
                }
            ],
            "validation_summary": "Test coverage complete."
        }
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.first.return_value = None

        matrix = build_traceability_matrix(self.mock_project, db_mock)
        self.assertEqual(matrix["total_requirements"], 3)
        self.assertIn("items", matrix)
        self.assertEqual(len(matrix["items"]), 3)
        self.assertIn("completeness_percentage", matrix)
        self.assertIn("validation_summary", matrix)

    @patch("export_service.render_mermaid_to_png", return_value=None)
    @patch("traceability_service.generate_traceability_matrix_ai")
    def test_export_pdf_and_docx(self, mock_ai, mock_render):
        mock_ai.return_value = {
            "mappings": [
                {
                    "requirement_index": 0,
                    "diagram_elements": ["Use Case: User Login"],
                    "api_endpoints": ["POST /api/auth/login"],
                    "validation_notes": "Valid"
                }
            ],
            "validation_summary": "Test coverage summary."
        }
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.first.return_value = None

        # Test before traceability
        pdf1 = export_service.generate_pdf(self.mock_project)
        docx1 = export_service.generate_docx(self.mock_project)
        self.assertGreater(len(pdf1.getvalue()), 100)
        self.assertGreater(len(docx1.getvalue()), 100)

        # Attach traceability and test again
        matrix = build_traceability_matrix(self.mock_project, db_mock)
        self.mock_project.traceability_json = json.dumps(matrix)

        pdf2 = export_service.generate_pdf(self.mock_project)
        docx2 = export_service.generate_docx(self.mock_project)
        self.assertGreater(len(pdf2.getvalue()), 100)
        self.assertGreater(len(docx2.getvalue()), 100)


if __name__ == "__main__":
    unittest.main()
