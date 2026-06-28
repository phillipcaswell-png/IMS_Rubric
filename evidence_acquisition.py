import hashlib
from datetime import datetime
from urllib import error as url_error
from urllib import request as url_request


ACQUISITION_STATUS_PENDING = "pending"
ACQUISITION_STATUS_ACQUIRED = "acquired"
ACQUISITION_STATUS_UNAVAILABLE = "unavailable"
ACQUISITION_STATUS_FAILED = "failed"
ACQUISITION_STATUS_UNSUPPORTED = "unsupported"
ACQUISITION_STATUS_NOT_ATTEMPTED = "not_attempted"


class SecEdgarAcquisitionProvider:
    """Acquire SEC filing source material for candidates discovered through SEC metadata."""

    provider_name = "SEC EDGAR Acquisition"

    def __init__(self, user_agent=None, timeout_seconds=8, max_content_chars=200000):
        self.user_agent = user_agent or "Athena/1.0 (evidence-acquisition)"
        self.timeout_seconds = int(timeout_seconds)
        self.max_content_chars = int(max_content_chars)

    def supports(self, candidate):
        if not isinstance(candidate, dict):
            return False

        reference_url = str(candidate.get("reference_url", "")).strip().lower()
        if not reference_url:
            return False

        if "sec.gov" not in reference_url:
            return False

        return reference_url.startswith("https://") or reference_url.startswith("http://")

    def acquire(self, candidate):
        normalized_candidate = _normalize_candidate(candidate)
        reference_url = normalized_candidate["reference_url"]
        retrieval_timestamp = datetime.now().isoformat()

        if not reference_url:
            return {
                **normalized_candidate,
                "provider_name": self.provider_name,
                "acquisition_status": ACQUISITION_STATUS_UNAVAILABLE,
                "retrieval_timestamp": retrieval_timestamp,
                "source_reference": "",
                "content_type": "",
                "source_content": "",
                "acquisition_error": "No source URL was available for acquisition.",
                "warnings": ["Candidate did not include a source URL."],
            }

        request = url_request.Request(reference_url, headers={"User-Agent": self.user_agent})
        try:
            with url_request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw_content = response.read()
                content_type = str(response.headers.get("Content-Type", "")).strip()
        except (url_error.URLError, url_error.HTTPError, TimeoutError) as exc:
            return {
                **normalized_candidate,
                "provider_name": self.provider_name,
                "acquisition_status": ACQUISITION_STATUS_FAILED,
                "retrieval_timestamp": retrieval_timestamp,
                "source_reference": reference_url,
                "content_type": "",
                "source_content": "",
                "acquisition_error": f"Acquisition failed: {type(exc).__name__}: {str(exc)}",
                "warnings": ["Source retrieval failed during preparation."],
            }

        source_content = ""
        acquisition_status = ACQUISITION_STATUS_ACQUIRED
        warnings = []
        if raw_content:
            try:
                decoded = raw_content.decode("utf-8", errors="replace")
                source_content = decoded[: self.max_content_chars]
                if len(decoded) > self.max_content_chars:
                    warnings.append("Source content was truncated to repository-safe size limits.")
            except Exception:
                acquisition_status = ACQUISITION_STATUS_UNAVAILABLE
                warnings.append("Source payload could not be decoded as text; reference retained only.")

        return {
            **normalized_candidate,
            "provider_name": self.provider_name,
            "acquisition_status": acquisition_status,
            "retrieval_timestamp": retrieval_timestamp,
            "source_reference": reference_url,
            "content_type": content_type,
            "source_content": source_content,
            "acquisition_error": "",
            "warnings": warnings,
        }


def acquire_candidate(candidate, providers=None):
    """Acquire one discovered candidate through the first supporting provider."""
    provider_chain = providers if providers is not None else [SecEdgarAcquisitionProvider()]
    normalized_candidate = _normalize_candidate(candidate)

    if not normalized_candidate["reference_url"]:
        return {
            **normalized_candidate,
            "provider_name": "No Acquisition Provider",
            "acquisition_status": ACQUISITION_STATUS_UNAVAILABLE,
            "retrieval_timestamp": datetime.now().isoformat(),
            "source_reference": "",
            "content_type": "",
            "source_content": "",
            "acquisition_error": "Candidate has no source URL/reference for acquisition.",
            "warnings": ["Candidate has no source URL/reference for acquisition."],
        }

    for provider in provider_chain:
        if hasattr(provider, "supports") and provider.supports(normalized_candidate):
            try:
                provider_result = provider.acquire(normalized_candidate)
            except Exception as exc:
                provider_result = {
                    **normalized_candidate,
                    "provider_name": getattr(provider, "provider_name", provider.__class__.__name__),
                    "acquisition_status": ACQUISITION_STATUS_FAILED,
                    "retrieval_timestamp": datetime.now().isoformat(),
                    "source_reference": normalized_candidate["reference_url"],
                    "content_type": "",
                    "source_content": "",
                    "acquisition_error": f"Provider failure: {type(exc).__name__}: {str(exc)}",
                    "warnings": ["Provider failure during source acquisition."],
                }
            return normalize_acquisition_result(provider_result, normalized_candidate)

    return {
        **normalized_candidate,
        "provider_name": "No Acquisition Provider",
        "acquisition_status": ACQUISITION_STATUS_UNSUPPORTED,
        "retrieval_timestamp": datetime.now().isoformat(),
        "source_reference": normalized_candidate["reference_url"],
        "content_type": "",
        "source_content": "",
        "acquisition_error": "No acquisition provider supports this candidate.",
        "warnings": ["No acquisition provider supports this candidate."],
    }


