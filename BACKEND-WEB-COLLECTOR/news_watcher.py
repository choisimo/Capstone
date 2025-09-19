from __future__ import annotations
"""
news_watcher.py

Watches Naver/Daum news search results for a configured keyword (default: '국민연금').
When a new article is detected, publishes a seed event ('seed.news.v1') and expands the
seed by collecting related content from YouTube (via API if configured) and the web
(via Perplexity if configured) and publishes those as 'raw.posts.v1'. Optionally creates
ChangeDetection.io watches for discovered URLs.

ENV configuration:
- NEWS_KEYWORD (default: 국민연금)
- NEWS_POLL_SEC (default: 120)
- NEWS_SOURCES (csv: naver,daum)
- CREATE_WATCH_FOR_NEWS (0|1, default 1)
- CREATE_WATCH_FOR_RELATED (0|1, default 0)
- RELATED_TOP_K (default: 5) - number of related results per engine
- YOUTUBE_API_KEY (optional) - if set, fetch comments for discovered videos
- PPLX_API_KEY (optional) - if set, use Perplexity to find related web pages
- WATCH_TAG (optional) - reused from BridgeConfig for ChangeDetection tagging (name)

Message bus reuses BusConfig/BridgeConfig from config.py
- MESSAGE_BUS: stdout|kafka|pubsub
- RAW_TOPIC: topic name for raw posts (default per bus)
- SEED_TOPIC: topic name for seed events (default: seed.news.v1)

Run:
  python BACKEND-WEB-COLLECTOR/news_watcher.py
"""

import json
import os
import time
import uuid
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
try:
    from readability import Document  # type: ignore
    HAS_READABILITY = True
except Exception:
    HAS_READABILITY = False
try:
    import yake  # type: ignore
    HAS_YAKE = True
except Exception:
    HAS_YAKE = False
try:
    from prometheus_client import Counter, Histogram, start_http_server  # type: ignore
    HAS_PROM = True
except Exception:
    HAS_PROM = False
try:
    import sentry_sdk  # type: ignore
    HAS_SENTRY = True
except Exception:
    HAS_SENTRY = False
try:
    # Package-relative imports
    from .config import ChangeDetectionConfig, BusConfig, BridgeConfig, PerplexityConfig
    from .cdio_client import ChangeDetectionClient
    from .perplexity_client import PerplexityClient
    from .publishers import make_publisher
except Exception:
    # Script execution fallback
    import sys as _sys
    _sys.path.append(os.path.dirname(__file__))
    from config import ChangeDetectionConfig, BusConfig, BridgeConfig, PerplexityConfig  # type: ignore
    from cdio_client import ChangeDetectionClient  # type: ignore
    from perplexity_client import PerplexityClient  # type: ignore
    from publishers import make_publisher  # type: ignore


@dataclass
class NewsWatcherConfig:
    keyword: str = os.getenv("NEWS_KEYWORD", "국민연금")
    poll_sec: int = int(os.getenv("NEWS_POLL_SEC", "120"))
    sources: List[str] = tuple(map(str.strip, os.getenv("NEWS_SOURCES", "naver,daum").split(",")))  # type: ignore
    create_watch_news: bool = os.getenv("CREATE_WATCH_FOR_NEWS", "1") in ("1", "true", "True")
    create_watch_related: bool = os.getenv("CREATE_WATCH_FOR_RELATED", "0") in ("1", "true", "True")
    related_top_k: int = int(os.getenv("RELATED_TOP_K", "5"))
    seed_topic: str = os.getenv("SEED_TOPIC", "seed.news.v1")
    # Enrichment features
    enable_article_body: bool = os.getenv("ENABLE_ARTICLE_BODY", "1") in ("1", "true", "True")
    enable_comments: bool = os.getenv("ENABLE_COMMENTS", "0") in ("1", "true", "True")
    enable_naver_comments: bool = os.getenv("ENABLE_NAVER_COMMENTS", "0") in ("1", "true", "True")
    enable_inline_nlp: bool = os.getenv("ENABLE_INLINE_NLP", "0") in ("1", "true", "True")
    enable_dynamic_keywords: bool = os.getenv("ENABLE_DYNAMIC_KEYWORDS", "0") in ("1", "true", "True")
    dynamic_keywords_limit: int = int(os.getenv("DYNAMIC_KEYWORDS_LIMIT", "3"))
    # Hugging Face Inference API for sentiment (optional)
    hf_sentiment_model: str = os.getenv("HF_SENTIMENT_MODEL", "")
    hf_api_url: Optional[str] = os.getenv("HF_SENTIMENT_API_URL", "") or None
    hf_api_key: Optional[str] = os.getenv("HF_API_KEY", "") or None
    # Robots and rate limiting
    enable_robots_check: bool = os.getenv("ENABLE_ROBOTS_CHECK", "1") in ("1", "true", "True")
    global_max_rps: float = float(os.getenv("GLOBAL_MAX_RPS", "1.0"))
    # Metrics & Sentry
    metrics_port: Optional[int] = int(os.getenv("METRICS_PORT", "0")) or None
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN", "") or None
    # Playwright settings
    playwright_headless: bool = os.getenv("PLAYWRIGHT_HEADLESS", "1") in ("1", "true", "True")


