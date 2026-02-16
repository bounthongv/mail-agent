"""
REST API for Mail Agent Flutter App.
Run this on your Ubuntu server to provide data to the Flutter Face.
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import sys
import os

# Add app directory to path to reuse DB models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import Summary, EmailAccount
from pydantic import BaseModel

app = FastAPI(title="Mail Agent API")

# Initialize DB on startup
init_db()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models for JSON response ---
class SummaryResponse(BaseModel):
    id: int
    sender: str
    subject: str
    summary_text: str
    received_at: str

    class Config:
        from_attributes = True

class AccountCreate(BaseModel):
    email: str
    password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    telegram_chat_id: str = ""

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "Mail Agent API is online"}

@app.get("/summaries", response_model=List[SummaryResponse])
def get_summaries(db: Session = Depends(get_db)):
    """Fetch all summaries from the database."""
    summaries = db.query(Summary).order_by(Summary.received_at.desc()).all()
    
    # Format dates to string for JSON compatibility
    results = []
    for s in summaries:
        results.append({
            "id": s.id,
            "sender": s.sender,
            "subject": s.subject,
            "summary_text": s.summary_text,
            "received_at": s.received_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return results

@app.post("/accounts")
def add_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Add a new email account from Flutter."""
    db_account = EmailAccount(
        email=account.email,
        password=account.password,
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        telegram_chat_id=account.telegram_chat_id,
        enabled=True
    )
    try:
        db.add(db_account)
        db.commit()
        return {"status": "success", "message": f"Account {account.email} added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Run on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
