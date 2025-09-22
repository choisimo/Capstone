import uvicorn
from app.config import settings

class FastAPI:
    def __init__(self, title="", description="", version=""):
        self.title = title
        self.description = description
        self.version = version
        self.routes = []
    
    def include_router(self, router, prefix="", tags=None):
        pass

app = FastAPI(
    title="OSINT Source Registry Service",
    description="Manages OSINT source registry with validation and trust scoring",
    version="1.0.0"
)

from app.routers import sources

app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-source-registry"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)