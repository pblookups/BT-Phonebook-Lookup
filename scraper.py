#!/usr/bin/env python3
"""
scraper.py (URL discovery only; no downloads)

Discovers BT Phonebook PDF URLs by crawling from a seed page and returning
a de-duplicated list of absolute .pdf links within bt.com.
"""

import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Default seed: BT A–Z directory finder (listing page for the PDFs)
DEFAULT_SEED = "https://www.bt.com/help/the-phone-book/a-z-directory-finder"

# Only allow crawling within these domains (avoid drifting)
ALLOWED_DOMAINS = {"www.bt.com", "bt.com"}

# Polite headers
HEADERS = {"User-Agent": "BT-Phonebook-Lookup/1.0 (+https://github.com/your/repo)"}

# Follow only pages that look like they may list directories / downloads
FOLLOW_RE = re.compile(r"/(page|directory|area|region|a-z|list|downloads?)/", re.I)


def discover_pdf_urls(seed_urls, domain_whitelist=None, max_pages=500, timeout=20):
    """
    Crawl from seed_urls, collecting absolute .pdf links within allowed domains.
    Returns a sorted list of unique URLs.
    """
    seen_pages, pdf_urls, to_visit = set(), set(), list(seed_urls)
    domain_whitelist = set(domain_whitelist or ALLOWED_DOMAINS)

    while to_visit and len(seen_pages) < max_pages:
        url = to_visit.pop()
        if url in seen_pages:
            continue
        seen_pages.add(url)

        try:
            resp = requests.get(url, timeout=timeout, headers=HEADERS)
            resp.raise_for_status()
        except Exception:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = (a["href"] or "").strip()
            if not href:
                continue

            abs_url = urljoin(url, href)
            host = urlparse(abs_url).netloc

            # Keep to the allowed domain(s)
            if host not in domain_whitelist:
                continue

            # Collect PDFs
            if abs_url.lower().endswith(".pdf"):
                pdf_urls.add(abs_url)
                continue

            # Optionally follow likely navigation pages to find more PDFs
            if FOLLOW_RE.search(abs_url) and abs_url not in seen_pages:
                to_visit.append(abs_url)

    return sorted(pdf_urls)


if __name__ == "__main__":
    seeds = [DEFAULT_SEED]
    urls = discover_pdf_urls(seeds, domain_whitelist=ALLOWED_DOMAINS)
    print(f"Found {len(urls)} PDFs")
    for u in urls:
        print(u)
