import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Lightweight in-memory DB stub (to be replaced with SQLAlchemy)
class InMemoryDB:
    def __init__(self):
        self.data = {}
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass

def get_db():
    return InMemoryDB()