import os
from datetime import datetime

class Settings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/osint_db")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.message_broker_url = os.getenv("MESSAGE_BROKER_URL", "amqp://guest:guest@localhost/")
        self.service_name = "osint-planning-service"
        self.log_level = "INFO"
        self.port = int(os.getenv("PORT", "8020"))

settings = Settings()

# Mock FastAPI app structure
class MockApp:
    def __init__(self, title="", lifespan=None):
        self.title = title
        self.lifespan = lifespan
        self.middleware = []
        self.routers = []
    
    def add_middleware(self, middleware_class, **kwargs):
        self.middleware.append((middleware_class, kwargs))
    
    def include_router(self, router, prefix=""):
        self.routers.append((router, prefix))

# Health check endpoint
def health_check():
    return {
        "status": "healthy", 
        "service": settings.service_name,
        "timestamp": datetime.utcnow().isoformat()
    }

# Create app instance
app = MockApp(title=settings.service_name)

print(f"OSINT Planning Service initialized")
print(f"Service: {settings.service_name}")
print(f"Database: {settings.database_url}")
print(f"Port: {settings.port}")

# Test the health check
if __name__ == "__main__":
    health = health_check()
    print(f"Health check: {health}")
    
    # Import and test the keyword router
    try:
        from routers.keywords import router, test_api
        app.include_router(router, prefix="/api/v1")
        print("Keywords router loaded successfully")
        test_api()
    except ImportError as e:
        print(f"Error importing keywords router: {e}")
        
    print(f"Server would start on port {settings.port}")