"""
Sync API for Mail Agent Mobile App
===================================
This API receives user config from mobile devices and returns summaries.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import json
import os
import sys

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import Summary, UserConfig

app = FastAPI(title="Mail Agent Sync API", version="2.0")

# Enable CORS for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Pydantic Models ===

class EmailAccount(BaseModel):
    email: str
    password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    enabled: bool = True

class PatternConfig(BaseModel):
    trusted_senders: List[str] = []
    spam_keywords: List[str] = []
    delete_keywords: List[str] = []

class UserConfigSync(BaseModel):
    user_id: str
    telegram_chat_id: str
    emails: List[EmailAccount]
    patterns: PatternConfig
    last_sync_time: Optional[datetime] = None
    device_id: Optional[str] = None

class SummaryResponse(BaseModel):
    id: int
    sender: str
    subject: str
    summary_text: str
    received_at: datetime
    created_at: datetime

class SyncResponse(BaseModel):
    status: str
    message: str
    summaries: List[SummaryResponse]
    summaries_count: int

# === API Endpoints ===

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Mail Agent Sync API", "version": "2.0"}

@app.get("/health")
def health():
    """Alias for health check"""
    return {"status": "healthy"}

@app.post("/sync", response_model=SyncResponse)
def sync_config(config: UserConfigSync, db: Session = Depends(get_db)):
    """
    Main sync endpoint:
    1. Save/update user config in database
    2. Save to disk (user_configs/user_id.yaml)
    3. Return new summaries since last sync
    """
    try:
        # 1. Update or create user config in database
        user_config = db.query(UserConfig).filter(
            UserConfig.user_id == config.user_id
        ).first()
        
        config_json = json.dumps(config.model_dump(), default=str)
        
        if user_config:
            user_config.config_json = config_json
            user_config.last_sync = datetime.utcnow()
            user_config.updated_at = datetime.utcnow()
            user_config.is_active = True
        else:
            user_config = UserConfig(
                user_id=config.user_id,
                config_json=config_json,
                last_sync=datetime.utcnow()
            )
            db.add(user_config)
        
        db.commit()
        
        # 2. Save to disk
        save_config_to_disk(config.user_id, config.model_dump())
        
        # 3. Get new summaries since last sync
        last_sync = config.last_sync_time or datetime.utcnow() - timedelta(days=7)
        
        summaries = db.query(Summary).filter(
            Summary.user_id == config.user_id,
            Summary.created_at > last_sync
        ).order_by(Summary.created_at.desc()).limit(50).all()
        
        # Mark as synced for this device
        for s in summaries:
            s.synced = True
            s.device_id = config.device_id
        db.commit()
        
        summary_responses = [
            SummaryResponse(
                id=s.id,
                sender=s.sender,
                subject=s.subject,
                summary_text=s.summary_text,
                received_at=s.received_at,
                created_at=s.created_at
            ) for s in summaries
        ]
        
        return SyncResponse(
            status="success",
            message=f"Config synced. Found {len(summaries)} new summaries.",
            summaries=summary_responses,
            summaries_count=len(summaries)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summaries/{user_id}", response_model=List[SummaryResponse])
def get_summaries(
    user_id: str, 
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get summaries for a user from last N hours"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    summaries = db.query(Summary).filter(
        Summary.user_id == user_id,
        Summary.created_at > since
    ).order_by(Summary.created_at.desc()).all()
    
    return [
        SummaryResponse(
            id=s.id,
            sender=s.sender,
            subject=s.subject,
            summary_text=s.summary_text,
            received_at=s.received_at,
            created_at=s.created_at
        ) for s in summaries
    ]

@app.delete("/config/{user_id}")
def delete_user_config(user_id: str, db: Session = Depends(get_db)):
    """Delete user config (for account deletion)"""
    user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
    if user_config:
        db.delete(user_config)
        db.commit()
        
        # Also delete from disk
        config_file = get_config_path(user_id)
        if os.path.exists(config_file):
            os.remove(config_file)
        
        return {"status": "deleted", "user_id": user_id}
    return {"status": "not_found", "user_id": user_id}

# === Helper Functions ===

def get_config_path(user_id: str) -> str:
    """Get path to user config file"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, 'user_configs')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, f"{user_id}.yaml")

def save_config_to_disk(user_id: str, config: dict) -> None:
    """Save user config to YAML file on disk"""
    import yaml
    config_path = get_config_path(user_id)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Saved config for {user_id} to {config_path}")

# === Run Server ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
