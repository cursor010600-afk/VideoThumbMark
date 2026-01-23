#!/usr/bin/env python3
"""
Helper script to update BOT_TOKEN in .env file
Usage: python update_bot_token.py YOUR_BOT_TOKEN
"""

import sys
import os

def update_bot_token(token):
    """Update BOT_TOKEN in .env file"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"❌ Error: {env_file} file not found!")
        return False
    
    # Read the file
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update the BOT_TOKEN line
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith('BOT_TOKEN='):
            new_lines.append(f'BOT_TOKEN={token}\n')
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        # Add it if it doesn't exist
        new_lines.append(f'BOT_TOKEN={token}\n')
    
    # Write back
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ Successfully updated BOT_TOKEN in {env_file}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_bot_token.py YOUR_BOT_TOKEN")
        print("\nExample:")
        print("  python update_bot_token.py 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
        sys.exit(1)
    
    token = sys.argv[1]
    if update_bot_token(token):
        print("\n✓ Bot token updated! You can now run: python run_local.py")
    else:
        sys.exit(1)
