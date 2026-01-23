# (c) @RknDeveloperr
# Rkn Developer 
# Don't Remove Credit 😔
# Telegram Channel @RknDeveloper & @Rkn_Botz
# Developer @RknDeveloperr
# Special Thanks To @ReshamOwner
# Update Channel @Digital_Botz & @DigitalBotz_Support
"""
Apache License 2.0
Copyright (c) 2022 @Digital_Botz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Telegram Link : https://t.me/Digital_Botz 
Repo Link : https://github.com/DigitalBotz/Digital-Rename-Bot
License Link : https://github.com/DigitalBotz/Digital-Rename-Bot/blob/main/LICENSE
"""

# pyrogram imports
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.file_id import FileId
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

# hachoir imports
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

# bots imports
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix, remove_path
from helper.database import digital_botz
from helper.ffmpeg import change_metadata, add_watermark, extract_thumbnail
from config import Config

# extra imports
from asyncio import sleep
import os, time, asyncio, re, threading


UPLOAD_TEXT = """Uploading Started...."""
DOWNLOAD_TEXT = """Download Started..."""

app = Client("4gb_FileRenameBot", api_id=Config.API_ID, api_hash=Config.API_HASH, session_string=Config.STRING_SESSION)

# Global queue system for sequential processing
user_queues = {}  # {user_id: [messages]}
user_processing = {}  # {user_id: bool}
queue_lock = threading.Lock()

async def process_user_queue(client, user_id):
    """Process videos sequentially from user's queue"""
    while True:
        # Get next message from queue
        with queue_lock:
            if not user_queues.get(user_id):
                user_processing[user_id] = False
                break
            message = user_queues[user_id].pop(0)
        
        # Process the video
        await process_single_video(client, message)

