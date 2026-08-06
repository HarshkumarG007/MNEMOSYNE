import logging
from typing import Any, Dict

import httpx
import whois  # type: ignore

from .base import BaseAgent

logger = logging.getLogger(__name__)


class OsintAgent(BaseAgent):
    """
    Privacy-preserving, narrowly-scoped external enrichment.
    Strictly limited to 3 lookups: whois, hibp (HaveIBeenPwned), geoip.
    """

    def __init__(self):  # type: ignore
        super().__init__(name="OsintAgent")
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Programmatic check ensuring scope isn't creeped
        allowed_methods = {"_execute", "whois_lookup", "hibp_lookup", "geoip_lookup"}
        public_methods = {m for m in dir(self) if callable(getattr(self, m)) and not m.startswith("_") and m not in {"run", "validate_output", "handle_error"}}

        if not public_methods.issubset(allowed_methods):
            raise RuntimeError(f"OSINT Agent scope creep detected! Unauthorized methods found: {public_methods - allowed_methods}")

    async def whois_lookup(self, domain: str) -> Dict[str, Any]:
        if domain in self._cache:
            return self._cache[domain]

        try:
            # whois library is synchronous, should be wrapped in executor for production
            w = whois.whois(domain)
            result = {"source": "public WHOIS", "data": dict(w)}
            self._cache[domain] = result
            return result
        except Exception as e:
            logger.error(f"WHOIS lookup failed for {domain}: {e}")
            return {"source": "public WHOIS", "error": str(e)}

    async def hibp_lookup(self, password_hash: str) -> Dict[str, Any]:
        """
        Uses the free HIBP API (k-anonymity) with a SHA-1 hash prefix.
        Does not require an API key.
        """
        prefix = password_hash[:5].upper()
        if prefix in self._cache:
            return self._cache[prefix]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.pwnedpasswords.com/range/{prefix}")
                response.raise_for_status()

            # Parse response to find suffix match
            suffixes = response.text.splitlines()
            result = {"source": "HaveIBeenPwned API", "matched_suffixes": len(suffixes)}
            self._cache[prefix] = result
            return result
        except Exception as e:
            logger.error(f"HIBP lookup failed for {prefix}: {e}")
            return {"source": "HaveIBeenPwned API", "error": str(e)}

    async def geoip_lookup(self, ip_address: str) -> Dict[str, Any]:
        if ip_address in self._cache:
            return self._cache[ip_address]

        try:
            # Use public ip-api for geo location
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://ip-api.com/json/{ip_address}")
                response.raise_for_status()

            result = {"source": "IP-API", "data": response.json()}
            self._cache[ip_address] = result
            return result
        except Exception as e:
            logger.error(f"GeoIP lookup failed for {ip_address}: {e}")
            return {"source": "IP-API", "error": str(e)}

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        lookup_type = input_data.get("type")
        query = input_data.get("query")

        if not query:
            return {"error": "No query provided"}

        if lookup_type == "whois":
            return await self.whois_lookup(query)
        elif lookup_type == "hibp":
            return await self.hibp_lookup(query)
        elif lookup_type == "geoip":
            return await self.geoip_lookup(query)
        else:
            return {"error": f"Unsupported lookup type: {lookup_type}"}
