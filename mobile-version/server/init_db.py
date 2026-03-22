#!/usr/bin/env python3
"""
Initialize the Mail Agent database.
Creates all required tables for the multi-user email automation system.
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import init_db

def main():
    """Initialize database and create tables."""
    print("=" * 60)
    print("🧪 Mail Agent Database Initialization")
    print("=" * 60)
    
    try:
        # Initialize database (creates tables if they don't exist)
        init_db()
        
        print("\n✅ Database initialized successfully!")
        print("\n📊 Created tables:")
        print("   • summaries - Email summaries for users")
        print("   • user_configs - Cached user configurations")
        
        print("\n🚀 Next steps:")
        print("   1. Configure server.yaml with your API keys")
        print("   2. Start API server: python sync_api.py")
        print("   3. Start worker: python worker.py")
        print("   4. Users can now sync from mobile app")
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
