# Video Watermark Bot Setup

## ✅ What's Been Configured

Your bot now automatically:
1. **Adds watermark** "@Coursesbuying" to all videos
2. **Extracts thumbnail** from the video automatically
3. **Processes videos** without asking for filename

## 🎯 How It Works

### For Videos:
1. User sends a video to the bot
2. Bot automatically:
   - Downloads the video
   - Adds watermark "@Coursesbuying" (bottom-right corner)
   - Extracts thumbnail from the video
   - Uploads the processed video back

### For Other Files (Audio/Documents):
- Original rename functionality still works

## ⚙️ Configuration

Watermark settings are in `.env`:
```
WATERMARK_TEXT=@Coursesbuying
WATERMARK_POSITION=bottom-right
```

### Watermark Position Options:
- `top-left` - Top left corner
- `top-right` - Top right corner  
- `bottom-left` - Bottom left corner
- `bottom-right` - Bottom right corner (default)
- `center` - Center of video

## 🚀 Usage

1. **Start the bot:**
   ```powershell
   python bot.py
   ```

2. **Send a video** to your bot in Telegram
3. Bot will automatically:
   - Process it
   - Add watermark
   - Extract thumbnail
   - Send it back

## 📝 Example

```
You: [Sends video.mp4]
Bot: 📥 Downloading video...
     🎨 Adding watermark @Coursesbuying...
     🖼️ Extracting thumbnail...
     📤 Uploading processed video...
     ✅ Video processed successfully!
     ✨ Watermark added: @Coursesbuying
     🖼️ Thumbnail extracted
```

## 🔧 Customization

To change the watermark text or position, edit `.env`:
```env
WATERMARK_TEXT=@YourUsername
WATERMARK_POSITION=top-right
```

Then restart the bot.

## ⚠️ Notes

- Watermark is added using FFmpeg
- Processing time depends on video size
- Original video is kept temporarily, then deleted after processing
- Thumbnail is extracted from 1 second into the video

## 🐛 Troubleshooting

If watermark doesn't appear:
1. Check FFmpeg is installed: `ffmpeg -version`
2. Check bot logs: `Get-Content BotLog.txt`
3. Make sure video format is supported (MP4, AVI, MOV, etc.)
