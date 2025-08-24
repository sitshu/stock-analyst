import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class TransientHTTPError(Exception):
    pass

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(TransientHTTPError),
)
async def fetch_json(url: str, timeout: float = 10.0):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code >= 500:
                raise TransientHTTPError(f"Server error {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as e:
            raise TransientHTTPError(str(e))
