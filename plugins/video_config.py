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
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# bots imports
from helper.database import digital_botz
from config import Config

# Store setup state for each user
setup_states = {}

@Client.on_message(filters.private & filters.command("setup"))
async def setup_command(client, message):
    """Start the interactive setup process"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMIN:
        return await message.reply_text("❌ This command is only available for admins.")
    
    # Reset setup state
    setup_states[user_id] = {"step": "watermark"}
    
    # Start with watermark question
    await ask_watermark_question(client, message, user_id)

async def ask_watermark_question(client, message, user_id):
    """Ask if user wants to add watermark"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data="setup_watermark_yes")],
        [InlineKeyboardButton("❌ No", callback_data="setup_watermark_no")],
        [InlineKeyboardButton("❌ Cancel Setup", callback_data="setup_cancel")]
    ])
    
    text = "🔧 **Video Processing Setup**\n\n"
    text += "**Step 1/3: Watermark**\n\n"
    text += "Do you want to add a watermark to videos?\n"
    text += f"Current watermark text: `{Config.WATERMARK_TEXT}`"
    
    if message.text:
        await message.reply_text(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)

async def ask_sequence_question(client, message, user_id):
    """Ask if user wants to add sequence number"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data="setup_sequence_yes")],
        [InlineKeyboardButton("❌ No", callback_data="setup_sequence_no")],
        [InlineKeyboardButton("◀️ Back", callback_data="setup_back_watermark")],
        [InlineKeyboardButton("❌ Cancel Setup", callback_data="setup_cancel")]
    ])
    
    text = "🔧 **Video Processing Setup**\n\n"
    text += "**Step 2/3: Sequence Number**\n\n"
    text += "Do you want to add a sequence/count number in the caption?\n"
    text += "(e.g., 'Video 1', 'Video 2', etc.)"
    
    await message.edit_text(text, reply_markup=keyboard)

async def ask_thumbnail_question(client, message, user_id):
    """Ask which thumbnail to use"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ Default Cover Image", callback_data="setup_thumb_default")],
        [InlineKeyboardButton("🎬 Extract from Video", callback_data="setup_thumb_extract")],
        [InlineKeyboardButton("📷 Custom Thumbnail", callback_data="setup_thumb_custom")],
        [InlineKeyboardButton("◀️ Back", callback_data="setup_back_sequence")],
        [InlineKeyboardButton("❌ Cancel Setup", callback_data="setup_cancel")]
    ])
    
    text = "🔧 **Video Processing Setup**\n\n"
    text += "**Step 3/3: Thumbnail**\n\n"
    text += "Which thumbnail should be applied to videos?\n\n"
    text += "• **Default Cover Image**: Use `default_cover.jpg`\n"
    text += "• **Extract from Video**: Extract frame from video\n"
    text += "• **Custom Thumbnail**: Use your custom thumbnail"
    
    await message.edit_text(text, reply_markup=keyboard)

async def save_settings_and_complete(client, message, user_id):
    """Save all settings and complete setup"""
    if user_id not in setup_states:
        return
    
    state = setup_states[user_id]
    
    # Get current settings or create new
    settings = await digital_botz.get_video_settings(user_id)
    
    # Update settings from state
    settings['watermark_enabled'] = state.get('watermark_enabled', True)
    settings['sequence_enabled'] = state.get('sequence_enabled', True)
    settings['thumbnail_type'] = state.get('thumbnail_type', 'default')
    
    # Save to database
    await digital_botz.set_video_settings(user_id, settings)
    
    # Reset sequence counter
    await digital_botz.reset_video_sequence(user_id)
    
    # Clear setup state
    del setup_states[user_id]
    
    # Show summary
    watermark_status = "✅ Enabled" if settings['watermark_enabled'] else "❌ Disabled"
    sequence_status = "✅ Enabled" if settings['sequence_enabled'] else "❌ Disabled"
    thumb_map = {
        "default": "🖼️ Default Cover Image",
        "extract": "🎬 Extract from Video",
        "custom": "📷 Custom Thumbnail"
    }
    thumb_status = thumb_map.get(settings['thumbnail_type'], settings['thumbnail_type'])
    
    text = "✅ **Setup Complete!**\n\n"
    text += "**Your Video Processing Settings:**\n\n"
    text += f"• **Watermark**: {watermark_status}\n"
    text += f"• **Sequence Number**: {sequence_status}\n"
    text += f"• **Thumbnail**: {thumb_status}\n\n"
    text += "These settings will be applied to all videos you send.\n"
    text += "Use `/setup` to change settings anytime.\n"
    text += "Use `/reset_sequence` to reset the video counter."
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Change Settings", callback_data="setup_restart")]
    ])
    
    await message.edit_text(text, reply_markup=keyboard)

