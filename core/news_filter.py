from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

import requests

from config import Config

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NewsItem:
    title: str
    link: str
    published_at: datetime


class NewsRiskEngine:
    """Fetch and cache RSS headlines, then flag short-term news risk by symbol."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._last_refresh: datetime | None = None
        self._items: list[NewsItem] = []

    def _needs_refresh(self, now: datetime) -> bool:
        if self._last_refresh is None:
            return True
        age = (now - self._last_refresh).total_seconds()
        return age >= float(self.config.news_refresh_seconds)

    @staticmethod
    def _parse_pub_date(raw: str | None, fallback: datetime) -> datetime:
        if not raw:
            return fallback
        try:
            parsed = parsedate_to_datetime(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return fallback

    def _fetch_source(self, url: str, now: datetime) -> list[NewsItem]:
        headers = {"User-Agent": "pytrade-news/1.0"}
        resp = requests.get(url, timeout=self.config.news_fetch_timeout_seconds, headers=headers)
        resp.raise_for_status()

        root = ElementTree.fromstring(resp.content)
        out: list[NewsItem] = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = self._parse_pub_date(item.findtext("pubDate"), now)
            if not title:
                continue
            out.append(NewsItem(title=title, link=link, published_at=pub))
        return out

    def refresh(self) -> tuple[bool, str]:
        now = datetime.now(timezone.utc)
        if not self.config.enable_news_filter:
            return True, "news_filter_disabled"
        if not self._needs_refresh(now):
            return True, "cache_fresh"

        items: list[NewsItem] = []
        errors: list[str] = []
        for url in self.config.news_sources:
            try:
                items.extend(self._fetch_source(url, now))
            except Exception as exc:
                errors.append(f"{url}: {exc}")

        if items:
            dedup: dict[str, NewsItem] = {}
            for it in items:
                key = f"{it.title}|{it.link}"
                if key not in dedup:
                    dedup[key] = it
            self._items = sorted(dedup.values(), key=lambda x: x.published_at, reverse=True)
            self._last_refresh = now
            if errors:
                logger.warning("News refresh partial errors: %s", " | ".join(errors))
            return True, "refreshed"

        if errors:
            logger.warning("News refresh failed: %s", " | ".join(errors))
        if self.config.news_fail_open:
            self._last_refresh = now
            return False, "news_unavailable_fail_open"
        return False, "news_unavailable_fail_closed"

    @staticmethod
    def _symbol_keywords(symbol: str) -> list[str]:
        key = "".join(ch for ch in symbol.upper() if ch.isalnum())
        keywords = [key.lower()]
        if key.startswith("XAUUSD"):
            keywords.extend(["gold", "xau", "bullion", "comex"])
        if key.endswith("USD") or key.startswith("USD"):
            keywords.extend(["usd", "dollar", "treasury", "yield"])
        return keywords

    def analyze_symbol(self, symbol: str) -> dict[str, Any]:
        ok, refresh_reason = self.refresh()
        now = datetime.now(timezone.utc)
        if not self.config.enable_news_filter:
            return {"enabled": False, "blocked": False, "reason": "news_filter_disabled", "matched": []}

        if not ok and refresh_reason == "news_unavailable_fail_closed":
            return {
                "enabled": True,
                "blocked": True,
                "reason": "news_feed_unavailable",
                "matched": [],
            }

        lookback = timedelta(minutes=float(self.config.news_lookback_minutes))
        block_window = timedelta(minutes=float(self.config.news_block_minutes))
        base_keywords = set(self.config.news_keywords)
        symbol_keywords = set(self._symbol_keywords(symbol))
        all_keywords = base_keywords | symbol_keywords

        matched: list[dict[str, Any]] = []
        high_impact_count = 0
        impact_terms = {"fed", "fomc", "cpi", "ppi", "nfp", "rate", "yield", "war", "sanction", "tariff"}

        for item in self._items:
            age = now - item.published_at
            if age < timedelta(0) or age > lookback:
                continue
            title_l = item.title.lower()
            if not any(k in title_l for k in all_keywords):
                continue

            matched_item = {
                "title": item.title,
                "link": item.link,
                "age_minutes": round(age.total_seconds() / 60.0, 1),
            }
            matched.append(matched_item)

            if any(t in title_l for t in impact_terms) and age <= block_window:
                high_impact_count += 1

        blocked = high_impact_count > 0
        reason = "ok"
        if blocked:
            reason = f"news_blocked_high_impact={high_impact_count}"
        elif not matched:
            reason = refresh_reason

        return {
            "enabled": True,
            "blocked": blocked,
            "reason": reason,
            "matched": matched[:3],
            "matched_count": len(matched),
            "high_impact_count": high_impact_count,
        }
