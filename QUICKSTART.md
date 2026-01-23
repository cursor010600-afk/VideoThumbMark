# Quick Start Guide

## ✅ What's Already Done

1. ✓ Python dependencies installed
2. ✓ python-dotenv installed (for .env file support)
3. ✓ Run scripts created

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Your Telegram Credentials

1. **API_ID & API_HASH**: Go to https://my.telegram.org/apps
   - Log in and create an app
   - Copy your `API_ID` and `API_HASH`

2. **BOT_TOKEN**: Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy the `BOT_TOKEN` you receive

3. **Your User ID**: Message @userinfobot on Telegram
   - It will reply with your User ID (a number)

### Step 2: Set Up MongoDB

**Option A: MongoDB Atlas (Free Cloud - Recommended)**
1. Go to https://cloud.mongodb.com
2. Create free account → Create free cluster
3. Click "Connect" → "Connect your application"
4. Copy the connection string
5. Replace `<password>` with your database password
6. This is your `DB_URL`

**Option B: Local MongoDB**
- Install MongoDB locally
- Use: `mongodb://localhost:27017` as `DB_URL`

### Step 3: Create .env File

1. Copy `env_template.txt` to `.env`:
   ```powershell
   copy env_template.txt .env
   ```

2. Open `.env` in a text editor and fill in:
   - `API_ID` - from Step 1
   - `API_HASH` - from Step 1  
   - `BOT_TOKEN` - from Step 1
   - `ADMIN` - your User ID from Step 1
   - `DB_URL` - from Step 2
   - `DB_NAME` - keep as `Digital_Rename_Bot` or change

### Step 4: Install FFmpeg (Required for video processing)

**Windows:**
```powershell
# Option 1: Using winget (if available)
winget install ffmpeg

# Option 2: Using chocolatey
choco install ffmpeg

# Option 3: Manual download
# Download from: https://www.gyan.dev/ffmpeg/builds/ 
# Extract and add to PATH
```

### Step 5: Run the Bot

```powershell
python run_local.py
```

Or use the batch file:
```powershell
.\run.bat
```

Or use PowerShell script:
```powershell
.\run.ps1
```

## 🎉 That's It!

The bot should start and you'll see: `Digital Rename Bot Is Started.....✨️`

Test it by messaging your bot on Telegram!

## 📝 Optional: Premium Features (4GB+ files)

If you want to support files larger than 4GB:
1. You need a Telegram Premium account
2. Generate a string session (search for "Pyrogram string session generator")
3. Add `STRING_SESSION` to your `.env` file

## ❓ Troubleshooting

- **"Missing required environment variables"**: Check your `.env` file
- **MongoDB connection error**: Verify your `DB_URL` is correct
- **Bot not responding**: Check `BOT_TOKEN` is correct
- **FFmpeg errors**: Make sure FFmpeg is installed and in PATH

For more details, see `SETUP.md`