async def setup_callback_handler(client, query: CallbackQuery):
    """Handle setup callback queries"""
    try:
        user_id = query.from_user.id
        
        # Check if user is admin
        if user_id not in Config.ADMIN:
            await query.answer("❌ This is only available for admins.", show_alert=True)
            return
        
        data = query.data
        print(f"DEBUG: Setup callback received: {data} from user {user_id}")
        
        if data == "setup_cancel":
            if user_id in setup_states:
                del setup_states[user_id]
            await query.message.edit_text("❌ Setup cancelled.")
            await query.answer()
            return
        
        # Initialize state if not exists
        if user_id not in setup_states:
            setup_states[user_id] = {}
        
        state = setup_states[user_id]
        
        if data == "setup_watermark_yes":
            state['watermark_enabled'] = True
            state['step'] = "sequence"
            await query.answer("✅ Watermark enabled")
            await ask_sequence_question(client, query.message, user_id)
        
        elif data == "setup_watermark_no":
            state['watermark_enabled'] = False
            state['step'] = "sequence"
            await query.answer("❌ Watermark disabled")
            await ask_sequence_question(client, query.message, user_id)
        
        elif data == "setup_sequence_yes":
            state['sequence_enabled'] = True
            state['step'] = "thumbnail"
            await query.answer("✅ Sequence number enabled")
            await ask_thumbnail_question(client, query.message, user_id)
        
        elif data == "setup_sequence_no":
            state['sequence_enabled'] = False
            state['step'] = "thumbnail"
            await query.answer("❌ Sequence number disabled")
            await ask_thumbnail_question(client, query.message, user_id)
        
        elif data == "setup_thumb_default":
            state['thumbnail_type'] = "default"
            await query.answer("✅ Default cover image selected")
            await save_settings_and_complete(client, query.message, user_id)
        
        elif data == "setup_thumb_extract":
            state['thumbnail_type'] = "extract"
            await query.answer("✅ Extract from video selected")
            await save_settings_and_complete(client, query.message, user_id)
        
        elif data == "setup_thumb_custom":
            state['thumbnail_type'] = "custom"
            await query.answer("✅ Custom thumbnail selected")
            await save_settings_and_complete(client, query.message, user_id)
        
        elif data == "setup_back_watermark":
            state['step'] = "watermark"
            await query.answer("◀️ Going back...")
            await ask_watermark_question(client, query.message, user_id)
        
        elif data == "setup_back_sequence":
            state['step'] = "sequence"
            await query.answer("◀️ Going back...")
            await ask_sequence_question(client, query.message, user_id)
        
        elif data == "setup_restart":
            setup_states[user_id] = {"step": "watermark"}
            await query.answer("🔄 Restarting setup...")
            await ask_watermark_question(client, query.message, user_id)
        else:
            # Unknown setup callback
            print(f"DEBUG: Unknown setup callback: {data}")
            await query.answer("❌ Unknown action", show_alert=True)
    except Exception as e:
        print(f"ERROR in setup_callback_handler: {e}")
        import traceback
        traceback.print_exc()
        try:
            await query.answer("❌ An error occurred", show_alert=True)
        except:
            pass

@Client.on_message(filters.private & filters.command("reset_sequence"))
async def reset_sequence_command(client, message):
    """Reset video sequence counter"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMIN:
        return await message.reply_text("❌ This command is only available for admins.")
    
    await digital_botz.reset_video_sequence(user_id)
    await message.reply_text("✅ Video sequence counter has been reset to 0.\nNext video will be 'Video 1'.")

@Client.on_message(filters.private & filters.command("view_settings"))
async def view_settings_command(client, message):
    """View current video processing settings"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMIN:
        return await message.reply_text("❌ This command is only available for admins.")
    
    settings = await digital_botz.get_video_settings(user_id)
    
    watermark_status = "✅ Enabled" if settings.get('watermark_enabled', True) else "❌ Disabled"
    sequence_status = "✅ Enabled" if settings.get('sequence_enabled', True) else "❌ Disabled"
    thumb_map = {
        "default": "🖼️ Default Cover Image",
        "extract": "🎬 Extract from Video",
        "custom": "📷 Custom Thumbnail"
    }
    thumb_status = thumb_map.get(settings.get('thumbnail_type', 'default'), settings.get('thumbnail_type', 'default'))
    sequence_count = settings.get('video_sequence_counter', 0)
    
    text = "⚙️ **Current Video Processing Settings**\n\n"
    text += f"• **Watermark**: {watermark_status}\n"
    text += f"• **Sequence Number**: {sequence_status}\n"
    text += f"• **Thumbnail**: {thumb_status}\n"
    text += f"• **Current Sequence**: {sequence_count}\n\n"
    text += "Use `/setup` to change settings.\n"
    text += "Use `/reset_sequence` to reset counter."
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Change Settings", callback_data="setup_restart")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

# Note: We don't override /start here to avoid conflicts with start_and_cb.py
# Users can use /setup command to configure video processing settings

# Rkn Developer 
# Don't Remove Credit 😔
# Telegram Channel @RknDeveloper & @Rkn_Botz
# Developer @RknDeveloperr
# Update Channel @Digital_Botz & @DigitalBotz_Support
