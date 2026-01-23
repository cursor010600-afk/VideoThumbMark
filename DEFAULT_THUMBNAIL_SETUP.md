# Default Thumbnail (Cover Photo) Setup

## Overview
The bot now uses a default cover image for all processed videos. When you upload a video, it will use this image as the thumbnail instead of extracting one from the video.

## Setup Instructions

### Step 1: Save Your Image
1. Save your cover image (the promotional image with @Coursesbuying) to:
   ```
   Thumbnails/default_cover.jpg
   ```

2. **Supported formats**: JPG, JPEG, PNG
   - If your image is PNG, save it as `default_cover.png` and update the path in `.env`

### Step 2: Configure (Optional)
If you want to use a different path or filename, add this to your `.env` file:
```env
DEFAULT_THUMBNAIL=Thumbnails/default_cover.jpg
```

### Step 3: Restart the Bot
After saving the image, restart your bot:
```powershell
python bot.py
```

## How It Works
- When a video is uploaded, the bot will:
  1. Download the video
  2. Add watermark (@Coursesbuying)
  3. Use your default cover image as the thumbnail
  4. Upload the processed video with your custom cover photo

- If the default thumbnail file doesn't exist, the bot will automatically extract a thumbnail from the video as a fallback.

## Image Requirements
- **Recommended size**: 320x320 pixels or larger (will be auto-resized)
- **Format**: JPG, JPEG, or PNG
- **File size**: Keep it under 200KB for best performance

## Troubleshooting
- **Image not showing?** Check that the file path is correct and the file exists
- **Wrong size?** The bot automatically resizes to 320x320, so any size will work
- **Format error?** Make sure the image is a valid JPG/PNG file