async def process_single_video(client, message):
    """
    Process a single video with watermark, thumbnail, and caption
    """
    user_id = message.from_user.id
    
    # Get user's video processing settings
    settings = await digital_botz.get_video_settings(user_id)
    watermark_enabled = settings.get('watermark_enabled', True)
    sequence_enabled = settings.get('sequence_enabled', True)
    thumbnail_type = settings.get('thumbnail_type', 'default')
    
    # Get and increment video sequence counter (per user, from database)
    # Always increment for all forwarded videos
    video_count = await digital_botz.increment_video_sequence(user_id)
    
    rkn_file = getattr(message, message.media.value)
    original_filename = rkn_file.file_name or ""
    # If no filename or default "video.mp4", treat as no filename
    if not original_filename or original_filename.lower() in ["video.mp4", "video"]:
        filename = ""  # Will be handled in caption logic
    else:
        filename = original_filename
    filesize = humanbytes(rkn_file.file_size)
    
    # Create processing message
    rkn_processing = await message.reply_text("`📥 Downloading video...`")
    
    # Create directories in /tmp for cloud storage
    if not os.path.isdir("/tmp/Watermarked"):
        os.makedirs("/tmp/Watermarked", exist_ok=True)
    if not os.path.isdir("/tmp/Thumbnails"):
        os.makedirs("/tmp/Thumbnails", exist_ok=True)
    
    # Download video with unique timestamp to prevent file conflicts
    # Use message ID + timestamp for guaranteed uniqueness
    unique_id = f"{message.id}_{int(time.time() * 1000)}"
    download_filename = filename if filename else f"video_{video_count}.mp4"
    download_path = f"/tmp/Watermarked/temp_{unique_id}.mp4"
    try:
        dl_path = await client.download_media(
            message=message, 
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading...", rkn_processing, time.time())
        )
    except Exception as e:
        return await rkn_processing.edit(f"❌ Download Error: {e}")
    
    # Small delay to ensure file handles are released (prevents WinError 32 on Windows)
    await asyncio.sleep(0.3)
    
    # Process video based on settings
    final_video_path = dl_path  # Default to downloaded video
    
    # Add watermark if enabled
    if watermark_enabled:
        watermark_path = f"/tmp/Watermarked/watermarked_{unique_id}.mp4"
        if await add_watermark(dl_path, watermark_path, Config.WATERMARK_TEXT, Config.WATERMARK_POSITION, rkn_processing):
            final_video_path = watermark_path
        else:
            await rkn_processing.edit("❌ Failed to add watermark. Continuing without watermark...")
            final_video_path = dl_path
    else:
        # No watermark, use downloaded video directly
        final_video_path = dl_path
    
    # Process thumbnail based on settings
    await rkn_processing.edit("`🖼️ Setting cover photo...`")
    ph_path = None
    ph_path_abs = None
    
    if thumbnail_type == "default":
        # Use default cover image
        default_path = Config.DEFAULT_THUMBNAIL
        print(f"DEBUG: Checking default thumbnail at: {default_path}, exists={os.path.exists(default_path)}")
        
        if os.path.exists(default_path):
            try:
                print(f"DEBUG: Processing default thumbnail...")
                img = Image.open(default_path).convert("RGB")
                try:
                    img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                except AttributeError:
                    img.thumbnail((320, 320), Image.ANTIALIAS)
                processed_thumb = f"/tmp/Thumbnails/default_processed_{int(time.time())}.jpg"
                # Use optimal quality from start (85 is good balance of quality and size)
                img.save(processed_thumb, "JPEG", quality=85, optimize=True, progressive=True)
                ph_path = processed_thumb
                print(f"DEBUG: Created processed thumbnail: {processed_thumb}, size={os.path.getsize(processed_thumb)} bytes, quality=85")
            except Exception as e:
                print(f"ERROR processing default thumbnail: {e}")
                import traceback
                traceback.print_exc()
                ph_path = default_path if os.path.exists(default_path) else None
                print(f"DEBUG: Falling back to raw default: {ph_path}")
        else:
            print(f"DEBUG: Default thumbnail not found, falling back to extract from video...")
            # Fallback: Extract thumbnail from video
            thumb_path = f"/tmp/Thumbnails/thumb_{unique_id}.jpg"
            if await extract_thumbnail(final_video_path, thumb_path):
                ph_path = thumb_path if os.path.exists(thumb_path) else None
                print(f"DEBUG: Extracted thumbnail from video: {ph_path}")
    
    elif thumbnail_type == "extract":
        # Extract thumbnail from video
        thumb_path = f"/tmp/Thumbnails/thumb_{unique_id}.jpg"
        if await extract_thumbnail(final_video_path, thumb_path):
            ph_path = thumb_path if os.path.exists(thumb_path) else None
            print(f"DEBUG: Extracted thumbnail from video: {ph_path}")
    
    elif thumbnail_type == "custom":
        # Use user's custom thumbnail from database
        custom_thumb_id = await digital_botz.get_thumbnail(user_id)
        if custom_thumb_id:
            # Download custom thumbnail
            try:
                thumb_path = f"/tmp/Thumbnails/custom_{user_id}_{int(time.time())}.jpg"
                await client.download_media(custom_thumb_id, file_name=thumb_path)
                if os.path.exists(thumb_path):
                    # Process to meet Telegram requirements
                    img = Image.open(thumb_path).convert("RGB")
                    try:
                        img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                    except AttributeError:
                        img.thumbnail((320, 320), Image.ANTIALIAS)
                    processed_thumb = f"/tmp/Thumbnails/custom_processed_{user_id}_{int(time.time())}.jpg"
                    # Use optimal quality from start
                    img.save(processed_thumb, "JPEG", quality=85, optimize=True, progressive=True)
                    ph_path = processed_thumb
                    print(f"DEBUG: Using custom thumbnail: {ph_path}")
            except Exception as e:
                print(f"ERROR downloading custom thumbnail: {e}")
                # Fallback to extract from video
                thumb_path = f"/tmp/Thumbnails/{download_filename}.jpg"
                if await extract_thumbnail(final_video_path, thumb_path):
                    ph_path = thumb_path if os.path.exists(thumb_path) else None
    
    # Get absolute path for thumbnail
    if ph_path and os.path.exists(ph_path):
        ph_path_abs = os.path.abspath(ph_path)
        print(f"DEBUG: Using thumbnail: {ph_path_abs}")
    
    # Get video duration
    duration = 0
    try:
        parser = createParser(final_video_path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get('duration').seconds
        if parser:
            parser.close()
    except:
        pass
    
    # Build caption based on settings
    original_caption = message.caption or ""
    caption_text = re.sub(r'@\w+', '', original_caption).strip()
    
    # Always add sequence number
    if not caption_text:
        # No caption: Video X @Coursesbuying
        final_caption = f"Video {video_count} @Coursesbuying"
    else:
        # Has caption: Video X\n[caption]\n@Coursesbuying
        final_caption = f"Video {video_count}\n{caption_text}\n@Coursesbuying"
    
    # Upload video
    await rkn_processing.edit("`📤 Uploading processed video...`")
    
    try:
        print(f"DEBUG: Sending video: {final_video_path}, caption={final_caption}, thumb={ph_path_abs}")
        await client.send_video(
            user_id,
            video=final_video_path,
            thumb=ph_path_abs if ph_path_abs else None,
            caption=final_caption,
            duration=duration,
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", rkn_processing, time.time())
        )
        print(f"DEBUG: Video sent successfully!")
        
        # Success message
        success_parts = []
        if watermark_enabled:
            success_parts.append("✨ Watermark added")
        # Always show sequence number
        success_parts.append(f"🔢 Sequence: {video_count}")
        if ph_path_abs:
            success_parts.append("🖼️ Thumbnail set")
        
        success_msg = "✅ **Video processed successfully!**"
        if success_parts:
            success_msg += "\n\n" + "\n".join(success_parts)
        
        await rkn_processing.edit(success_msg)
    except Exception as e:
        await rkn_processing.edit(f"❌ Upload Error: {e}")
    
    # Cleanup temp files - aggressive cleanup for cloud deployment
    try:
        if os.path.exists(dl_path) and dl_path != final_video_path:
            os.remove(dl_path)
            print(f"Cleaned up download file: {dl_path}")
        if os.path.exists(final_video_path) and watermark_enabled:
            # Clean up watermarked file after upload
            os.remove(final_video_path)
            print(f"Cleaned up watermarked file: {final_video_path}")
        if ph_path and os.path.exists(ph_path) and ph_path.startswith("/tmp/Thumbnails/default_processed_"):
            os.remove(ph_path)
            print(f"Cleaned up processed thumbnail: {ph_path}")
        if ph_path and os.path.exists(ph_path) and ph_path.startswith("/tmp/Thumbnails/custom_processed_"):
            os.remove(ph_path)
            print(f"Cleaned up custom processed thumbnail: {ph_path}")
        if ph_path and os.path.exists(ph_path) and ph_path.startswith("/tmp/Thumbnails/custom_") and not ph_path.startswith("/tmp/Thumbnails/custom_processed_"):
            os.remove(ph_path)
            print(f"Cleaned up custom thumbnail: {ph_path}")
        if ph_path and os.path.exists(ph_path) and ph_path.startswith("/tmp/Thumbnails/thumb_"):
            os.remove(ph_path)
            print(f"Cleaned up extracted thumbnail: {ph_path}")
    except Exception as e:
        print(f"ERROR during cleanup: {e}")

@Client.on_message(filters.private & filters.video)
async def rename_start(client, message):
    """
    Add videos to queue for sequential processing
    """
    user_id = message.from_user.id
    
    # Add to queue
    with queue_lock:
        if user_id not in user_queues:
            user_queues[user_id] = []
        user_queues[user_id].append(message)
        queue_size = len(user_queues[user_id])
        
        # Start processor if not already running
        if not user_processing.get(user_id, False):
            user_processing[user_id] = True
            asyncio.create_task(process_user_queue(client, user_id))
    
    # Notify user about queue position (only if there are other videos in queue)
    if queue_size > 1:
        await message.reply_text(f"📋 **Added to queue**\n\nPosition: {queue_size}\n\nYour video will be processed in order.")

@Client.on_message(filters.private & (filters.audio | filters.document))
async def rename_start_other(client, message):
    """Handle non-video files (original rename functionality)"""
    user_id  = message.from_user.id
    rkn_file = getattr(message, message.media.value)
    filename = rkn_file.file_name
    filesize = humanbytes(rkn_file.file_size)
    mime_type = rkn_file.mime_type
    dcid = FileId.decode(rkn_file.file_id).dc_id
    extension_type = mime_type.split('/')[0]

    if client.premium and client.uploadlimit:
        await digital_botz.reset_uploadlimit_access(user_id)
        user_data = await digital_botz.get_user_data(user_id)
        if user_data is None:
            # If user_data is None, create default values
            limit = Config.FREE_UPLOAD_LIMIT
            used = 0
        else:
            limit = user_data.get('uploadlimit', Config.FREE_UPLOAD_LIMIT)
            used = user_data.get('used_limit', 0)
        remain = int(limit) - int(used)
        used_percentage = int(used) / int(limit) * 100 if int(limit) > 0 else 0
        if remain < int(rkn_file.file_size):
            return await message.reply_text(f"{used_percentage:.2f}% Of Daily Upload Limit {humanbytes(limit)}.\n\n Media Size: {filesize}\n Your Used Daily Limit {humanbytes(used)}\n\nYou have only **{humanbytes(remain)}** Data.\nPlease, Buy Premium Plan s.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪪 Uᴘɢʀᴀᴅᴇ", callback_data="plans")]]))
         
    if await digital_botz.has_premium_access(user_id) and client.premium:
        if not Config.STRING_SESSION:
            if rkn_file.file_size > 2000 * 1024 * 1024:
                 return await message.reply_text("Sᴏʀʀy Bʀᴏ Tʜɪꜱ Bᴏᴛ Iꜱ Dᴏᴇꜱɴ'ᴛ Sᴜᴩᴩᴏʀᴛ Uᴩʟᴏᴀᴅɪɴɢ Fɪʟᴇꜱ Bɪɢɢᴇʀ Tʜᴀɴ 2Gʙ+")

        try:
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )       
            await asyncio.sleep(30)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )
        except Exception as e:
            print(f"Error in rename_start: {e}")
    else:
        # Regular (non-premium) users
        if rkn_file.file_size > 2000 * 1024 * 1024 and client.premium:
            return await message.reply_text("If you want to rename 4GB+ files then you will have to buy premium. /plans")
        
        # For regular users, also ask for filename
        try:
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )       
            await asyncio.sleep(30)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )
        except Exception as e:
            print(f"Error in rename_start (regular user): {e}")

        try:
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )       
            await asyncio.sleep(30)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )
        except Exception as e:
            print(f"Error in rename_start (non-premium): {e}")