@dataclass
class SeedState:
    # url_norm -> iso_ts when processed
    seen: Dict[str, str]

    @staticmethod
    def load(path: str) -> "SeedState":
        if not os.path.exists(path):
            return SeedState(seen={})
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SeedState(seen=data.get("seen", {}))
        except Exception:
            return SeedState(seen={})

    def save(self, path: str) -> None:
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"seen": self.seen}, f, ensure_ascii=False)
        os.replace(tmp, path)


def norm_url(u: str) -> str:
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(u)
        path = parts.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))
    except Exception:
        return u


def hash_key(s: str) -> bytes:
    import hashlib

    return hashlib.sha256(s.encode("utf-8")).digest()


def compute_author_hash(platform: str, author: Optional[str]) -> str:
    """Stable author hash for persona estimation across events. Returns 32-hex or empty."""
    if not author:
        return ""
    import hashlib as _hl
    return _hl.sha256(f"{platform}:{author}".encode("utf-8")).hexdigest()[:32]


# ------------------------ Fetchers ------------------------

def _ua_session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    })
    return sess

def _soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


# ------------------------ Guardrails & Limits ------------------------

class RateLimiter:
    def __init__(self, rps: float) -> None:
        from collections import deque
        self.interval = 1.0 / max(0.001, rps)
        self.last_ts = 0.0

    def acquire(self) -> None:
        import time as _t
        now = _t.time()
        delta = now - self.last_ts
        if delta < self.interval:
            _t.sleep(self.interval - delta)
        self.last_ts = _t.time()


class RobotsGuard:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._cache: Dict[str, Any] = {}

    def _get_parser(self, base: str):
        import urllib.robotparser as rp
        import urllib.parse as up
        parsed = up.urlparse(base)
        root = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        if root in self._cache:
            return self._cache[root]
        parser = rp.RobotFileParser()
        try:
            parser.set_url(root)
            parser.read()
        except Exception:
            parser.disallow_all = False  # type: ignore
        self._cache[root] = parser
        return parser

    def allowed(self, url: str, ua: str = "*") -> bool:
        if not self.enabled:
            return True
        try:
            parser = self._get_parser(url)
            return parser.can_fetch(ua, url)
        except Exception:
            return True


# Globals set in main()
RATE_LIMITER: Optional[RateLimiter] = None
ROBOTS_GUARD: Optional[RobotsGuard] = None
_C_REQ = None
_H_REQ_LAT = None
_C_PUB = None
_C_ERR = None
_C_SUM = None  # summaries counter
_H_SUM_LAT = None  # summary latency histogram


