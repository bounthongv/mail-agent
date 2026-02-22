from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()

class Summary(Base):
    """Stores email summaries for users to sync"""
    __tablename__ = 'summaries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    sender = Column(String)
    subject = Column(String)
    summary_text = Column(Text)
    received_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced = Column(Boolean, default=False)  # Track if user has synced this
    device_id = Column(String, nullable=True)  # Which device synced (for multi-device)
    
    @staticmethod
    def is_expired(created_at: datetime, retention_days: int = 30) -> bool:
        """Check if summary is older than retention period"""
        return datetime.utcnow() - created_at > timedelta(days=retention_days)


class UserConfig(Base):
    """Cached user configuration from mobile devices"""
    __tablename__ = 'user_configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False, index=True)
    config_json = Column(Text, nullable=False)  # JSON string of full config
    last_sync = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
