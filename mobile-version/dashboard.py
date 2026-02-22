import streamlit as st
import pandas as pd
import sys
import os
import threading
from sqlalchemy.orm import Session
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import EmailAccount, Summary, User
from worker import run_worker

# Set page config
st.set_page_config(page_title="Mail Agent Mobile", page_icon="📧", layout="wide")

# Ensure database is initialized
init_db()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'person_id' not in st.session_state:
    st.session_state['person_id'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'show_password_change' not in st.session_state:
    st.session_state['show_password_change'] = False

# Start background worker if not running
if 'worker_started' not in st.session_state:
    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()
    st.session_state['worker_started'] = True

def get_db():
    return SessionLocal()

def login():
    """Authentication screen"""
    st.title("📧 Mail Agent Login")
    st.markdown("---")
    
    with st.form("login_form"):
        person_id = st.text_input("User ID (Person ID)")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            db = get_db()
            try:
                user = db.query(User).filter(User.person_id == person_id).first()
                if user and user.check_password(password):
                    st.session_state['authenticated'] = True
                    st.session_state['person_id'] = person_id
                    st.session_state['user_id'] = user.id
                    st.session_state['show_password_change'] = user.is_first_login
                    
                    # Update last login
                    user.last_login = datetime.utcnow()
                    db.commit()
                    
                    st.rerun()
                else:
                    st.error("Invalid User ID or Password")
            except Exception as e:
                st.error(f"Login error: {e}")
            finally:
                db.close()

def change_password():
    """Force password change on first login"""
    st.title("🔐 Change Password")
    st.warning("This is your first login. Please change your password.")
    st.markdown("---")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Password"):
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                db = get_db()
                try:
                    user = db.query(User).filter(User.id == st.session_state['user_id']).first()
                    if user and user.check_password(current_password):
                        user.set_password(new_password)
                        user.is_first_login = False
                        db.commit()
                        st.session_state['show_password_change'] = False
                        st.success("Password updated successfully!")
                        st.rerun()
                    else:
                        st.error("Current password is incorrect")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    db.close()

def logout():
    """Clear session"""
    st.session_state['authenticated'] = False
    st.session_state['person_id'] = None
    st.session_state['user_id'] = None
    st.session_state['show_password_change'] = False
    st.rerun()

# MAIN APPLICATION LOGIC
if not st.session_state['authenticated']:
    login()
else:
    # Check if password change required
    if st.session_state['show_password_change']:
        change_password()
    else:
        # AUTHENTICATED USER INTERFACE
        
        # Sidebar with user info and navigation
        st.sidebar.title(f"📧 Mail Agent")
        st.sidebar.markdown(f"**User:** `{st.session_state['person_id']}`")
        st.sidebar.markdown("---")
        
        menu = st.sidebar.radio("Navigation", ["Dashboard", "My Accounts", "Settings"])
        
        st.sidebar.markdown("---")
        st.sidebar.button("🚪 Logout", on_click=logout)
        
        db = get_db()
        person_id = st.session_state['person_id']
        user_id = st.session_state['user_id']
        
        try:
            if menu == "Dashboard":
                st.title("Today's Summaries")
                
                # Filter by current user only
                summaries = db.query(Summary).filter(
                    Summary.person_id == person_id
                ).order_by(Summary.received_at.desc()).all()
                
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
                        delete = st.text_area("Delete Keywords (Move to Trash)")
                        
                        host = st.text_input("IMAP Host", value="imap.gmail.com")
                        port = st.number_input("IMAP Port", value=993)
                        
                        if st.form_submit_button("Save Account"):
                            try:
                                new_acc = EmailAccount(
                                    person_id=person_id,
                                    user_id=user_id,
                                    email=email, 
                                    password=password, 
                                    telegram_chat_id=telegram_id,
                                    trusted_senders=trusted,
                                    spam_keywords=spam,
                                    delete_keywords=delete,
                                    imap_host=host, 
                                    imap_port=port
                                )
                                db.add(new_acc)
                                db.commit()
                                st.success(f"Added {email} successfully!")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Error adding account: {e}")
                
                # List user's accounts only
                accounts = db.query(EmailAccount).filter(
                    EmailAccount.person_id == person_id
                ).all()
                
                if accounts:
                    st.subheader("Your Accounts")
                    df = pd.DataFrame([
                        {"Email": a.email, "Host": a.imap_host, "Enabled": a.enabled}
                        for a in accounts
                    ])
                    st.table(df)
                    
                    # Delete user's own account
                    st.markdown("---")
                    email_to_del = st.selectbox("Select email to remove", [a.email for a in accounts])
                    if st.button("Delete Account", type="primary"):
                        try:
                            acc = db.query(EmailAccount).filter(
                                EmailAccount.email == email_to_del,
                                EmailAccount.person_id == person_id  # Security: only delete own
                            ).first()
                            if acc:
                                db.delete(acc)
                                db.commit()
                                st.warning(f"Deleted {email_to_del}")
                                st.rerun()
                            else:
                                st.error("Account not found")
                        except Exception as e:
                            db.rollback()
                            st.error(f"Error deleting: {e}")
                else:
                    st.info("No accounts configured yet. Add one above!")
            
            elif menu == "Settings":
                st.title("System Settings")
                
                # User Settings
                st.subheader("Your Settings")
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    st.write(f"**User ID:** {user.person_id}")
                    st.write(f"**Last Login:** {user.last_login or 'Never'}")
                    
                    # Password change option
                    with st.expander("🔐 Change Password"):
                        with st.form("settings_change_password"):
                            current_pwd = st.text_input("Current Password", type="password")
                            new_pwd = st.text_input("New Password", type="password")
                            confirm_pwd = st.text_input("Confirm Password", type="password")
                            
                            if st.form_submit_button("Update"):
                                if new_pwd != confirm_pwd:
                                    st.error("Passwords don't match")
                                elif len(new_pwd) < 6:
                                    st.error("Password must be at least 6 characters")
                                elif not user.check_password(current_pwd):
                                    st.error("Current password is incorrect")
                                else:
                                    try:
                                        user.set_password(new_pwd)
                                        db.commit()
                                        st.success("Password updated!")
                                    except Exception as e:
                                        db.rollback()
                                        st.error(f"Error: {e}")
                
                st.markdown("---")
                
                # Global System Info
                st.subheader("System Status")
                account_count = db.query(EmailAccount).filter(
                    EmailAccount.person_id == person_id
                ).count()
                summary_count = db.query(Summary).filter(
                    Summary.person_id == person_id
                ).count()
                
                st.write(f"**Your Email Accounts:** {account_count}")
                st.write(f"**Your Summaries:** {summary_count}")
                st.write("**AI Provider:** Cloud AI (Ollama → Gemini Fallback)")
                st.write("**Status:** ✅ Running")
                
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            db.close()
