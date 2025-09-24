"""
데이터베이스 연결 및 세션 관리
"""
import os
import logging
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    데이터베이스 매니저
    
    연결 풀과 세션 관리
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20
    ):
        """
        초기화
        
        Args:
            database_url: 데이터베이스 URL
            echo: SQL 로깅 여부
            pool_size: 연결 풀 크기
            max_overflow: 최대 오버플로우
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/hybrid_crawler"
        )
        
        # SQLite인 경우 pool 설정 조정
        if self.database_url.startswith("sqlite"):
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                echo=echo
            )
        else:
            # PostgreSQL 등 다른 DB
            self.engine = create_engine(
                self.database_url,
                poolclass=pool.QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # 연결 체크
                echo=echo
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """비밀번호를 숨긴 URL 반환"""
        if "@" in self.database_url:
            parts = self.database_url.split("@")
            return parts[0].split("://")[0] + "://***@" + parts[1]
        return self.database_url
    
    def create_tables(self):
        """테이블 생성"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """테이블 삭제"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """세션 생성"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        세션 컨텍스트 매니저
        
        자동으로 커밋/롤백 처리
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """엔진 종료"""
        self.engine.dispose()
        logger.info("Database connection closed")
    
    def health_check(self) -> bool:
        """헬스 체크"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# 글로벌 데이터베이스 매니저
_db_manager: Optional[DatabaseManager] = None


def init_db(
    database_url: Optional[str] = None,
    create_tables: bool = True,
    echo: bool = False
) -> DatabaseManager:
    """
    데이터베이스 초기화
    
    Args:
        database_url: 데이터베이스 URL
        create_tables: 테이블 생성 여부
        echo: SQL 로깅
    
    Returns:
        DatabaseManager 인스턴스
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(
            database_url=database_url,
            echo=echo
        )
        
        if create_tables:
            _db_manager.create_tables()
    
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성용 데이터베이스 세션
    
    Yields:
        데이터베이스 세션
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = init_db()
    
    db = _db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


def close_db():
    """데이터베이스 연결 종료"""
    global _db_manager
    
    if _db_manager:
        _db_manager.close()
        _db_manager = None


# 테스트용 SQLite 설정
def get_test_db(
    db_path: str = "test.db",
    echo: bool = False
) -> DatabaseManager:
    """
    테스트용 데이터베이스
    
    Args:
        db_path: SQLite 파일 경로
        echo: SQL 로깅
    
    Returns:
        테스트 DatabaseManager
    """
    database_url = f"sqlite:///{db_path}"
    
    manager = DatabaseManager(
        database_url=database_url,
        echo=echo
    )
    manager.create_tables()
    
    return manager
