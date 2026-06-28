import unittest

import evidence_discovery


class EvidenceDiscoveryTests(unittest.TestCase):
    def test_normalize_candidate_shape(self):
        normalized = evidence_discovery.normalize_candidate(
            {
                "title": "10-K",
                "source": "SEC",
                "document_type": "10-K",
                "publication_date": "2000-01-01",
                "reference_url": "https://example.test",
                "reference_id": "ACC-1",
                "discovery_status": "candidate",
                "warnings": ["metadata only"],
            },
            provider_name="SEC EDGAR",
        )

        expected_keys = {
            "title",
            "source",
            "document_type",
            "publication_date",
            "reference_url",
            "reference_id",
            "discovery_status",
            "provider_name",
            "warnings",
            "candidate_evidence",
        }
        self.assertEqual(set(normalized.keys()), expected_keys)
        self.assertTrue(normalized["candidate_evidence"])

    def test_aggregate_discovery_results_dedupes_and_preserves_shape(self):
        aggregated = evidence_discovery.aggregate_discovery_results(
            [
                {
                    "provider_name": "Provider A",
                    "status": "discovered",
                    "candidates": [
                        {
                            "title": "10-K",
                            "source": "SEC",
                            "document_type": "10-K",
                            "publication_date": "2000-01-01",
                            "reference_url": "https://example.test/1",
                            "reference_id": "ACC-1",
                            "discovery_status": "candidate",
                            "warnings": [],
                        }
                    ],
                    "warnings": ["source-latency"],
                },
                {
                    "provider_name": "Provider B",
                    "status": "discovered",
                    "candidates": [
                        {
                            "title": "10-K",
                            "source": "SEC",
                            "document_type": "10-K",
                            "publication_date": "2000-01-01",
                            "reference_url": "https://example.test/1",
                            "reference_id": "ACC-1",
                            "discovery_status": "candidate",
                            "warnings": [],
                        }
                    ],
                    "warnings": [],
                },
            ]
        )

        self.assertEqual(aggregated["evidence_discovery_status"], "discovered")
        self.assertGreaterEqual(aggregated["candidate_count"], 1)
        self.assertIn("candidate_documents", aggregated)
        self.assertIn("discovery_warnings", aggregated)

        candidate = aggregated["candidate_documents"][0]
        expected_candidate_keys = {
            "title",
            "source",
            "document_type",
            "publication_date",
            "reference_url",
            "reference_id",
            "discovery_status",
            "provider_name",
            "warnings",
            "candidate_evidence",
        }
        self.assertEqual(set(candidate.keys()), expected_candidate_keys)

    def test_discovery_handles_provider_failure_truthfully(self):
        class BrokenProvider:
            provider_name = "Broken"

            def discover(self, ticker, observation_date):
                raise RuntimeError("network down")

        result = evidence_discovery.discover_candidate_documents(
            ticker="KODK",
            observation_date="2000-01-01",
            providers=[BrokenProvider()],
        )

        self.assertEqual(result["evidence_discovery_status"], "failed")
        self.assertEqual(result["candidate_count"], 0)
        self.assertTrue(any("Provider failure" in warning for warning in result["discovery_warnings"]))


if __name__ == "__main__":
    unittest.main()