def request_get(sess: requests.Session, url: str, *, timeout: int = 20, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    import time as _t
    start = _t.time()
    if ROBOTS_GUARD and not ROBOTS_GUARD.allowed(url):
        raise RuntimeError(f"Blocked by robots.txt: {url}")
    if RATE_LIMITER:
        RATE_LIMITER.acquire()
    try:
        r = sess.get(url, timeout=timeout, headers=headers, params=params)
        if _C_REQ:
            try:
                _C_REQ.labels(domain=_domain(url), status=str(r.status_code)).inc()
            except Exception:
                pass
        return r
    finally:
        if _H_REQ_LAT:
            try:
                _H_REQ_LAT.observe(max(0.0, _t.time() - start))
            except Exception:
                pass


def _domain(url: str) -> str:
    try:
        import urllib.parse as up
        return up.urlparse(url).netloc
    except Exception:
        return ""


def _extract_main_text(html: str, url: str) -> Tuple[str, str]:
    """Extract (title, text) from an article page. Uses readability if available, with safe fallback."""
    title = ""
    text = ""
    if HAS_READABILITY:
        try:
            doc = Document(html)
            title = (doc.short_title() or doc.title() or "").strip()
            summary_html = doc.summary(html_partial=True)
            body = _soup(summary_html).get_text(" ", strip=True)
            text = body.strip()
        except Exception:
            pass
    if not text:
        s = _soup(html)
        candidate = s.select_one("article") or s.select_one("#articleBody, .article_body, .news_view, #article")
        if candidate:
            text = candidate.get_text(" ", strip=True)
        else:
            text = s.get_text(" ", strip=True)
        title = title or (s.title.string.strip() if s.title and s.title.string else "")
    if len(text) > 12000:
        text = text[:12000]
    return title, text


def analyze_sentiment_via_hf(text: str, cfg: NewsWatcherConfig) -> Optional[Dict[str, Any]]:
    """Call HF Inference API for sentiment if configured. Return {label, score} or None."""
    if not cfg.enable_inline_nlp:
        return None
    model = cfg.hf_sentiment_model
    if not (model or cfg.hf_api_url):
        return None
    api_url = cfg.hf_api_url or f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Content-Type": "application/json"}
    if cfg.hf_api_key:
        headers["Authorization"] = f"Bearer {cfg.hf_api_key}"
    try:
        payload = {"inputs": text[:4000], "options": {"wait_for_model": True}}
        resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        scores = None
        if isinstance(data, list) and data and isinstance(data[0], list):
            scores = data[0]
        elif isinstance(data, list):
            scores = data
        if not scores:
            return None
        best = max(scores, key=lambda x: x.get("score", 0))
        raw = str(best.get("label", "")).lower()
        label = "neutral"
        if any(k in raw for k in ["pos", "+", "5 star", "4 star", "positive"]):
            label = "positive"
        elif any(k in raw for k in ["neg", "-", "1 star", "2 star", "negative"]):
            label = "negative"
        return {"label": label, "score": float(best.get("score", 0.0))}
    except Exception:
        return None


def extract_keywords_yake(text: str, top_k: int = 10) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if HAS_YAKE:
        try:
            kw_extractor = yake.KeywordExtractor(lan="ko", n=1, top=top_k)
            kws = kw_extractor.extract_keywords(text)
            kws_sorted = sorted(kws, key=lambda x: x[1])[:top_k]
            return [k for k, _ in kws_sorted]
        except Exception:
            pass
    tokens = re.findall(r"[\w가-힣]{2,}", text)
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:top_k]]


def extract_daum_post_id(html: str) -> Optional[str]:
    for pat in [r'"postId"\s*:\s*(\d+)', r'data-post-id\s*=\s*"(\d+)"']:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    s = _soup(html)
    og = s.select_one('meta[property="og:url"]')
    if og and og.get('content'):
        m = re.search(r"/v/(\d+)", og['content'])
        if m:
            return m.group(1)
    return None


