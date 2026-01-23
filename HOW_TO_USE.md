# How to Use the Digital Rename Bot

## 📋 Step-by-Step Guide

### Step 1: Start the Bot
1. Open Telegram
2. Search for your bot (the username you created with @BotFather)
3. Send `/start` command
4. The bot should respond with a welcome message

### Step 2: Send a Video/File
1. **Send a video, audio, or document file** directly to the bot (in private chat)
2. The bot should respond with a message showing:
   - Old file name
   - File extension
   - File size
   - MIME type
   - DC ID
   - A request to enter the new filename

### Step 3: Reply with New Filename
1. **Reply to the bot's message** with your new filename
2. Format: `:-new_filename.ext`
   - Example: `:-my_video.mp4`
   - Example: `:-song.mp3`
   - Example: `:-document.pdf`
3. The bot will:
   - Download your file
   - Rename it
   - Upload it back to you

## ⚠️ Common Issues & Solutions

### Bot Not Responding?

1. **Check if Force Subscription is Enabled**
   - If `FORCE_SUB` is set in your `.env` file, you must join that channel first
   - The bot will send you a message asking you to join

2. **Check Bot Logs**
   - Look at `BotLog.txt` for any errors
   - Common errors:
     - Database connection issues
     - Invalid channel IDs
     - Missing permissions

3. **Make Sure You:**
   - Sent the file in a **private chat** with the bot (not in a group)
   - The file is a **video, audio, or document** (not a photo)
   - You've started the bot with `/start` first

4. **File Size Limits:**
   - Free users: Up to 2GB
   - Premium users: Up to 4GB+ (requires STRING_SESSION)

### Bot Asks for New Filename but Nothing Happens?

1. Make sure you **reply to the bot's message** (not send a new message)
2. Use the format: `:-new_filename.ext`
3. Wait for the bot to process (it may take time for large files)

## 🔧 Troubleshooting

### Check Bot Status
```powershell
# Check if bot is running
Get-Process python

# Check bot logs
Get-Content BotLog.txt -Tail 50
```

### Restart the Bot
1. Stop the bot (Ctrl+C if running in terminal)
2. Start again: `python bot.py`

### Test the Bot
1. Send `/start` - should get welcome message
2. Send a small video file - should get filename request
3. Reply with `:-test.mp4` - should process and send back

## 📝 Example Conversation

```
You: /start
Bot: Welcome message...

You: [Sends video file]
Bot: Media info:
     Old file name: video.mp4
     Extension: VIDEO
     File size: 50 MB
     Please enter the new filename...

You: :-my_new_video.mp4
Bot: [Downloads, renames, uploads]
     [Sends renamed file back]
```

## 🎯 Quick Test

1. Send `/start` to your bot
2. Send a small test video (under 10MB)
3. When bot asks for filename, reply: `:-test.mp4`
4. Wait for the bot to process and send it back

If this doesn't work, check the `BotLog.txt` file for errors!
