import os
import tempfile
import unittest

import extraction_coordinator
import services


class ExtractionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "extraction-coordinator-test.db")
        self.original_database_file = services.DATABASE_FILE
        services.DATABASE_FILE = self.database_path
        services.init_db()

        self.thesis_id = services.create_thesis(
            company_name="Test Co",
            ticker="TST",
            decision_question="Can Athena prepare this evaluation for analyst review as of 2000-01-01?",
            account_type=None,
            portfolio_role=None,
            primary_horizon=None,
            regime_state=None,
            reviewer="tester",
            status="Draft",
            drl=0,
            validation_mode_enabled=False,
            evidence_cutoff_date=None,
        )
        self.preparation_id = services.insert_query(
            """
            INSERT INTO evaluation_preparations
            (
                ticker,
                observation_date,
                thesis_id,
                lifecycle_state,
                workspace_ready,
                readiness_status,
                evidence_discovery_status,
                candidate_count,
                discovery_warnings_json,
                evidence_acquisition_status,
                acquired_document_count,
                acquisition_warnings_json,
                extraction_status,
                extracted_observation_count,
                extraction_timestamp,
                extraction_warnings_json,
                extraction_reused,
                extractor_version,
                warnings_json,
                errors_json,
                status_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "TST",
                "2000-01-01",
                int(self.thesis_id),
                "requested",
                1,
                "pending",
                "discovered",
                1,
                "[]",
                "acquired",
                1,
                "[]",
                "pending",
                0,
                None,
                "[]",
                0,
                extraction_coordinator.DEFAULT_EXTRACTOR_VERSION,
                "[]",
                "[]",
                "{}",
            ),
        )

        self.acquired_document_id = services.insert_query(
            """
            INSERT INTO evaluation_acquired_documents
            (
                preparation_id,
                thesis_id,
                title,
                source,
                document_type,
                publication_date,
                reference_url,
                reference_id,
                provider_name,
                discovery_provider,
                discovery_source,
                original_candidate_identifier,
                acquisition_status,
                retrieval_timestamp,
                source_reference,
                content_type,
                source_content,
                source_content_hash,
                acquisition_error,
                warnings_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                int(self.preparation_id),
                int(self.thesis_id),
                "Test filing",
                "SEC",
                "10-K",
                "2000-01-01",
                "https://www.sec.gov/Archives/test.htm",
                "ACC-77",
                "SEC EDGAR Acquisition",
                "SEC EDGAR",
                "SEC",
                "ACC-77",
                "acquired",
                "https://www.sec.gov/Archives/test.htm",
                "text/html",
                "sample source text",
                "hash-1",
                "",
                "[]",
            ),
        )

    def tearDown(self):
        services.DATABASE_FILE = self.original_database_file
        self.temp_dir.cleanup()

    def test_extraction_reuse_for_same_version_and_hash(self):
        original_extract = extraction_coordinator.extract_observation_suggestions_from_text

        def fake_extract(**kwargs):
            return {
                "success": True,
                "message": "ok",
                "suggestions": [
                    {
                        "passage": "Revenue remained durable.",
                        "pillar_signal": "B3",
                        "confidence": "high",
                        "source_location": "p.12",
                    }
                ],
            }

        extraction_coordinator.extract_observation_suggestions_from_text = fake_extract
        try:
            first = extraction_coordinator.coordinate_extraction(
                preparation_id=self.preparation_id,
                thesis_id=self.thesis_id,
                acquired_documents=[
                    {
                        "id": self.acquired_document_id,
                        "title": "Test filing",
                        "source": "SEC",
                        "document_type": "10-K",
                        "acquisition_status": "acquired",
                        "source_content": "sample source text",
                        "source_content_hash": "hash-1",
                        "source_reference": "https://www.sec.gov/Archives/test.htm",
                        "original_candidate_identifier": "ACC-77",
                        "retrieval_timestamp": "2000-01-01T00:00:00",
                    }
                ],
                extractor_version="theia-v1",
            )
            second = extraction_coordinator.coordinate_extraction(
                preparation_id=self.preparation_id,
                thesis_id=self.thesis_id,
                acquired_documents=[
                    {
                        "id": self.acquired_document_id,
                        "title": "Test filing",
                        "source": "SEC",
                        "document_type": "10-K",
                        "acquisition_status": "acquired",
                        "source_content": "sample source text",
                        "source_content_hash": "hash-1",
                        "source_reference": "https://www.sec.gov/Archives/test.htm",
                        "original_candidate_identifier": "ACC-77",
                        "retrieval_timestamp": "2000-01-01T00:00:00",
                    }
                ],
                extractor_version="theia-v1",
            )
        finally:
            extraction_coordinator.extract_observation_suggestions_from_text = original_extract

        self.assertEqual(first["extraction_status"], "completed")
        self.assertEqual(first["extracted_observation_count"], 1)
        self.assertFalse(first["extraction_reused"])

        self.assertEqual(second["extraction_status"], "completed")
        self.assertEqual(second["extracted_observation_count"], 1)
        self.assertTrue(second["extraction_reused"])

    def test_extractor_version_invalidation_triggers_new_extraction(self):
        original_extract = extraction_coordinator.extract_observation_suggestions_from_text

        call_count = {"value": 0}

        def fake_extract(**kwargs):
            call_count["value"] += 1
            return {
                "success": True,
                "message": "ok",
                "suggestions": [
                    {
                        "passage": f"signal-{call_count['value']}",
                        "pillar_signal": "B1",
                        "confidence": "medium",
                        "source_location": "p.1",
                    }
                ],
            }

        extraction_coordinator.extract_observation_suggestions_from_text = fake_extract
        try:
            extraction_coordinator.coordinate_extraction(
                preparation_id=self.preparation_id,
                thesis_id=self.thesis_id,
                acquired_documents=[
                    {
                        "id": self.acquired_document_id,
                        "title": "Test filing",
                        "acquisition_status": "acquired",
                        "source_content": "sample source text",
                        "source_content_hash": "hash-1",
                        "source_reference": "https://www.sec.gov/Archives/test.htm",
                        "original_candidate_identifier": "ACC-77",
                        "retrieval_timestamp": "2000-01-01T00:00:00",
                    }
                ],
                extractor_version="theia-v1",
            )
            second = extraction_coordinator.coordinate_extraction(
                preparation_id=self.preparation_id,
                thesis_id=self.thesis_id,
                acquired_documents=[
                    {
                        "id": self.acquired_document_id,
                        "title": "Test filing",
                        "acquisition_status": "acquired",
                        "source_content": "sample source text",
                        "source_content_hash": "hash-1",
                        "source_reference": "https://www.sec.gov/Archives/test.htm",
                        "original_candidate_identifier": "ACC-77",
                        "retrieval_timestamp": "2000-01-01T00:00:00",
                    }
                ],
                extractor_version="theia-v2",
            )
        finally:
            extraction_coordinator.extract_observation_suggestions_from_text = original_extract

        self.assertEqual(call_count["value"], 2)
        self.assertFalse(second["extraction_reused"])

    def test_provenance_is_persisted_for_extracted_observations(self):
        original_extract = extraction_coordinator.extract_observation_suggestions_from_text

        def fake_extract(**kwargs):
            return {
                "success": True,
                "message": "ok",
                "suggestions": [
                    {
                        "passage": "Provenance check passage",
                        "pillar_signal": "B2",
                        "confidence": "high",
                        "source_location": "p.3",
                    }
                ],
            }

        extraction_coordinator.extract_observation_suggestions_from_text = fake_extract
        try:
            extraction_coordinator.coordinate_extraction(
                preparation_id=self.preparation_id,
                thesis_id=self.thesis_id,
                acquired_documents=[
                    {
                        "id": self.acquired_document_id,
                        "title": "Test filing",
                        "acquisition_status": "acquired",
                        "source_content": "sample source text",
                        "source_content_hash": "hash-1",
                        "source_reference": "https://www.sec.gov/Archives/test.htm",
                        "original_candidate_identifier": "ACC-77",
                        "retrieval_timestamp": "2000-01-01T00:00:00",
                    }
                ],
                extractor_version="theia-v1",
            )
        finally:
            extraction_coordinator.extract_observation_suggestions_from_text = original_extract

        provenance_df = services.fetch_dataframe(
            """
            SELECT preparation_id, thesis_id, acquired_document_id, original_candidate_identifier,
                   source_reference, acquisition_timestamp, extraction_timestamp, extractor_version
            FROM evaluation_extracted_observations
            """
        )
        self.assertFalse(provenance_df.empty)
        row = provenance_df.iloc[0]
        self.assertEqual(int(row["preparation_id"]), int(self.preparation_id))
        self.assertEqual(int(row["thesis_id"]), int(self.thesis_id))
        self.assertEqual(int(row["acquired_document_id"]), int(self.acquired_document_id))
        self.assertEqual(str(row["original_candidate_identifier"]).strip(), "ACC-77")
        self.assertTrue(str(row["source_reference"]).strip())
        self.assertTrue(str(row["extractor_version"]).strip())

    def test_failure_is_non_blocking_and_truthful(self):
        original_extract = extraction_coordinator.extract_observation_suggestions_from_text

        def fake_extract(**kwargs):
            return {
                "success": False,
                "message": "forced failure",
                "suggestions": [],
            }

        extraction_coordinator.extract_observation_suggestions_from_text = fake_extract
        try:
            result = extraction_coordinator.coordinate_extraction(
                preparation_id=self.preparation_id,
                thesis_id=self.thesis_id,
                acquired_documents=[
                    {
                        "id": self.acquired_document_id,
                        "title": "Test filing",
                        "acquisition_status": "acquired",
                        "source_content": "sample source text",
                        "source_content_hash": "hash-1",
                        "source_reference": "https://www.sec.gov/Archives/test.htm",
                        "original_candidate_identifier": "ACC-77",
                        "retrieval_timestamp": "2000-01-01T00:00:00",
                    }
                ],
                extractor_version="theia-v1",
            )
        finally:
            extraction_coordinator.extract_observation_suggestions_from_text = original_extract

        self.assertEqual(result["extraction_status"], "failed")
        self.assertEqual(result["extracted_observation_count"], 0)
        self.assertEqual(len(result["extraction_results"]), 1)
        self.assertEqual(result["extraction_results"][0]["extraction_status"], "failed")


if __name__ == "__main__":
    unittest.main()
