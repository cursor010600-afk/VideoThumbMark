#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local run script for Digital Rename Bot
This script loads environment variables from .env file and runs the bot
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Loaded environment variables from .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed. Install it with: pip install python-dotenv")
    print("[WARNING] Or set environment variables manually before running.")
    print("[WARNING] Continuing with system environment variables...\n")

# Check required environment variables
required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "ADMIN", "DB_URL"]
missing_vars = []

for var in required_vars:
    if not os.environ.get(var):
        missing_vars.append(var)

if missing_vars:
    print("[ERROR] Missing required environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\nPlease set these in your .env file or as environment variables.")
    print("See SETUP.md for instructions.")
    sys.exit(1)

print("[OK] All required environment variables are set")
print("Starting bot...\n")

# Import and run the bot
if __name__ == "__main__":
    try:
        from bot import main
        main()
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Bot stopped by user!")
    except Exception as e:
        print(f"\n[ERROR] Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
