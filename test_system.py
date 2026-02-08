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
    config = load_config()
    print(f"   Email(s): {', '.join([e.email for e in config.emails])}")
    print(f"   Telegram Chat ID: {config.telegram.chat_id}")
    print(f"   Primary AI: {config.ai.provider} ({config.ai.model})")
    if config.localai.enabled:
        print(f"   Backup AI: {config.localai.provider} ({config.localai.model})")


if __name__ == "__main__":
    print("="*50)
    print("Mail Agent - System Verification")
    print("="*50)
    
    test_config()
    test_summary()
    
    print("\n" + "="*50)
    print("Configuration verified! System is ready.")
    print("="*50)
