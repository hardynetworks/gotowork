"""Application configuration."""
import secrets
from pathlib import Path


class Settings:
    """App settings."""
    
    # Application
    APP_NAME = "Crew Scheduler"
    DEBUG = True
    
    # Database
    DATABASE_URL = "postgresql://admin:password123@localhost:5432/crew_scheduler"
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    
    # Redis
    REDIS_URL = "redis://localhost:6379/0"
    
    # Authentication
    SECRET_KEY = secrets.token_hex(32)
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Scheduling Rules (can be overridden via admin)
    SHIFT_LENGTH_HOURS = 8
    MAX_SHIFTS_PER_DAY = 1
    MIN_BREAK_MINUTES = 30
    MAX_WEEKLY_HOURS = 40
    MAX_CONSECUTIVE_DAYS = 5
    REQUIRED_COVERAGE_FACTOR = 1.2  # 20% buffer for absences
    
    @classmethod
    def get(cls):
        """Get settings singleton."""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance


settings = Settings.get()