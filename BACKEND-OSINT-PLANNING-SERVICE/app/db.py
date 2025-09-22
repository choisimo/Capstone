import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/osint_db")

# Mock database connection for now - will be replaced with SQLAlchemy
class MockDB:
    def __init__(self):
        self.data = {}
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass

def get_db():
    return MockDB()