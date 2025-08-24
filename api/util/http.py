# api/util/http.py
import os
try:
    from curl_cffi import requests as crequests
    _HAS_CURL_CFFI = True
except Exception:
    import requests as crequests  # type: ignore
    _HAS_CURL_CFFI = False

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

_IMPERSONATE = os.getenv("YF_IMPERSONATE", "0").lower() in ("1", "true", "yes")

_session = None

def reset_session():
    """Reset the global session (useful when env vars change)"""
    global _session
    _session = None

def get_session():
    global _session
    if _session is not None:
        return _session

    if _HAS_CURL_CFFI and _IMPERSONATE:
        s = crequests.Session(impersonate=os.getenv("YF_IMPERSONATE_PROFILE", "chrome"))
    else:
        s = crequests.Session()
        retries = Retry(
            total=3, backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"], raise_on_status=False,
        )
        s.mount("https://", HTTPAdapter(max_retries=retries))

    s.headers.update({
        "User-Agent": os.getenv(
            "YF_UA",
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/124.0.0.0 Safari/537.36")
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    _session = s
    return _session