def fetch_daum_comments_by_post_id(sess: requests.Session, referer_url: str, post_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        api = f"https://comment.daum.net/apis/v1/posts/{post_id}/comments"
        params = {"offset": 0, "limit": min(100, limit), "sort": "RECOMMEND"}
        headers = {"Referer": referer_url, "Accept": "application/json"}
        r = request_get(sess, api, timeout=20, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        for c in data or []:
            sn = c.get("content") or c.get("text") or ""
            author = (c.get("user", {}) or {}).get("displayName") or (c.get("userId") or "")
            likes = c.get("likeCount") or c.get("like") or 0
            dislikes = c.get("dislikeCount") or c.get("dislike") or 0
            out.append({
                "author": str(author or ""),
                "text": str(sn or ""),
                "likes": int(likes or 0),
                "dislikes": int(dislikes or 0)
            })
    except Exception:
        pass
    return out

def fetch_naver_news(keyword: str, sess: Optional[requests.Session] = None) -> List[Dict[str, str]]:
    """Return list of {title, url} for recent Naver news search results."""
    sess = sess or _ua_session()
    q = requests.utils.quote(keyword)
    url = f"https://search.naver.com/search.naver?where=news&sm=tab_opt&sort=1&query={q}"
    r = request_get(sess, url, timeout=20)
    r.raise_for_status()
    soup = _soup(r.text)
    out: List[Dict[str, str]] = []
    for a in soup.select("a.news_tit"):
        href = a.get("href", "")
        title = a.get("title") or a.text.strip()
        if not href or not title:
            continue
        # Prefer direct naver/v.daum links eventually resolved by publisher sites
        out.append({"title": title, "url": href})
    return out


def fetch_daum_news(keyword: str, sess: Optional[requests.Session] = None) -> List[Dict[str, str]]:
    """Return list of {title, url} for recent Daum news search results."""
    sess = sess or _ua_session()
    q = requests.utils.quote(keyword)
    url = f"https://search.daum.net/search?w=news&sort=recency&q={q}"
    r = request_get(sess, url, timeout=20)
    r.raise_for_status()
    soup = _soup(r.text)
    out: List[Dict[str, str]] = []
    # Various selectors for robustness
    for a in soup.select("a.f_nb, a.f_link_b, a.c-tit-doc"):
        href = a.get("href", "")
        title = a.get("title") or a.text.strip()
        if not href or not title:
            continue
        out.append({"title": title, "url": href})
    # Fallback generic
    if not out:
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            txt = a.get("title") or a.text.strip()
            if href and txt and ("v.daum.net" in href or "/news/" in href):
                out.append({"title": txt, "url": href})
    return out


# ------------------------ Event builders ------------------------

def build_seed_event(item: Dict[str, str], source_site: str, br_cfg: BridgeConfig) -> Dict[str, Any]:
    url = item.get("url", "")
    title = item.get("title", "")
    url_n = norm_url(url)
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "source": "news",
        "channel": source_site,
        "url": url,
        "author_hash": "",
        "text": title,
        "lang": "",
        "created_at": now.isoformat(),
        "meta": {
            "url_norm": url_n,
            "platform_profile": br_cfg.platform_profile,
            "title": title,
            "keyword": os.getenv("NEWS_KEYWORD", "국민연금"),
            "tags": ["seed"],
        },
    }


def build_raw_event(url: str, text: str, source: str, channel: str, br_cfg: BridgeConfig, extra_meta: Optional[Dict[str, Any]] = None, *, author_hash: str = "") -> Dict[str, Any]:
    url_n = norm_url(url)
    now = datetime.now(timezone.utc)
    meta = {
        "url_norm": url_n,
        "platform_profile": br_cfg.platform_profile,
    }
    if extra_meta:
        meta.update(extra_meta)
    return {
        "id": str(uuid.uuid4()),
        "source": source,
        "channel": channel,
        "url": url,
        "author_hash": author_hash or "",
        "text": text,
        "lang": "",
        "created_at": now.isoformat(),
        "meta": meta,
    }


# ------------------------ Expansion ------------------------

# Summarization import (lazy, optional)
try:
    from .summarizer import build_summary_event  # type: ignore
except Exception:
    try:
        from summarizer import build_summary_event  # type: ignore
    except Exception:
        build_summary_event = None  # type: ignore


def _maybe_publish_summary(raw_evt: Dict[str, Any], publisher, bus_cfg: BusConfig):
    """Build and publish a summary event for a just-published raw event.
    Guarded by summarizer feature flags inside build_summary_event.
    """
    if not build_summary_event:
        return
    try:
        import time as _t
        start = _t.time()
        summary_evt = build_summary_event(raw_evt)
        if not summary_evt:
            return
        headers = {
            "trace_id": str(uuid.uuid4()),
            "schema_version": "summary.events.v1",
            "source": raw_evt.get("source"),
            "channel": raw_evt.get("channel"),
            "content_type": "application/json",
            "platform_profile": raw_evt.get("meta", {}).get("platform_profile"),
            "raw_id": raw_evt.get("id"),
        }
        key = hash_key(f"summary:{raw_evt.get('id')}")
        data = json.dumps(summary_evt, ensure_ascii=False).encode("utf-8")
        publisher.publish(bus_cfg.summary_topic, key=key, value=data, headers=headers)
        if _C_PUB:
            try:
                _C_PUB.labels(topic=bus_cfg.summary_topic).inc()
            except Exception:
                pass
        if _C_SUM:
            try:
                _C_SUM.labels(topic=bus_cfg.summary_topic).inc()
            except Exception:
                pass
        if _H_SUM_LAT:
            try:
                _H_SUM_LAT.observe(max(0.0, _t.time() - start))
            except Exception:
                pass
    except Exception:
        if _C_ERR:
            try:
                _C_ERR.labels(type="summary").inc()
            except Exception:
                pass
        pass

def youtube_search_and_comments(api_key: str, query: str, max_videos: int = 5, max_comments: int = 50) -> List[Tuple[str, str, List[Dict[str, Any]]]]:
    """Return list of (video_id, title, comments[{author, text, likes}])."""
    sess = _ua_session()
    # Search videos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_videos,
        "order": "date",
        "safeSearch": "none",
    }
    r = request_get(sess, search_url, timeout=20, params=params)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    out: List[Tuple[str, str, List[Dict[str, Any]]]] = []
    for it in items:
        vid = it.get("id", {}).get("videoId")
        title = (it.get("snippet", {}) or {}).get("title", "")
        if not vid:
            continue
        comments: List[Dict[str, Any]] = []
        try:
            ct_url = "https://www.googleapis.com/youtube/v3/commentThreads"
            ct_params = {
                "key": api_key,
                "part": "snippet",
                "videoId": vid,
                "maxResults": min(100, max_comments),
                "order": "relevance",
                "textFormat": "plainText",
            }
            rr = request_get(sess, ct_url, timeout=20, params=ct_params)
            rr.raise_for_status()
            cdata = rr.json()
            for c in cdata.get("items", [])[:max_comments]:
                top = (c.get("snippet", {}) or {}).get("topLevelComment", {})
                sn = top.get("snippet", {})
                comments.append({
                    "author": str(sn.get("authorDisplayName") or ""),
                    "text": str(sn.get("textDisplay") or ""),
                    "likes": int(sn.get("likeCount") or 0),
                })
        except Exception:
            pass
        out.append((vid, title, comments))
    return out


