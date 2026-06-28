import os
import tempfile
import unittest

import evaluation_engine
import services


class EvaluationEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "evaluation-engine-test.db")
        self.original_database_file = services.DATABASE_FILE
        services.DATABASE_FILE = self.database_path
        services.init_db()

    def tearDown(self):
        services.DATABASE_FILE = self.original_database_file
        self.temp_dir.cleanup()

    def test_prepare_evaluation_creates_canonical_preparation_object(self):
        result = evaluation_engine.prepare_evaluation("KODK", "2000-01-01")

        self.assertEqual(result["ticker"], "KODK")
        self.assertEqual(result["observation_date"], "2000-01-01")
        self.assertEqual(result["lifecycle_state"], evaluation_engine.LIFECYCLE_READY_FOR_ANALYST)
        self.assertTrue(result["workspace_ready"])
        self.assertEqual(result["readiness_status"], evaluation_engine.READINESS_READY_FOR_ANALYST)
        self.assertIn(result["evidence_discovery_status"], ["discovered", "unavailable", "failed", "pending"])
        self.assertIsInstance(result["candidate_count"], int)
        self.assertIsInstance(result["candidate_documents"], list)
        self.assertIsInstance(result["discovery_warnings"], list)
        self.assertIn(result["acquisition_status"], ["acquired", "unavailable", "failed", "pending", "not_attempted"])
        self.assertIsInstance(result["acquired_document_count"], int)
        self.assertIsInstance(result["acquired_documents"], list)
        self.assertIsInstance(result["acquisition_warnings"], list)
        self.assertIn(result["extraction_status"], ["completed", "unsupported", "failed", "pending", "not_attempted"])
        self.assertIsInstance(result["extracted_observation_count"], int)
        self.assertIsInstance(result["extraction_results"], list)
        self.assertIsInstance(result["extraction_warnings"], list)
        self.assertIsInstance(result["extraction_reused"], bool)
        self.assertIsInstance(result["extractor_version"], str)
        self.assertEqual(result["preparation_action"], "created")
        self.assertEqual(result["thesis_action"], "created")
        self.assertIsInstance(result["preparation_id"], int)
        self.assertIsInstance(result["thesis_id"], int)
        self.assertEqual(
            sorted(result.keys()),
            sorted(
                [
                    "ticker",
                    "observation_date",
                    "lifecycle_state",
                    "thesis_id",
                    "preparation_id",
                    "workspace_ready",
                    "readiness_status",
                    "evidence_discovery_status",
                    "candidate_count",
                    "candidate_documents",
                    "discovery_warnings",
                    "acquisition_status",
                    "acquired_document_count",
                    "acquired_documents",
                    "acquisition_warnings",
                    "extraction_status",
                    "extracted_observation_count",
                    "extraction_timestamp",
                    "extraction_results",
                    "extraction_warnings",
                    "extraction_reused",
                    "extractor_version",
                    "preparation_action",
                    "thesis_action",
                    "warnings",
                    "errors",
                    "step_status",
                    "updated_at",
                    "created_at",
                ]
            ),
        )

    def test_prepare_evaluation_is_idempotent_for_same_request_key(self):
        first = evaluation_engine.prepare_evaluation("KODK", "2000-01-01")
        second = evaluation_engine.prepare_evaluation("kodk", "2000-01-01")

        self.assertEqual(first["preparation_id"], second["preparation_id"])
        self.assertEqual(first["thesis_id"], second["thesis_id"])
        self.assertEqual(second["preparation_action"], "reused")
        self.assertEqual(second["thesis_action"], "reused")
        self.assertEqual(sorted(first.keys()), sorted(second.keys()))

        preparations_df = services.fetch_dataframe("SELECT * FROM evaluation_preparations")
        theses_df = services.fetch_dataframe("SELECT * FROM theses")

        self.assertEqual(len(preparations_df.index), 1)
        self.assertEqual(len(theses_df.index), 1)

    def test_prepare_evaluation_returns_truthful_failure_for_invalid_request(self):
        result = evaluation_engine.prepare_evaluation("", "")

        self.assertEqual(result["lifecycle_state"], evaluation_engine.LIFECYCLE_FAILED)
        self.assertEqual(result["readiness_status"], evaluation_engine.READINESS_FAILED)
        self.assertFalse(result["workspace_ready"])
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["candidate_documents"], [])
        self.assertIn("ticker and observation_date are required.", result["errors"])

    def test_prepare_evaluation_reports_partial_when_workspace_verification_fails(self):
        original_get_overview_metrics = evaluation_engine.get_overview_metrics

        def _raise_failure(thesis_id):
            raise RuntimeError("workspace unavailable")

        evaluation_engine.get_overview_metrics = _raise_failure
        try:
            result = evaluation_engine.prepare_evaluation("MSFT", "2001-01-01")
        finally:
            evaluation_engine.get_overview_metrics = original_get_overview_metrics

        self.assertEqual(result["lifecycle_state"], evaluation_engine.LIFECYCLE_PARTIAL)
        self.assertEqual(result["readiness_status"], evaluation_engine.READINESS_PARTIAL)
        self.assertFalse(result["workspace_ready"])
        self.assertTrue(any("Workspace verification failed" in item for item in result["errors"]))

    def test_prepare_evaluation_reuses_persisted_candidate_documents(self):
        class StaticProvider:
            provider_name = "Static Provider"

            def discover(self, ticker, observation_date):
                return {
                    "provider_name": self.provider_name,
                    "status": "discovered",
                    "candidates": [
                        {
                            "title": f"{ticker} annual report",
                            "source": "Static",
                            "document_type": "10-K",
                            "publication_date": "2000-01-01",
                            "reference_url": "https://example.test/10k",
                            "reference_id": "ACC-1",
                            "discovery_status": "candidate",
                            "warnings": [],
                        }
                    ],
                    "warnings": [],
                }

        provider = StaticProvider()
        first = evaluation_engine.prepare_evaluation("KODK", "2000-01-01", discovery_providers=[provider])
        second = evaluation_engine.prepare_evaluation("KODK", "2000-01-01", discovery_providers=[])

        self.assertEqual(first["candidate_count"], 1)
        self.assertEqual(second["candidate_count"], 1)
        self.assertEqual(second["candidate_documents"][0]["reference_id"], "ACC-1")
        self.assertGreaterEqual(len(second["acquired_documents"]), 1)
        self.assertEqual(second["acquired_documents"][0]["original_candidate_identifier"], "ACC-1")

    def test_prepare_evaluation_skips_acquisition_when_discovery_has_no_candidates(self):
        class UnavailableProvider:
            provider_name = "Unavailable"

            def discover(self, ticker, observation_date):
                return {
                    "provider_name": self.provider_name,
                    "status": "unavailable",
                    "candidates": [],
                    "warnings": ["No candidates available."],
                }

        result = evaluation_engine.prepare_evaluation(
            "IBM",
            "2000-01-01",
            discovery_providers=[UnavailableProvider()],
        )

        self.assertEqual(result["evidence_discovery_status"], "unavailable")
        self.assertEqual(result["acquisition_status"], "not_attempted")
        self.assertEqual(result["extraction_status"], "not_attempted")
        self.assertEqual(result["acquired_document_count"], 0)
        self.assertEqual(result["acquired_documents"], [])

    def test_prepare_evaluation_acquisition_failure_does_not_block_workspace(self):
        class StaticProvider:
            provider_name = "Static Provider"

            def discover(self, ticker, observation_date):
                return {
                    "provider_name": self.provider_name,
                    "status": "discovered",
                    "candidates": [
                        {
                            "title": "10-K",
                            "source": "SEC",
                            "document_type": "10-K",
                            "publication_date": "2000-01-01",
                            "reference_url": "https://example.test/10k",
                            "reference_id": "ACC-9",
                            "discovery_status": "candidate",
                            "warnings": [],
                        }
                    ],
                    "warnings": [],
                }

        class BrokenAcquisitionProvider:
            provider_name = "Broken Acquisition"

            def supports(self, candidate):
                return True

            def acquire(self, candidate):
                raise RuntimeError("source retrieval unavailable")

        result = evaluation_engine.prepare_evaluation(
            "IBM",
            "2000-01-01",
            discovery_providers=[StaticProvider()],
            acquisition_providers=[BrokenAcquisitionProvider()],
        )

        self.assertEqual(result["lifecycle_state"], evaluation_engine.LIFECYCLE_READY_FOR_ANALYST)
        self.assertTrue(result["workspace_ready"])
        self.assertEqual(result["acquisition_status"], "failed")
        self.assertEqual(result["acquired_document_count"], 0)
        self.assertGreaterEqual(len(result["acquired_documents"]), 1)
        self.assertTrue(any("Provider failure" in item.get("acquisition_error", "") for item in result["acquired_documents"]))

    def test_prepare_evaluation_discovery_failure_does_not_block_workspace(self):
        class BrokenProvider:
            provider_name = "Broken Provider"

            def discover(self, ticker, observation_date):
                raise RuntimeError("discovery offline")

        result = evaluation_engine.prepare_evaluation(
            "IBM",
            "2000-01-01",
            discovery_providers=[BrokenProvider()],
        )

        self.assertEqual(result["lifecycle_state"], evaluation_engine.LIFECYCLE_READY_FOR_ANALYST)
        self.assertTrue(result["workspace_ready"])
        self.assertEqual(result["evidence_discovery_status"], "failed")
        self.assertEqual(result["candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()