"""Course logos from the Google favicon service, cached on disk so they work offline later."""
import urllib.request
from urllib.parse import urlparse

from .. import config

CACHE = config.DATA_DIR / "favicons"


def domain_of(url):
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    return urlparse(url).netloc.lower()


def cached(url):
    d = domain_of(url)
    p = CACHE / f"{d}.png"
    return p if d and p.exists() else None


def fetch(url):
    """Blocking. Returns a Path or None. Call from a worker thread."""
    d = domain_of(url)
    if not d:
        return None
    if (hit := cached(url)):
        return hit
    try:
        with urllib.request.urlopen(f"https://www.google.com/s2/favicons?domain={d}&sz=64", timeout=5) as r:
            data = r.read()
        CACHE.mkdir(parents=True, exist_ok=True)
        path = CACHE / f"{d}.png"
        path.write_bytes(data)
        return path
    except OSError:
        return None
