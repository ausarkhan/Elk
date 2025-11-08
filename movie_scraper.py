"""Minimal MovieScraper scaffold used by Designer+Lead.

This module provides a MovieScraper class with a small, testable contract:
- fetch(url) -> ParsedPage
- scrape(year) -> List[Movie]

Design decisions (explicit):
- parser callable accepts HTML (str) and returns List[dict] with keys 'title','rating','plot'.
- Items missing a title or with an unparsable rating are skipped (not raised).
- Duplicate movies (by title) are deduplicated, keeping first occurrence.
- If a dataset_manager is provided, its save_movies(movies, filename) is called.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
import logging

from movie import Movie


class ScrapeError(Exception):
    pass


class ParseError(Exception):
    pass


@dataclass
class ParsedPage:
    html: str
    metadata: Dict = None

    def extract_items(self, parser: Callable[[str], List[Dict]]) -> List[Dict]:
        return parser(self.html)


class MovieScraper:
    def __init__(self, https_client, parser: Callable[[str], List[Dict]], dataset_manager=None, base_url: str = "https://example.com") -> None:
        self.https_client = https_client
        self.parser = parser
        self.dataset_manager = dataset_manager
        self.base_url = base_url.rstrip('/')

    def fetch(self, url: str) -> ParsedPage:
        try:
            resp = self.https_client.get_with_retries(url)
        except Exception as e:
            logging.error("Network error while fetching %s: %s", url, e)
            raise

        status = getattr(resp, 'status_code', None)
        if status is not None and status != 200:
            raise ScrapeError(f"Non-200 status: {status}")

        html = getattr(resp, 'text', '')
        return ParsedPage(html=html, metadata={'url': url, 'status_code': status})

    def scrape(self, year: int) -> List[Movie]:
        url = f"{self.base_url.rstrip('/')}/{year}"
        parsed = self.fetch(url)

        try:
            items = parsed.extract_items(self.parser)
        except Exception as e:
            logging.exception("Parser error for %s", url)
            raise ParseError(e)

        movies: List[Movie] = []
        seen_titles = set()
        for it in items:
            title = (it.get('title') or '').strip() if isinstance(it.get('title'), str) else None
            if not title:
                # skip items without a title
                continue
            if title in seen_titles:
                continue
            rating = it.get('rating')
            try:
                rating_val = float(rating) if rating is not None else None
            except Exception:
                # skip items with invalid rating
                continue
            plot = it.get('plot') or ''
            m = Movie(title, rating_val, plot)
            movies.append(m)
            seen_titles.add(title)

        if self.dataset_manager and hasattr(self.dataset_manager, 'save_movies'):
            filename = f"movies_{year}.json"
            try:
                self.dataset_manager.save_movies(movies, filename)
            except Exception:
                logging.exception("Failed to save movies to dataset manager")

        return movies