def normalize_acquisition_result(result, candidate):
    """Normalize provider output into canonical acquisition shape."""
    normalized_candidate = _normalize_candidate(candidate)
    if not isinstance(result, dict):
        result = {}

    warnings = result.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = [str(warnings)]

    source_content = str(result.get("source_content", ""))
    source_hash = hashlib.sha256(source_content.encode("utf-8")).hexdigest() if source_content else ""

    return {
        "title": str(result.get("title", normalized_candidate["title"]))[:500].strip(),
        "source": str(result.get("source", normalized_candidate["source"]))[:200].strip(),
        "document_type": str(result.get("document_type", normalized_candidate["document_type"]))[:120].strip(),
        "publication_date": str(result.get("publication_date", normalized_candidate["publication_date"]))[:32].strip(),
        "reference_url": str(result.get("reference_url", normalized_candidate["reference_url"]))[:2000].strip(),
        "reference_id": str(result.get("reference_id", normalized_candidate["reference_id"]))[:200].strip(),
        "provider_name": str(result.get("provider_name", "Unknown Acquisition Provider")).strip(),
        "discovery_provider": str(result.get("discovery_provider", normalized_candidate["discovery_provider"]))[:200].strip(),
        "discovery_source": str(result.get("discovery_source", normalized_candidate["discovery_source"]))[:200].strip(),
        "original_candidate_identifier": str(
            result.get("original_candidate_identifier", normalized_candidate["original_candidate_identifier"])
        )[:300].strip(),
        "acquisition_status": str(result.get("acquisition_status", ACQUISITION_STATUS_UNAVAILABLE)).strip(),
        "retrieval_timestamp": str(result.get("retrieval_timestamp", datetime.now().isoformat())).strip(),
        "source_reference": str(result.get("source_reference", normalized_candidate["reference_url"]))[:2000].strip(),
        "content_type": str(result.get("content_type", "")).strip(),
        "source_content": source_content,
        "source_content_hash": source_hash,
        "acquisition_error": str(result.get("acquisition_error", "")).strip(),
        "warnings": [str(item).strip() for item in warnings if str(item).strip()],
        "acquired_source_material": True,
    }


def report_acquisition_status(acquired_documents):
    """Compute aggregate acquisition status and warnings from normalized documents."""
    if not acquired_documents:
        return {
            "acquisition_status": ACQUISITION_STATUS_NOT_ATTEMPTED,
            "acquired_document_count": 0,
            "acquisition_warnings": [],
        }

    warnings = []
    statuses = []
    acquired_count = 0
    for document in acquired_documents:
        status = str(document.get("acquisition_status", ACQUISITION_STATUS_UNAVAILABLE)).strip()
        statuses.append(status)
        if status == ACQUISITION_STATUS_ACQUIRED:
            acquired_count += 1
        warnings.extend([str(item).strip() for item in document.get("warnings", []) if str(item).strip()])

    if acquired_count > 0:
        aggregate_status = ACQUISITION_STATUS_ACQUIRED
    elif any(status == ACQUISITION_STATUS_FAILED for status in statuses):
        aggregate_status = ACQUISITION_STATUS_FAILED
    elif statuses:
        aggregate_status = ACQUISITION_STATUS_UNAVAILABLE
    else:
        aggregate_status = ACQUISITION_STATUS_NOT_ATTEMPTED

    return {
        "acquisition_status": aggregate_status,
        "acquired_document_count": acquired_count,
        "acquisition_warnings": warnings,
    }


def acquire_supported_candidates(candidate_documents, providers=None):
    """Acquire source material for discovered candidates without performing independent search."""
    normalized_candidates = candidate_documents if isinstance(candidate_documents, list) else []
    acquired_documents = [acquire_candidate(candidate, providers=providers) for candidate in normalized_candidates]
    status = report_acquisition_status(acquired_documents)
    return {
        "acquisition_status": status["acquisition_status"],
        "acquired_document_count": status["acquired_document_count"],
        "acquired_documents": acquired_documents,
        "acquisition_warnings": status["acquisition_warnings"],
    }


def _normalize_candidate(candidate):
    if not isinstance(candidate, dict):
        candidate = {}

    discovery_provider = str(candidate.get("provider_name", "")).strip() or "Unknown Discovery Provider"
    reference_id = str(candidate.get("reference_id", "")).strip()
    reference_url = str(candidate.get("reference_url", "")).strip()
    title = str(candidate.get("title", "")).strip()

    original_identifier = reference_id or reference_url or title

    return {
        "title": title,
        "source": str(candidate.get("source", "")).strip(),
        "document_type": str(candidate.get("document_type", "")).strip(),
        "publication_date": str(candidate.get("publication_date", "")).strip(),
        "reference_url": reference_url,
        "reference_id": reference_id,
        "discovery_provider": discovery_provider,
        "discovery_source": str(candidate.get("source", "")).strip(),
        "original_candidate_identifier": original_identifier,
    }