def expand_seed(seed_evt: Dict[str, Any], bus_cfg: BusConfig, br_cfg: BridgeConfig, cd_client: Optional[ChangeDetectionClient], publisher) -> None:
    """Expand a seed news event by fetching related web results and YouTube items.
    Publishes raw.posts.v1 events for related pages, videos, and comments.
    """
    watcher_cfg = NewsWatcherConfig()

    # Perplexity web search expansion
    try:
        pplx_cfg = PerplexityConfig.from_env()
        if pplx_cfg.api_key:
            pplx = PerplexityClient(base_url=pplx_cfg.base_url, api_key=pplx_cfg.api_key, model=pplx_cfg.model, timeout=pplx_cfg.timeout_sec)
            query = f"{seed_evt.get('text','')} 관련 커뮤니티 반응과 토론"
            results = pplx.search(query, top_k=watcher_cfg.related_top_k)
            for r in results:
                url = r.get("url") or ""
                snippet = r.get("snippet") or r.get("title") or ""
                if not url or not snippet:
                    continue
                meta = {
                    "seed_url": seed_evt.get("url"),
                    "seed_id": seed_evt.get("id"),
                    "seed_title": seed_evt.get("text"),
                    "title": r.get("title"),
                    "score": r.get("score"),
                    "source_engine": "perplexity",
                }
                evt = build_raw_event(url, snippet, source="web", channel="search", br_cfg=br_cfg, extra_meta=meta)
                headers = {
                    "trace_id": str(uuid.uuid4()),
                    "schema_version": "raw.posts.v1",
                    "source": evt["source"],
                    "channel": evt["channel"],
                    "content_type": "text/plain",
                    "platform_profile": br_cfg.platform_profile,
                }
                key = hash_key(f"{evt['source']}:{evt['meta']['url_norm']}")
                data = json.dumps(evt, ensure_ascii=False).encode("utf-8")
                publisher.publish(bus_cfg.raw_topic, key=key, value=data, headers=headers)
                _maybe_publish_summary(evt, publisher, bus_cfg)
                if watcher_cfg.create_watch_related and cd_client:
                    try:
                        cd_client.import_urls(text=url, tag=os.getenv("WATCH_TAG"))
                    except Exception:
                        pass
    except Exception:
        pass

    # YouTube related expansion
    try:
        ytb_key = os.getenv("YOUTUBE_API_KEY", "")
        if ytb_key:
            videos = youtube_search_and_comments(ytb_key, query=seed_evt.get("text", ""), max_videos=watcher_cfg.related_top_k, max_comments=50)
            for vid, title, comments in videos:
                video_url = f"https://www.youtube.com/watch?v={vid}"
                meta_v = {
                    "seed_url": seed_evt.get("url"),
                    "seed_id": seed_evt.get("id"),
                    "seed_title": seed_evt.get("text"),
                    "video_id": vid,
                    "video_title": title,
                }
                evt_video = build_raw_event(video_url, title or video_url, source="youtube", channel="video", br_cfg=br_cfg, extra_meta=meta_v)
                headers_video = {
                    "trace_id": str(uuid.uuid4()),
                    "schema_version": "raw.posts.v1",
                    "source": evt_video["source"],
                    "channel": evt_video["channel"],
                    "content_type": "text/plain",
                    "platform_profile": br_cfg.platform_profile,
                }
                key_v = hash_key(f"{evt_video['source']}:{evt_video['meta']['url_norm']}")
                data_v = json.dumps(evt_video, ensure_ascii=False).encode("utf-8")
                publisher.publish(bus_cfg.raw_topic, key=key_v, value=data_v, headers=headers_video)
                _maybe_publish_summary(evt_video, publisher, bus_cfg)
                for c in comments:
                    ctext = c.get("text") or ""
                    if not ctext:
                        continue
                    meta_c = {
                        "seed_url": seed_evt.get("url"),
                        "seed_id": seed_evt.get("id"),
                        "seed_title": seed_evt.get("text"),
                        "video_id": vid,
                        "video_title": title,
                        "author": c.get("author"),
                        "likes": c.get("likes", 0),
                    }
                    if NewsWatcherConfig().enable_inline_nlp:
                        senti_c = analyze_sentiment_via_hf(ctext, NewsWatcherConfig())
                        if senti_c:
                            meta_c.update({
                                "sentiment": senti_c.get("label"),
                                "sentiment_score": senti_c.get("score"),
                            })
                    evt_cmt = build_raw_event(
                        video_url,
                        ctext,
                        source="youtube",
                        channel="comment",
                        br_cfg=br_cfg,
                        extra_meta=meta_c,
                        author_hash=compute_author_hash("youtube", c.get("author")),
                    )
                    headers_c = {
                        "trace_id": str(uuid.uuid4()),
                        "schema_version": "raw.posts.v1",
                        "source": evt_cmt["source"],
                        "channel": evt_cmt["channel"],
                        "content_type": "text/plain",
                        "platform_profile": br_cfg.platform_profile,
                    }
                    key_c = hash_key(f"{evt_cmt['source']}:{evt_cmt['meta']['url_norm']}:{hash(ctext)}")
                    data_c = json.dumps(evt_cmt, ensure_ascii=False).encode("utf-8")
                    publisher.publish(bus_cfg.raw_topic, key=key_c, value=data_c, headers=headers_c)
    except Exception:
        pass


