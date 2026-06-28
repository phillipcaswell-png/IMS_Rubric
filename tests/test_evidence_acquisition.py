import unittest

import evidence_acquisition


class EvidenceAcquisitionTests(unittest.TestCase):
    def test_normalize_acquisition_result_preserves_provenance_fields(self):
        candidate = {
            "title": "10-K",
            "source": "SEC",
            "document_type": "10-K",
            "publication_date": "2000-01-01",
            "reference_url": "https://www.sec.gov/Archives/example.htm",
            "reference_id": "ACC-100",
            "provider_name": "SEC EDGAR",
        }
        normalized = evidence_acquisition.normalize_acquisition_result(
            {
                "provider_name": "SEC EDGAR Acquisition",
                "acquisition_status": "acquired",
                "retrieval_timestamp": "2000-01-02T10:00:00",
                "source_reference": "https://www.sec.gov/Archives/example.htm",
                "content_type": "text/html",
                "source_content": "hello world",
                "acquisition_error": "",
                "warnings": [],
            },
            candidate,
        )

        expected_keys = {
            "title",
            "source",
            "document_type",
            "publication_date",
            "reference_url",
            "reference_id",
            "provider_name",
            "discovery_provider",
            "discovery_source",
            "original_candidate_identifier",
            "acquisition_status",
            "retrieval_timestamp",
            "source_reference",
            "content_type",
            "source_content",
            "source_content_hash",
            "acquisition_error",
            "warnings",
            "acquired_source_material",
        }
        self.assertEqual(set(normalized.keys()), expected_keys)
        self.assertEqual(normalized["original_candidate_identifier"], "ACC-100")
        self.assertEqual(normalized["discovery_provider"], "SEC EDGAR")

    def test_acquire_supported_candidates_reports_unsupported_truthfully(self):
        result = evidence_acquisition.acquire_supported_candidates(
            candidate_documents=[
                {
                    "title": "News Item",
                    "source": "Other Source",
                    "document_type": "Article",
                    "publication_date": "2000-01-01",
                    "reference_url": "https://example.test/article",
                    "reference_id": "N-1",
                    "provider_name": "Custom Discovery",
                }
            ],
            providers=[evidence_acquisition.SecEdgarAcquisitionProvider()],
        )

        self.assertEqual(result["acquisition_status"], "unavailable")
        self.assertEqual(result["acquired_document_count"], 0)
        self.assertEqual(result["acquired_documents"][0]["acquisition_status"], "unsupported")

    def test_acquire_candidate_provider_failure_is_non_fatal(self):
        class BrokenProvider:
            provider_name = "Broken"

            def supports(self, candidate):
                return True

            def acquire(self, candidate):
                raise RuntimeError("network down")

        result = evidence_acquisition.acquire_candidate(
            {
                "title": "10-K",
                "source": "SEC",
                "document_type": "10-K",
                "publication_date": "2000-01-01",
                "reference_url": "https://www.sec.gov/Archives/example.htm",
                "reference_id": "ACC-2",
                "provider_name": "SEC EDGAR",
            },
            providers=[BrokenProvider()],
        )

        self.assertEqual(result["acquisition_status"], "failed")
        self.assertIn("Provider failure", result["acquisition_error"])


if __name__ == "__main__":
    unittest.main()
