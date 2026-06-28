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


if __name__ == "__main__":
    unittest.main()