# ------------------------ Main loop ------------------------

if __name__ == "__main__":
    bus_cfg = BusConfig.from_env()
    br_cfg = BridgeConfig.from_env()
    cd_cfg = ChangeDetectionConfig.from_env()
    watcher_cfg = NewsWatcherConfig()

    cd_client = ChangeDetectionClient(cd_cfg.base_url, cd_cfg.api_key)
    publisher = make_publisher(bus_cfg.bus, bus_cfg.kafka_brokers, bus_cfg.pubsub_project)

    state_path = os.getenv("NEWS_STATE_PATH", ".news_state.json")
    state = SeedState.load(state_path)

    sess = _ua_session()

    print(json.dumps({
        "msg": "news watcher starting",
        "keyword": watcher_cfg.keyword,
        "sources": list(watcher_cfg.sources),
        "poll": watcher_cfg.poll_sec,
        "bus": bus_cfg.bus,
        "raw_topic": bus_cfg.raw_topic,
        "seed_topic": watcher_cfg.seed_topic,
        "cd_base": cd_cfg.base_url,
    }, ensure_ascii=False))

    # Init Sentry
    if HAS_SENTRY and watcher_cfg.sentry_dsn:
        try:
            sentry_sdk.init(dsn=watcher_cfg.sentry_dsn)
        except Exception:
            pass

    # Init Prometheus metrics
    if HAS_PROM:
        try:
            _C_REQ = Counter("newswatcher_http_requests_total", "HTTP requests", ["domain", "status"])  # type: ignore
            _H_REQ_LAT = Histogram("newswatcher_http_request_seconds", "HTTP request latency seconds")  # type: ignore
            _C_PUB = Counter("newswatcher_events_published_total", "Published events", ["topic"])  # type: ignore
            _C_ERR = Counter("newswatcher_errors_total", "Errors", ["type"])  # type: ignore
            _C_SUM = Counter("newswatcher_summaries_total", "Summary events published", ["topic"])  # type: ignore
            _H_SUM_LAT = Histogram("newswatcher_summary_latency_seconds", "Summary build+publish latency seconds")  # type: ignore
            if watcher_cfg.metrics_port:
                start_http_server(int(watcher_cfg.metrics_port))  # type: ignore
        except Exception:
            pass

    # Init robots and rate limiter
    RATE_LIMITER = RateLimiter(watcher_cfg.global_max_rps)
    ROBOTS_GUARD = RobotsGuard(enabled=watcher_cfg.enable_robots_check)

    while True:
        try:
            def process_article(item: Dict[str, str], source_site: str, allow_expand: bool = True) -> None:
                url = item.get("url", "")
                url_n = norm_url(url)
                if not url_n or url_n in state.seen:
                    return
                # Seed event
                seed_evt = build_seed_event(item, source_site=source_site, br_cfg=br_cfg)
                headers = {
                    "trace_id": str(uuid.uuid4()),
                    "schema_version": "seed.news.v1",
                    "source": seed_evt["source"],
                    "channel": seed_evt["channel"],
                    "content_type": "text/plain",
                    "platform_profile": br_cfg.platform_profile,
                }
                key = hash_key(f"news:{url_n}")
                data = json.dumps(seed_evt, ensure_ascii=False).encode("utf-8")
                publisher.publish(watcher_cfg.seed_topic, key=key, value=data, headers=headers)
                if _C_PUB:
                    try:
                        _C_PUB.labels(topic=watcher_cfg.seed_topic).inc()
                    except Exception:
                        pass

                # Create watch for the article
                if watcher_cfg.create_watch_news and cd_client:
                    try:
                        cd_client.import_urls(text=url, tag=os.getenv("WATCH_TAG"))
                    except Exception:
                        pass

                # Fetch article body and comments (optional)
                article_title = None
                article_text = None
                if watcher_cfg.enable_article_body or watcher_cfg.enable_comments:
                    try:
                        rr = request_get(sess, url, timeout=20)
                        rr.raise_for_status()
                        html = rr.text
                        if watcher_cfg.enable_article_body:
                            t, body = _extract_main_text(html, url)
                            article_title = t
                            article_text = body
                            if body:
                                # Optional enrichment
                                enr_meta: Dict[str, Any] = {
                                    "seed_url": seed_evt.get("url"),
                                    "seed_id": seed_evt.get("id"),
                                    "seed_title": seed_evt.get("text"),
                                    "article_title": t,
                                }
                                if watcher_cfg.enable_inline_nlp:
                                    senti = analyze_sentiment_via_hf(body, watcher_cfg)
                                    if senti:
                                        enr_meta.update({
                                            "sentiment": senti.get("label"),
                                            "sentiment_score": senti.get("score"),
                                        })
                                    kws = extract_keywords_yake(f"{seed_evt.get('text','')}\n{body}", top_k=10)
                                    if kws:
                                        enr_meta["keywords"] = kws
                                evt_article = build_raw_event(url, body, source="news", channel="article", br_cfg=br_cfg, extra_meta=enr_meta)
                                headers_article = {
                                    "trace_id": str(uuid.uuid4()),
                                    "schema_version": "raw.posts.v1",
                                    "source": evt_article["source"],
                                    "channel": evt_article["channel"],
                                    "content_type": "text/plain",
                                    "platform_profile": br_cfg.platform_profile,
                                }
                                key_a = hash_key(f"{evt_article['source']}:{evt_article['meta']['url_norm']}:article")
                                data_a = json.dumps(evt_article, ensure_ascii=False).encode("utf-8")
                                publisher.publish(bus_cfg.raw_topic, key=key_a, value=data_a, headers=headers_article)
                                _maybe_publish_summary(evt_article, publisher, bus_cfg)
                                if _C_PUB:
                                    try:
                                        _C_PUB.labels(topic=bus_cfg.raw_topic).inc()
                                    except Exception:
                                        pass

                        if watcher_cfg.enable_comments and "daum.net" in url:
                            post_id = extract_daum_post_id(html)
                            if post_id:
                                comments = fetch_daum_comments_by_post_id(sess, referer_url=url, post_id=post_id, limit=100)
                                for c in comments:
                                    ctext = c.get("text") or ""
                                    if not ctext:
                                        continue
                                    meta_c = {
                                        "seed_url": seed_evt.get("url"),
                                        "seed_id": seed_evt.get("id"),
                                        "seed_title": seed_evt.get("text"),
                                        "article_title": article_title,
                                        "likes": c.get("likes", 0),
                                        "dislikes": c.get("dislikes", 0),
                                        "author": c.get("author"),
                                        "comment_provider": "daum",
                                    }
                                    if watcher_cfg.enable_inline_nlp:
                                        senti_c = analyze_sentiment_via_hf(ctext, watcher_cfg)
                                        if senti_c:
                                            meta_c.update({
                                                "sentiment": senti_c.get("label"),
                                                "sentiment_score": senti_c.get("score"),
                                            })
                                    evt_c = build_raw_event(
                                        url,
                                        ctext,
                                        source="news",
                                        channel="comment",
                                        br_cfg=br_cfg,
                                        extra_meta=meta_c,
                                        author_hash=compute_author_hash("daum", c.get("author")),
                                    )
                                    headers_c = {
                                        "trace_id": str(uuid.uuid4()),
                                        "schema_version": "raw.posts.v1",
                                        "source": evt_c["source"],
                                        "channel": evt_c["channel"],
                                        "content_type": "text/plain",
                                        "platform_profile": br_cfg.platform_profile,
                                    }
                                    key_c = hash_key(f"{evt_c['source']}:{evt_c['meta']['url_norm']}:{hash(ctext)}")
                                    data_c = json.dumps(evt_c, ensure_ascii=False).encode("utf-8")
                                    publisher.publish(bus_cfg.raw_topic, key=key_c, value=data_c, headers=headers_c)

                        # Naver comments via Playwright (optional)
                        if watcher_cfg.enable_comments and watcher_cfg.enable_naver_comments and "naver.com" in url:
                            try:    
                                comments_nv = fetch_naver_comments_playwright(url, limit=200, headless=watcher_cfg.playwright_headless)
                                for c in comments_nv:
                                    ctext = c.get("text") or ""
                                    if not ctext:
                                        continue
                                    meta_c = {
                                        "seed_url": seed_evt.get("url"),
                                        "seed_id": seed_evt.get("id"),
                                        "seed_title": seed_evt.get("text"),
                                        "article_title": article_title,
                                        "likes": c.get("likes", 0),
                                        "dislikes": c.get("dislikes", 0),
                                        "author": c.get("author"),
                                        "comment_provider": "naver",
                                    }
                                    if watcher_cfg.enable_inline_nlp:
                                        senti_c = analyze_sentiment_via_hf(ctext, watcher_cfg)
                                        if senti_c:
                                            meta_c.update({
                                                "sentiment": senti_c.get("label"),
                                                "sentiment_score": senti_c.get("score"),
                                            })
                                    evt_c = build_raw_event(
                                        url,
                                        ctext,
                                        source="news",
                                        channel="comment",
                                        br_cfg=br_cfg,
                                        extra_meta=meta_c,
                                        author_hash=compute_author_hash("naver", c.get("author")),
                                    )
                                    headers_c = {
                                        "trace_id": str(uuid.uuid4()),
                                        "schema_version": "raw.posts.v1",
                                        "source": evt_c["source"],
                                        "channel": evt_c["channel"],
                                        "content_type": "text/plain",
                                        "platform_profile": br_cfg.platform_profile,
                                    }
                                    key_c = hash_key(f"{evt_c['source']}:{evt_c['meta']['url_norm']}:{hash(ctext)}")
                                    data_c = json.dumps(evt_c, ensure_ascii=False).encode("utf-8")
                                    publisher.publish(bus_cfg.raw_topic, key=key_c, value=data_c, headers=headers_c)
                            except Exception:
                                pass
                    except Exception:
                        pass

                # Expand immediately via YouTube/Perplexity
                expand_seed(seed_evt, bus_cfg, br_cfg, cd_client, publisher)

                # Dynamic keyword expansion (single-level)
                if allow_expand and watcher_cfg.enable_dynamic_keywords and article_text:
                    dyn_kws = extract_keywords_yake(f"{seed_evt.get('text','')}\n{article_text}", top_k=watcher_cfg.dynamic_keywords_limit)
                    for dyn_kw in dyn_kws:
                        for src2 in watcher_cfg.sources:
                            try:
                                sub_items: List[Dict[str, str]] = []
                                if src2 == "naver":
                                    sub_items = fetch_naver_news(dyn_kw, sess)
                                elif src2 == "daum":
                                    sub_items = fetch_daum_news(dyn_kw, sess)
                                for sub in sub_items[:5]:
                                    process_article(sub, src2, allow_expand=False)
                            except Exception:
                                continue

                state.seen[url_n] = datetime.now(timezone.utc).isoformat()
                state.save(state_path)

            # Process base keyword first
            for source in watcher_cfg.sources:
                try:
                    items: List[Dict[str, str]] = []
                    if source == "naver":
                        items = fetch_naver_news(watcher_cfg.keyword, sess)
                    elif source == "daum":
                        items = fetch_daum_news(watcher_cfg.keyword, sess)
                    else:
                        continue
                    for it in items[:20]:
                        process_article(it, source, allow_expand=True)
                except Exception:
                    continue

            time.sleep(watcher_cfg.poll_sec)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            time.sleep(min(60, watcher_cfg.poll_sec))


