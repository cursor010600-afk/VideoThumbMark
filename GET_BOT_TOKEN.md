# How to Get Your Bot Token

## Quick Steps:

1. **Open Telegram** and search for **@BotFather**

2. **Start a chat** with @BotFather

3. **Send the command**: `/newbot`

4. **Follow the prompts**:
   - Choose a name for your bot (e.g., "My Rename Bot")
   - Choose a username for your bot (must end with "bot", e.g., "my_rename_bot")

5. **Copy the token** that @BotFather gives you
   - It will look like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

6. **Update your .env file**:
   - Open `.env` in a text editor
   - Replace `your_bot_token_here` with the token you got
   - Save the file

7. **Run the bot**:
   ```powershell
   python run_local.py
   ```

## Alternative: If you already have a bot

If you already created a bot before:
1. Message @BotFather
2. Send `/mybots`
3. Select your bot
4. Click "API Token"
5. Copy the token and update your `.env` file
