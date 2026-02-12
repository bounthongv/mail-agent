from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class EmailAccount(Base):
    __tablename__ = 'email_accounts'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    imap_host = Column(String, default='imap.gmail.com')
    imap_port = Column(Integer, default=993)
    telegram_chat_id = Column(String, nullable=True) # Per-user telegram
    
    # Store patterns as comma-separated strings or JSON in the DB
    trusted_senders = Column(Text, default="")
    spam_keywords = Column(Text, default="")
    delete_keywords = Column(Text, default="")
    
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Summary(Base):
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('email_accounts.id'))
    sender = Column(String)
    subject = Column(String)
    summary_text = Column(Text)
    received_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