@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        button = [[InlineKeyboardButton("📁 Dᴏᴄᴜᴍᴇɴᴛ",callback_data = "upload#document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Vɪᴅᴇᴏ", callback_data = "upload#video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Aᴜᴅɪᴏ", callback_data = "upload#audio")])
        await message.reply(
            text=f"**Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Fɪʟᴇ Tyᴩᴇ**\n**• Fɪʟᴇ Nᴀᴍᴇ :-**`{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )

async def upload_files(bot, sender_id, upload_type, file_path, ph_path, caption, duration, rkn_processing):
    """
    Unified function to upload files based on type
    - Supports both 2GB and 4GB files
    - Uses same function for all file sizes
    - Handles document, video, and audio files
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
            
        # Upload document files (2GB & 4GB)
        if upload_type == "document":
            filw = await bot.send_document(
                sender_id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=(UPLOAD_TEXT, rkn_processing, time.time()))
        
        # Upload video files (2GB & 4GB)  
        elif upload_type == "video":
            filw = await bot.send_video(
                sender_id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=(UPLOAD_TEXT, rkn_processing, time.time()))
        
        # Upload audio files (2GB & 4GB)
        elif upload_type == "audio":
            filw = await bot.send_audio(
                sender_id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=(UPLOAD_TEXT, rkn_processing, time.time()))
        else:
            return None, f"Unknown upload type: {upload_type}"
        
        # Return uploaded file object
        return filw, None
        
    except Exception as e:
        # Return error if upload fails
        return None, str(e)


#@Client.on_callback_query(filters.regex("upload"))
async def upload_doc(bot, update):
    rkn_processing = await update.message.edit("`Processing...`")
    
    # Creating Directory for Metadata in /tmp
    if not os.path.isdir("/tmp/Metadata"):
        os.makedirs("/tmp/Metadata", exist_ok=True)

    user_id = int(update.message.chat.id) 
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]
    user_data = await digital_botz.get_user_data(user_id)

    try:
        # adding prefix and suffix
        prefix = user_data.get('prefix', None) if user_data else None
        suffix = user_data.get('suffix', None) if user_data else None
        new_filename = await add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await rkn_processing.edit(f"⚠️ Something went wrong can't able to set Prefix or Suffix ☹️ \n\n❄️ Contact My Creator -> @RknDeveloperr\nError: {e}")

    # msg file location 
    file = update.message.reply_to_message
    media = getattr(file, file.media.value)
    
    # File paths for download and metadata in /tmp
    file_path = f"/tmp/Renames/{new_filename}"
    metadata_path = f"/tmp/Metadata/{new_filename}"

    await rkn_processing.edit("`Try To Download....`")
    if bot.premium and bot.uploadlimit and user_data:
        limit = user_data.get('uploadlimit', 0)
        used = user_data.get('used_limit', 0)        
        total_used = int(used) + int(media.file_size)
        await digital_botz.set_used_limit(user_id, total_used)
    
    try:            
        dl_path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=(DOWNLOAD_TEXT, rkn_processing, time.time()))                    
    except Exception as e:
        if bot.premium and bot.uploadlimit:
            used_remove = int(used) - int(media.file_size)
            await digital_botz.set_used_limit(user_id, used_remove)
        return await rkn_processing.edit(f"Download Error: {e}")

    # Check if it's a video file and add watermark automatically
    is_video = file.media == MessageMediaType.VIDEO or (hasattr(file, 'video') and file.video)
    
    if is_video:
        # Add watermark to video
        await rkn_processing.edit("`Adding watermark...`")
        watermark_path = f"/tmp/Watermarked/{new_filename}"
        
        # Create directory if it doesn't exist
        if not os.path.isdir("/tmp/Watermarked"):
            os.makedirs("/tmp/Watermarked", exist_ok=True)
        
        if await add_watermark(dl_path, watermark_path, Config.WATERMARK_TEXT, Config.WATERMARK_POSITION):
            await rkn_processing.edit("`Watermark added! Extracting thumbnail...`")
            # Extract thumbnail from watermarked video
            thumb_path = f"/tmp/Thumbnails/{new_filename}.jpg"
            if not os.path.isdir("/tmp/Thumbnails"):
                os.makedirs("/tmp/Thumbnails", exist_ok=True)
            
            if await extract_thumbnail(watermark_path, thumb_path):
                # Use watermarked video and extracted thumbnail
                file_path = watermark_path
                ph_path = thumb_path if os.path.exists(thumb_path) else None
            else:
                # If thumbnail extraction fails, use watermarked video but no custom thumbnail
                file_path = watermark_path
                ph_path = None
        else:
            # If watermark fails, use original file
            await rkn_processing.edit("`Watermark failed, using original video...`")
            file_path = dl_path
            ph_path = None
    else:
        file_path = dl_path
        ph_path = None

    metadata_mode = await digital_botz.get_metadata_mode(user_id)
    if metadata_mode:        
        metadata = await digital_botz.get_metadata_code(user_id)
        if metadata:
            await rkn_processing.edit("I Fᴏᴜɴᴅ Yᴏᴜʀ Mᴇᴛᴀᴅᴀᴛᴀ\n\n__**Pʟᴇᴀsᴇ Wᴀɪᴛ...**__\n**Aᴅᴅɪɴɢ Mᴇᴛᴀᴅᴀᴛᴀ Tᴏ Fɪʟᴇ....**")            
            if await change_metadata(dl_path, metadata_path, metadata):            
                await rkn_processing.edit("Metadata Added.....")
                print("Metadata Added.....")
            else:
                await rkn_processing.edit("Failed to add metadata, uploading original file...")
                metadata_mode = False
        else:
            await rkn_processing.edit("No metadata found, uploading original file...")
            metadata_mode = False
    else:
        await rkn_processing.edit("`Try To Uploading....`")
        
    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get('duration').seconds
        if parser:
            parser.close()
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        pass
        
    ph_path = None
    c_caption = user_data.get('caption', None) if user_data else None
    c_thumb = user_data.get('file_id', None) if user_data else None

    if c_caption:
         try:
             # adding custom caption 
             caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
         except Exception as e:
             if bot.premium and bot.uploadlimit:
                 used_remove = int(used) - int(media.file_size)
                 await digital_botz.set_used_limit(user_id, used_remove)
             return await rkn_processing.edit(text=f"Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ Exᴄᴇᴩᴛ Kᴇyᴡᴏʀᴅ Aʀɢᴜᴍᴇɴᴛ ●> ({e})")             
    else:
         caption = f"**{new_filename}**"
 
    if (media.thumbs or c_thumb):
         # downloading thumbnail path
         try:
             if c_thumb:
                 ph_path = await bot.download_media(c_thumb) 
             else:
                 ph_path = await bot.download_media(media.thumbs[0].file_id)
             
             if ph_path and os.path.exists(ph_path):
                 Image.open(ph_path).convert("RGB").save(ph_path)
                 img = Image.open(ph_path)
                 img.resize((320, 320))
                 img.save(ph_path, "JPEG")
         except Exception as e:
             print(f"Error processing thumbnail: {e}")
             ph_path = None

    upload_type = update.data.split("#")[1]
    
    # Use the correct file path based on metadata mode
    final_file_path = metadata_path if metadata_mode and os.path.exists(metadata_path) else file_path
    
    if media.file_size > 2000 * 1024 * 1024:
        # Upload file using unified function for large files
        filw, error = await upload_files(
            app, Config.LOG_CHANNEL, upload_type, final_file_path, 
            ph_path, caption, duration, rkn_processing
        )

        if error:
            if bot.premium and bot.uploadlimit:
                used_remove = int(used) - int(media.file_size)
                await digital_botz.set_used_limit(user_id, used_remove)
            await remove_path(ph_path, file_path, dl_path, metadata_path)
            return await rkn_processing.edit(f"Upload Error: {error}")

        
        from_chat = filw.chat.id
        mg_id = filw.id
        await asyncio.sleep(2)
        await bot.copy_message(update.from_user.id, from_chat, mg_id)
        await bot.delete_messages(from_chat, mg_id)
        
    else:
        # Upload file using unified function for regular files
        filw, error = await upload_files(
            bot, update.message.chat.id, upload_type, final_file_path, 
            ph_path, caption, duration, rkn_processing
        )
                   
        if error:
            if bot.premium and bot.uploadlimit:
                used_remove = int(used) - int(media.file_size)
                await digital_botz.set_used_limit(user_id, used_remove)
            await remove_path(ph_path, file_path, dl_path, metadata_path)
            return await rkn_processing.edit(f"Upload Error: {error}")        

    # Clean up files
    await remove_path(ph_path, file_path, dl_path, metadata_path)
    return await rkn_processing.edit("Uploaded Successfully....")



# @RknDeveloper
# ✅ Team-RknDeveloper
# Rkn Developer 
# Don't Remove Credit 😔
# Telegram Channel @RknDeveloper & @Rkn_Botz
# Developer @RknDeveloperr
# Special Thanks To @ReshamOwner
# Update Channel @Digital_Botz & @DigitalBotz_Support
