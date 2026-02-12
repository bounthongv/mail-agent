import streamlit as st
import pandas as pd
import sys
import os
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import EmailAccount, Summary

# Set page config for mobile/tablet feel
st.set_page_config(page_title="Mail Agent Mobile", page_icon="📧", layout="wide")

# Ensure database is initialized
init_db()

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Sidebar for Navigation
st.sidebar.title("📧 Mail Agent")
menu = st.sidebar.radio("Navigation", ["Dashboard", "My Accounts", "Settings"])

db = SessionLocal()

if menu == "Dashboard":
    st.title("Today's Summaries")
    
    # Load summaries from DB
    summaries = db.query(Summary).order_by(Summary.received_at.desc()).all()
    
    if not summaries:
        st.info("No summaries found yet. Make sure your agent is running!")
    else:
        for s in summaries:
            with st.expander(f"**From:** {s.sender} | **Subject:** {s.subject}"):
                st.write(s.summary_text)
                st.caption(f"Received: {s.received_at}")

elif menu == "My Accounts":
    st.title("Connected Email Accounts")
    
    # Add new account form
    with st.expander("➕ Add New Account"):
        with st.form("add_account"):
            email = st.text_input("Email Address")
            password = st.text_input("App Password", type="password")
            telegram_id = st.text_input("Telegram Chat ID (to receive summaries)")
            
            st.markdown("---")
            st.subheader("Filter Patterns (One per line)")
            trusted = st.text_area("Trusted Senders (Skip AI check)")
            spam = st.text_area("Spam Keywords (Move to Spam)")
            
            host = st.text_input("IMAP Host", value="imap.gmail.com")
            port = st.number_input("IMAP Port", value=993)
            
            if st.form_submit_button("Save Account"):
                new_acc = EmailAccount(
                    email=email, 
                    password=password, 
                    telegram_chat_id=telegram_id,
                    trusted_senders=trusted,
                    spam_keywords=spam,
                    imap_host=host, 
                    imap_port=port
                )
                db.add(new_acc)
                db.commit()
                st.success(f"Added {email} successfully!")
                st.rerun()

    # List existing accounts
    accounts = db.query(EmailAccount).all()
    if accounts:
        df = pd.DataFrame([
            {"Email": a.email, "Host": a.imap_host, "Enabled": a.enabled}
            for a in accounts
        ])
        st.table(df)
        
        # Simple delete functionality
        email_to_del = st.selectbox("Select email to remove", [a.email for a in accounts])
        if st.button("Delete Account", type="primary"):
            acc = db.query(EmailAccount).filter(EmailAccount.email == email_to_del).first()
            db.delete(acc)
            db.commit()
            st.warning(f"Deleted {email_to_del}")
            st.rerun()

elif menu == "Settings":
    st.title("System Settings")
    st.write("Current AI Provider: **Gemini (Cloud)**")
    st.write("Status: **Healthy**")
    
db.close()
