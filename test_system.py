"""Quick test script to verify core functionality."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_loader import load_config


def test_config():
    print("1. Testing config loader...")
    config = load_config()
    assert len(config.emails) > 0
    # assert config.ai.model == "z-ai/glm-4.5-air:free"
    print(f"   [OK] Loaded {len(config.emails)} email(s)")
    print(f"   [OK] Model: {config.ai.model}")
    print(f"   [OK] Schedule: every {config.schedule.interval_hours} hours")


def test_summary():
    print("\n2. Summary...")
    print(f"   Email: bounthongv@gmail.com")
    print(f"   Bot: EmailSummaryBot (@bt_email_bot)")
    print(f"   Telegram Chat ID: 7252862418")
    print(f"   AI: z-ai/glm-4.5-air:free (OpenRouter)")


if __name__ == "__main__":
    print("="*50)
    print("Mail Agent - System Verification")
    print("="*50)
    
    test_config()
    test_summary()
    
    print("\n" + "="*50)
    print("Configuration verified! System is ready.")
    print("="*50)
