import re
from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup

from app.services.skill_extractor import extract_skills


REKRUTE_BASE_URL = "https://www.rekrute.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.rekrute.com/",
}

CATEGORIES = {
    "all": {"code": "1", "label": "Cadres / Tous secteurs"},
    "it": {"code": "3", "label": "Métiers IT"},
    "commercial": {"code": "4", "label": "Commercial & Marketing"},
    "finance": {"code": "5", "label": "Finance & Comptabilité"},
    "hr": {"code": "6", "label": "RH & Formation"},
    "technique": {"code": "7", "label": "Métiers Techniques"},
    "ingenierie": {"code": "8", "label": "Ingénierie"},
}


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""

    value = unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def build_rekrute_url(category_code: str, page: int = 1, query: Optional[str] = None) -> str:
    """
    Uses the same URL format as the working teammate scraper:
    /offres.html?s=3&p=1&o=1&query=python
    """
    url = f"{REKRUTE_BASE_URL}/offres.html?s={category_code}&p={page}&o=1"

    if query:
        url += f"&query={quote(query.strip())}"

    return url


def _parse_listing(item, source: str = "rekrute") -> Optional[Dict[str, Any]]:
    try:
        title_tag = item.select_one("h2 a.titreJob")

        if not title_tag:
            return None

        raw_title = clean_text(title_tag.get_text(" ", strip=True))

        if "|" in raw_title:
            title, location = [part.strip() for part in raw_title.split("|", 1)]
        else:
            title = raw_title
            location = "Maroc"

        href = title_tag.get("href", "")
        job_url = urljoin(REKRUTE_BASE_URL, href)

        company = ""
        company_img = item.select_one("img.photo")

        if company_img:
            company = clean_text(company_img.get("alt", ""))

        if not company:
            company = "Rekrute"

        desc_tag = item.select_one("div.info span")
        description = clean_text(desc_tag.get_text(" ", strip=True)) if desc_tag else ""

        full_text = f"{title}\n{company}\n{description}"
        skills = extract_skills(full_text)

        return {
            "title": title[:180],
            "company": company[:180],
            "description": description[:3000],
            "location": location,
            "required_skills": skills,
            "url": job_url,
            "source": source,
        }

    except Exception as exc:
        print(f"[ScrapingAgent] Parse error: {exc}")
        return None


def _scrape_rekrute_category(
    category_code: str,
    label: str,
    query: Optional[str] = None,
    max_pages: int = 1,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    jobs = []

    session = requests.Session()
    session.headers.update(HEADERS)

    # Try homepage first to obtain cookies/session context.
    try:
        session.get(REKRUTE_BASE_URL, timeout=15)
    except Exception as exc:
        print(f"[ScrapingAgent] Homepage prefetch failed: {exc}")

    for page in range(1, max_pages + 1):
        if len(jobs) >= limit:
            break

        url = build_rekrute_url(category_code=category_code, page=page, query=query)

        try:
            response = session.get(url, timeout=15)

            if response.status_code == 403:
                return [
                    {
                        "_blocked": True,
                        "_url": url,
                        "_error": "Rekrute returned HTTP 403",
                    }
                ]

            response.raise_for_status()

        except requests.RequestException as exc:
            print(f"[ScrapingAgent][{label}] Page {page} error: {exc}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.select("li.post-id")

        if not listings:
            print(f"[ScrapingAgent][{label}] No listings found on page {page}")
            break

        for item in listings:
            if len(jobs) >= limit:
                break

            job = _parse_listing(item, source="rekrute")

            if job:
                jobs.append(job)

    return jobs


def scrape_rekrute_jobs(
    category: str = "it",
    query: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Scrapes public Rekrute listings using the teammate's working URL pattern.
    """
    category_data = CATEGORIES.get(category, CATEGORIES["it"])
    category_code = category_data["code"]
    category_label = category_data["label"]

    jobs = _scrape_rekrute_category(
        category_code=category_code,
        label=category_label,
        query=query,
        max_pages=3,
        limit=limit,
    )

    if jobs and jobs[0].get("_blocked"):
        return {
            "source": "rekrute",
            "url": jobs[0].get("_url"),
            "status": "failed",
            "error": jobs[0].get("_error"),
            "category": category,
            "query": query,
            "count": 0,
            "jobs": [],
        }

    # Deduplicate by URL.
    seen = set()
    unique_jobs = []

    for job in jobs:
        url = job.get("url")

        if url and url in seen:
            continue

        unique_jobs.append(job)

        if url:
            seen.add(url)

    example_url = build_rekrute_url(category_code=category_code, page=1, query=query)

    return {
        "source": "rekrute",
        "url": example_url,
        "status": "success",
        "category": category,
        "query": query,
        "count": len(unique_jobs),
        "jobs": unique_jobs,
    }