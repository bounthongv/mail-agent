#!/usr/bin/env python3
"""Configuration validation script for multi-user Mail Agent."""

import json
import os
from dotenv import load_dotenv

def validate_config():
    """Validate .env configuration."""
    print("🔍 Validating Mail Agent Configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check API keys
    print("\n📱 API Keys:")
    api_keys = {
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'HUGGINGFACE_API_KEY': os.getenv('HUGGINGFACE_API_KEY'),
        'NVIDIA_API_KEY': os.getenv('NVIDIA_API_KEY'),
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN')
    }
    
    for key, value in api_keys.items():
        status = "✅" if value and value.strip() else "❌"
        print(f"  {status} {key}: {'Set' if value else 'Missing'}")
    
    # Check AI URLs
    print("\n🌐 AI Service URLs:")
    ai_urls = {
        'WINDOWS_AI_URL': os.getenv('WINDOWS_AI_URL'),
        'UBUNTU_AI_URL': os.getenv('UBUNTU_AI_URL')
    }
    
    for key, value in ai_urls.items():
        status = "✅" if value and value.strip() else "⚠️"
        print(f"  {status} {key}: {value if value else 'Using default'}")
    
    # Validate USERS_CONFIG
    print("\n👥 Multi-User Configuration:")
    users_config_str = os.getenv('USERS_CONFIG', '[]')
    
    try:
        users_config = json.loads(users_config_str)
        print(f"  ✅ Valid JSON format")
        print(f"  📊 Found {len(users_config)} users")
        
        total_emails = 0
        for i, user in enumerate(users_config, 1):
            print(f"\n    User {i}:")
            print(f"      🆔 User ID: {user.get('user_id', 'Missing!')}")
            print(f"      💬 Telegram Chat ID: {user.get('telegram_chat_id', 'Missing!')}")
            
            emails = user.get('emails', [])
            total_emails += len(emails)
            print(f"      📧 Email accounts: {len(emails)}")
            
            for j, email in enumerate(emails, 1):
                email_addr = email.get('email', 'Missing!')
                password_set = "✅" if email.get('password') else "❌"
                host = email.get('imap_host', 'Default')
                port = email.get('imap_port', 'Default')
                enabled = "✅" if email.get('enabled', True) else "❌"
                print(f"        {j}. {email_addr} ({password_set} password)")
                print(f"           Server: {host}:{port} | Enabled: {enabled}")
            
            # Check patterns
            patterns = user.get('patterns', {})
            if patterns:
                print(f"      🎯 Patterns:")
                for pattern_type, pattern_value in patterns.items():
                    if pattern_value:
                        print(f"        {pattern_type}: {len(str(pattern_value).split(','))} items")
                    else:
                        print(f"        {pattern_type}: Not configured")
        
        print(f"\n📈 Total email accounts across all users: {total_emails}")
        
        if total_emails == 0:
            print("  ⚠️ Warning: No email accounts configured!")
            return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error parsing users config: {e}")
        return False

def main():
    """Main validation function."""
    print("=" * 60)
    print("🧪 Mail Agent Configuration Validator")
    print("=" * 60)
    
    if validate_config():
        print("\n✅ Configuration looks good!")
        print("\n🚀 Next steps:")
        print("   1. Run: python3 init_db.py")
        print("   2. Start worker: python3 worker.py")
        print("   3. Open dashboard: streamlit run dashboard.py")
    else:
        print("\n❌ Configuration has issues!")
        print("   Please fix the errors above before running the agent.")

if __name__ == "__main__":
    main()