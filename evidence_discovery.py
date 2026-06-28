import json
import os
from datetime import date, datetime
from urllib import error as url_error
from urllib import request as url_request


DISCOVERY_STATUS_DISCOVERED = "discovered"
DISCOVERY_STATUS_UNAVAILABLE = "unavailable"
DISCOVERY_STATUS_FAILED = "failed"
DISCOVERY_STATUS_NOT_ATTEMPTED = "not_attempted"


def normalize_candidate(candidate, provider_name):
    """Normalize a provider candidate into the canonical discovery shape."""
    warnings = candidate.get("warnings", []) if isinstance(candidate, dict) else []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]

    normalized = {
        "title": str(candidate.get("title", "")).strip() if isinstance(candidate, dict) else "",
        "source": str(candidate.get("source", "")).strip() if isinstance(candidate, dict) else "",
        "document_type": str(candidate.get("document_type", "")).strip() if isinstance(candidate, dict) else "",
        "publication_date": str(candidate.get("publication_date", "")).strip() if isinstance(candidate, dict) else "",
        "reference_url": str(candidate.get("reference_url", "")).strip() if isinstance(candidate, dict) else "",
        "reference_id": str(candidate.get("reference_id", "")).strip() if isinstance(candidate, dict) else "",
        "discovery_status": str(candidate.get("discovery_status", "candidate")).strip() if isinstance(candidate, dict) else "candidate",
        "provider_name": provider_name,
        "warnings": [str(item).strip() for item in warnings if str(item).strip()],
        "candidate_evidence": True,
    }
    return normalized


