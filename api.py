from __future__ import annotations
import logging, re
from typing import Optional, Tuple, Dict
from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup
from .const import BASE_URL, LOGIN_URL, DASHBOARD_CANDIDATES
_LOGGER = logging.getLogger(__name__)
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0 Safari/537.36")

def _clean_number(txt: str) -> Optional[int]:
    if not txt: return None
    digits = re.sub(r"[^\d]", "", txt)
    try: return int(digits) if digits else None
    except: return None

def _sanitize_for_log(html: str) -> str:
    return re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted@mail]", html)

def _find_value_before_label(soup: BeautifulSoup, label_regex: str) -> Optional[int]:
    label = soup.find(string=re.compile(label_regex, re.I))
    if not label: return None
    prev = label.find_previous(string=re.compile(r"^[\d\.,]+$"))
    if prev: return _clean_number(prev)
    if getattr(label, 'parent', None):
        return _clean_number(label.parent.get_text(" ", strip=True))
    return None

def _parse_stats_from_html(html: str) -> Tuple[Optional[int], Optional[int]]:
    soup = BeautifulSoup(html, "html.parser")
    lifetime = _find_value_before_label(soup, r"Lifetime\s*Meters")
    season = _find_value_before_label(soup, r"Season\s*Meters")
    if lifetime is None:
        m = re.search(r"([\d\.,]+)\s*Lifetime\s*Meters", html, re.I)
        if m: lifetime = _clean_number(m.group(1))
    if season is None:
        m = re.search(r"([\d\.,]+)\s*Season\s*Meters", html, re.I)
        if m: season = _clean_number(m.group(1))
    return lifetime, season

class Concept2Client:
    def __init__(self, session: ClientSession, username: str, password: str):
        self._session=session; self._username=username; self._password=password; self._logged_in=False
    async def _get_csrf(self) -> Optional[str]:
        try:
            _LOGGER.debug("Concept2: loginpagina openen voor CSRF-token")
            async with self._session.get(LOGIN_URL, headers={"User-Agent": USER_AGENT}, allow_redirects=True) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Concept2: CSRF-pagina gaf status %s", resp.status); return None
                html=await resp.text()
        except Exception as exc:
            _LOGGER.warning("Concept2: fout bij ophalen loginpagina: %s", exc); return None
        soup=BeautifulSoup(html,"html.parser")
        token_input=soup.select_one('input[name="_token"]')
        if token_input and token_input.get("value"): return token_input["value"]
        meta=soup.select_one('meta[name="csrf-token"]')
        if meta and meta.get("content"): return meta["content"]
        _LOGGER.warning("Concept2: CSRF-token niet gevonden op loginpagina"); return None
    async def login(self)->bool:
        token=await self._get_csrf()
        if not token:
            _LOGGER.warning("Concept2: login overgeslagen (geen CSRF-token)"); return False
        payload={"_token":token,"username":self._username,"password":self._password}
        headers={"User-Agent":USER_AGENT,"Origin":BASE_URL,"Referer":LOGIN_URL}
        try:
            _LOGGER.debug("Concept2: inloggen met POST")
            async with self._session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True) as resp:
                if resp.status not in (200,302):
                    _LOGGER.warning("Concept2: login mislukte: HTTP %s", resp.status); return False
        except Exception as exc:
            _LOGGER.warning("Concept2: login call exception: %s", exc); return False
        self._logged_in=True; return True
    async def _ensure_login(self)->None:
        if not self._logged_in: await self.login()
    async def fetch_stats(self) -> Dict[str, Optional[int]]:
        await self._ensure_login()
        last_error=None
        for url in DASHBOARD_CANDIDATES:
            try:
                _LOGGER.debug("Concept2: dashboardpagina ophalen: %s", url)
                async with self._session.get(url, headers={"User-Agent":USER_AGENT,"Referer":LOGIN_URL}, allow_redirects=True) as resp:
                    if resp.status in (401,403):
                        _LOGGER.debug("Concept2: %s -> opnieuw inloggen en herproberen", resp.status)
                        self._logged_in=False; await self.login(); continue
                    if resp.status != 200:
                        last_error=f"HTTP {resp.status} op {url}"; _LOGGER.debug("Concept2: %s", last_error); continue
                    html=await resp.text()
                lifetime, season = _parse_stats_from_html(html)
                if lifetime is not None or season is not None:
                    _LOGGER.debug("Concept2: Stats gevonden: lifetime=%s, season=%s", lifetime, season)
                    return {"lifetime": lifetime, "season": season}
                _LOGGER.debug("Concept2: parsing mislukt op %s, snippet: %s", url, _sanitize_for_log((html or "")[:800]))
                last_error = "Parser vond geen meters"
            except ClientResponseError as cre:
                last_error=f"HTTP error {cre.status} op {url}"; _LOGGER.debug("Concept2: %s", last_error)
            except Exception as exc:
                last_error=f"Fout op {url}: {exc}"; _LOGGER.debug("Concept2: %s", last_error)
        _LOGGER.warning("Concept2: meterstats niet gevonden (%s). Site down of markup gewijzigd?", last_error or "geen details")
        return {"lifetime": None, "season": None}
