from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from crawl4ai import AsyncWebCrawler  # type: ignore
except Exception:
    AsyncWebCrawler = None  # fallback for environments without crawl4ai

app = FastAPI(title="Crawl4AI Worker", version="0.1.0")


class CrawlRequest(BaseModel):
    url: str
    js_render: bool = False
    wait_for: Optional[str] = None  # CSS selector to wait for (optional)


class CrawlResponse(BaseModel):
    url: str
    markdown: Optional[str] = None
    html: Optional[str] = None
    status: str


@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl_url(request: CrawlRequest):
    if AsyncWebCrawler is None:
        raise HTTPException(status_code=500, detail="crawl4ai not available in this environment")

    try:
        # Manage browser lifecycle via context manager
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=request.url,
                js_code=request.wait_for if request.js_render else None,
            )

            if not getattr(result, "success", False):
                raise HTTPException(status_code=400, detail=f"Crawl failed: {getattr(result, 'error_message', 'unknown')}")

            return CrawlResponse(
                url=getattr(result, "url", request.url),
                markdown=getattr(result, "markdown", None),
                html=getattr(result, "html", None),
                status="SUCCESS",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