def aggregate_discovery_results(provider_results):
    """Aggregate provider outputs into one canonical discovery payload."""
    candidates = []
    warnings = []
    statuses = []

    for result in provider_results:
        if not isinstance(result, dict):
            continue
        statuses.append(str(result.get("status", DISCOVERY_STATUS_UNAVAILABLE)).strip())
        warnings.extend([str(item).strip() for item in result.get("warnings", []) if str(item).strip()])

        provider_name = str(result.get("provider_name", "Unknown Provider")).strip()
        for raw_candidate in result.get("candidates", []):
            candidates.append(normalize_candidate(raw_candidate, provider_name))

    deduped_candidates = []
    seen = set()
    for candidate in candidates:
        key = (
            candidate.get("provider_name", ""),
            candidate.get("reference_id", ""),
            candidate.get("title", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped_candidates.append(candidate)

    if deduped_candidates:
        aggregate_status = DISCOVERY_STATUS_DISCOVERED
    elif any(status == DISCOVERY_STATUS_FAILED for status in statuses):
        aggregate_status = DISCOVERY_STATUS_FAILED
    elif statuses:
        aggregate_status = DISCOVERY_STATUS_UNAVAILABLE
    else:
        aggregate_status = DISCOVERY_STATUS_NOT_ATTEMPTED

    return {
        "evidence_discovery_status": aggregate_status,
        "candidate_count": len(deduped_candidates),
        "candidate_documents": deduped_candidates,
        "discovery_warnings": warnings,
        "provider_results": provider_results,
    }


class SecEdgarDiscoveryProvider:
    """Discover candidate SEC filings for a ticker using EDGAR metadata endpoints."""

    provider_name = "SEC EDGAR"
    _ticker_map_cache = None

    def __init__(self, user_agent=None, timeout_seconds=6):
        self.user_agent = user_agent or _resolve_sec_user_agent()
        self.timeout_seconds = int(timeout_seconds)
        self.last_fetch_error = ""

    def discover(self, ticker, observation_date):
        normalized_ticker = str(ticker).strip().upper()
        if not normalized_ticker:
            return {
                "provider_name": self.provider_name,
                "status": DISCOVERY_STATUS_UNAVAILABLE,
                "candidates": [],
                "warnings": ["Ticker is required for SEC discovery."],
            }

        cik = self._lookup_cik(normalized_ticker)
        if not cik:
            if self.last_fetch_error:
                return {
                    "provider_name": self.provider_name,
                    "status": DISCOVERY_STATUS_UNAVAILABLE,
                    "candidates": [],
                    "warnings": [
                        f"SEC ticker mapping request failed: {self.last_fetch_error}. Configure SEC_USER_AGENT with contact details.",
                    ],
                }
            return {
                "provider_name": self.provider_name,
                "status": DISCOVERY_STATUS_UNAVAILABLE,
                "candidates": [],
                "warnings": [f"SEC ticker mapping unavailable for '{normalized_ticker}'."],
            }

        filings = self._fetch_recent_filings(cik)
        if filings is None:
            warning = "SEC submissions endpoint unavailable during preparation."
            if self.last_fetch_error:
                warning = f"SEC submissions request failed: {self.last_fetch_error}."
            return {
                "provider_name": self.provider_name,
                "status": DISCOVERY_STATUS_UNAVAILABLE,
                "candidates": [],
                "warnings": [warning],
            }

        cutoff = _normalize_observation_date(observation_date)
        allowed_forms = {"10-K", "10-Q", "8-K", "20-F", "6-K"}
        candidates = []
        for filing in filings:
            form = str(filing.get("form", "")).strip().upper()
            filing_date = str(filing.get("filing_date", "")).strip()
            if form not in allowed_forms:
                continue
            if cutoff and filing_date and filing_date > cutoff:
                continue

            accession = str(filing.get("accession", "")).strip()
            primary_document = str(filing.get("primary_document", "")).strip()
            reference_url = self._build_archive_url(cik, accession, primary_document)
            candidates.append(
                {
                    "title": f"{normalized_ticker} {form} filing",
                    "source": self.provider_name,
                    "document_type": form,
                    "publication_date": filing_date,
                    "reference_url": reference_url,
                    "reference_id": accession,
                    "discovery_status": "candidate",
                    "warnings": [],
                }
            )

        return {
            "provider_name": self.provider_name,
            "status": DISCOVERY_STATUS_DISCOVERED if candidates else DISCOVERY_STATUS_UNAVAILABLE,
            "candidates": candidates[:8],
            "warnings": [] if candidates else ["No qualifying filings found on or before the observation date."],
        }

    def _lookup_cik(self, ticker):
        ticker_map = self._get_ticker_map()
        if ticker_map is None:
            return None
        return ticker_map.get(ticker)

    def _get_ticker_map(self):
        if SecEdgarDiscoveryProvider._ticker_map_cache is not None:
            return SecEdgarDiscoveryProvider._ticker_map_cache

        payload = self._fetch_json("https://www.sec.gov/files/company_tickers.json")
        if not isinstance(payload, dict):
            return None

        ticker_map = {}
        for _, value in payload.items():
            if not isinstance(value, dict):
                continue
            ticker_value = str(value.get("ticker", "")).strip().upper()
            cik_raw = value.get("cik_str")
            if not ticker_value or cik_raw is None:
                continue
            try:
                cik_value = str(int(cik_raw)).zfill(10)
            except (TypeError, ValueError):
                continue
            ticker_map[ticker_value] = cik_value

        SecEdgarDiscoveryProvider._ticker_map_cache = ticker_map
        return ticker_map

    def _fetch_recent_filings(self, cik):
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        payload = self._fetch_json(submissions_url)
        if not isinstance(payload, dict):
            return None

        filings = payload.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accession_numbers = filings.get("accessionNumber", [])
        filing_dates = filings.get("filingDate", [])
        primary_documents = filings.get("primaryDocument", [])

        count = min(len(forms), len(accession_numbers), len(filing_dates), len(primary_documents))
        rows = []
        for idx in range(count):
            rows.append(
                {
                    "form": forms[idx],
                    "accession": accession_numbers[idx],
                    "filing_date": filing_dates[idx],
                    "primary_document": primary_documents[idx],
                }
            )
        return rows

    def _build_archive_url(self, cik, accession, primary_document):
        if not accession or not primary_document:
            return ""
        cik_numeric = str(int(cik)) if str(cik).strip().isdigit() else str(cik).strip()
        accession_compact = str(accession).replace("-", "").strip()
        if not cik_numeric or not accession_compact:
            return ""
        return f"https://www.sec.gov/Archives/edgar/data/{cik_numeric}/{accession_compact}/{primary_document}"

    def _fetch_json(self, url):
        request = url_request.Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        try:
            with url_request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
            self.last_fetch_error = ""
            return json.loads(payload)
        except url_error.HTTPError as exc:
            self.last_fetch_error = f"HTTPError {exc.code}"
            return None
        except (url_error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.last_fetch_error = f"{type(exc).__name__}: {str(exc)}"
            return None


def _resolve_sec_user_agent():
    configured = str(os.getenv("SEC_USER_AGENT", "")).strip()
    if configured:
        return configured
    return "Athena Operational Validation Contact ops@athena.local"


def discover_candidate_documents(ticker, observation_date, providers=None):
    """Discover candidate evidence metadata through one or more providers."""
    provider_chain = providers if providers is not None else [SecEdgarDiscoveryProvider()]

    provider_results = []
    for provider in provider_chain:
        provider_name = getattr(provider, "provider_name", provider.__class__.__name__)
        try:
            result = provider.discover(ticker=ticker, observation_date=observation_date)
        except Exception as exc:
            result = {
                "provider_name": provider_name,
                "status": DISCOVERY_STATUS_FAILED,
                "candidates": [],
                "warnings": [f"Provider failure: {type(exc).__name__}: {str(exc)}"],
            }

        if not isinstance(result, dict):
            result = {
                "provider_name": provider_name,
                "status": DISCOVERY_STATUS_FAILED,
                "candidates": [],
                "warnings": ["Provider returned invalid discovery payload."],
            }

        result.setdefault("provider_name", provider_name)
        result.setdefault("status", DISCOVERY_STATUS_UNAVAILABLE)
        result.setdefault("candidates", [])
        result.setdefault("warnings", [])
        provider_results.append(result)

    return aggregate_discovery_results(provider_results)


def _normalize_observation_date(observation_date):
    if isinstance(observation_date, datetime):
        return observation_date.date().isoformat()
    if isinstance(observation_date, date):
        return observation_date.isoformat()
    if observation_date is None:
        return ""

    raw_value = str(observation_date).strip()
    if not raw_value:
        return ""
    try:
        return datetime.fromisoformat(raw_value).date().isoformat()
    except ValueError:
        return ""
