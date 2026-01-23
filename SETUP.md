# Local Setup Guide for Digital Rename Bot

## Prerequisites

1. **Python 3.12+** (You have Python 3.12.10 ✓)
2. **MongoDB Database** - You can use:
   - Local MongoDB installation
   - MongoDB Atlas (free cloud database): https://cloud.mongodb.com
3. **FFmpeg** (for video processing)
4. **Telegram API Credentials**

## Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy your `API_ID` and `API_HASH`

## Step 2: Create a Telegram Bot

1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the `BOT_TOKEN` you receive

## Step 3: Get Your User ID

1. Search for @userinfobot on Telegram
2. Start a chat with it
3. Copy your User ID (it's a number)

## Step 4: Set Up MongoDB

### Option A: Use MongoDB Atlas (Recommended for beginners)

1. Go to https://cloud.mongodb.com
2. Create a free account
3. Create a new cluster (free tier is fine)
4. Click "Connect" → "Connect your application"
5. Copy the connection string
6. Replace `<password>` with your database password
7. This is your `DB_URL`

### Option B: Use Local MongoDB

1. Install MongoDB locally
2. Start MongoDB service
3. Use: `mongodb://localhost:27017` as your `DB_URL`

## Step 5: Install FFmpeg

### Windows:
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract and add to PATH, or
3. Use: `winget install ffmpeg` (if winget is available)

### Or use chocolatey:
```powershell
choco install ffmpeg
```

## Step 6: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` file and fill in all the required values:
   - `API_ID` - From Step 1
   - `API_HASH` - From Step 1
   - `BOT_TOKEN` - From Step 2
   - `ADMIN` - Your User ID from Step 3
   - `DB_URL` - From Step 4
   - `DB_NAME` - Keep as `Digital_Rename_Bot` or change if you want

## Step 7: Install Python Dependencies

Run:
```powershell
pip install -r requirements.txt
```

## Step 8: Run the Bot

Run:
```powershell
python bot.py
```

The bot should start and you'll see a message like "Digital Rename Bot Is Started.....✨️"

## Optional: Premium Features (4GB+ files)

If you want to support files larger than 4GB:

1. You need a Telegram Premium account
2. Generate a string session using a tool like:
   - https://replit.com/@SpEcHlDe/GenerateStringSession
   - Or use Pyrogram's string session generator
3. Add the `STRING_SESSION` to your `.env` file

## Troubleshooting

- **Import errors**: Make sure all dependencies are installed
- **MongoDB connection errors**: Check your `DB_URL` is correct
- **Bot not responding**: Check your `BOT_TOKEN` is correct
- **FFmpeg errors**: Make sure FFmpeg is installed and in PATH