def fetch_naver_comments_playwright(url: str, limit: int = 200, headless: bool = True) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return comments
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(10000)
            page.goto(url)
            # Wait for naver comment module
            sel_module = "#cbox_module, .u_cbox"
            try:
                page.wait_for_selector(sel_module, timeout=15000)
            except Exception:
                browser.close()
                return comments
            # Click more buttons until enough
            load_more_selectors = [
                ".u_cbox_btn_more",
                ".u_cbox_btn_view_more",
            ]
            loaded = 0
            for _ in range(30):
                if loaded >= limit:
                    break
                clicked = False
                for sel in load_more_selectors:
                    btns = page.query_selector_all(sel)
                    if btns:
                        try:
                            btns[0].click()
                            clicked = True
                            page.wait_for_timeout(800)
                            break
                        except Exception:
                            pass
                if not clicked:
                    break
                # update loaded count heuristically
                loaded = len(page.query_selector_all(".u_cbox_comment"))
            # Extract comments
            items = page.query_selector_all(".u_cbox_comment")
            for it in items[:limit]:
                try:
                    author = (it.query_selector(".u_cbox_nick") or it.query_selector(".u_cbox_name")).inner_text().strip()  # type: ignore
                except Exception:
                    author = ""
                try:
                    text = (it.query_selector(".u_cbox_contents") or it.query_selector(".u_cbox_text_wrap")).inner_text().strip()  # type: ignore
                except Exception:
                    text = ""
                def _num(sel: str) -> int:
                    try:
                        el = it.query_selector(sel)
                        if not el:
                            return 0
                        t = el.inner_text().replace(",", "").strip()
                        return int(re.findall(r"\d+", t)[0]) if re.findall(r"\d+", t) else 0
                    except Exception:
                        return 0
                likes = _num(".u_cbox_cnt_recomm")
                dislikes = _num(".u_cbox_cnt_unrecomm")
                if text:
                    comments.append({"author": author, "text": text, "likes": likes, "dislikes": dislikes})
            browser.close()
    except Exception:
        pass
    return comments


