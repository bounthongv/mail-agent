from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import bcrypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    person_id = Column(String, unique=True, nullable=False, index=True)  # Unique identifier
    password_hash = Column(String, nullable=False)  # Hashed password
    is_first_login = Column(Boolean, default=True)  # Force password change on first login
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    # Relationships
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")

class EmailAccount(Base):
    __tablename__ = 'email_accounts'
    id = Column(Integer, primary_key=True)
    person_id = Column(String, nullable=False, index=True)  # From .env USERS_CONFIG
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Link to User table
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    imap_host = Column(String, default='imap.gmail.com')
    imap_port = Column(Integer, default=993)
    telegram_chat_id = Column(String, nullable=True)
    
    # Store patterns as comma-separated strings
    trusted_senders = Column(Text, default="")
    spam_keywords = Column(Text, default="")
    delete_keywords = Column(Text, default="")
    
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="email_accounts")
    summaries = relationship("Summary", back_populates="account", cascade="all, delete-orphan")

class Summary(Base):
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('email_accounts.id'))
    person_id = Column(String, nullable=False, index=True)  # For quick person-based queries
    sender = Column(String)
    subject = Column(String)
    summary_text = Column(Text)
    received_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    account = relationship("EmailAccount", back_populates="summaries")
