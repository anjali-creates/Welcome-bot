"""
🔥 EXTREME WELCOME BOT - ULTIMATE EDITION 🔥
✅ Full Member Tagging | ✅ Professional Welcome | ✅ Admin Control
"""

import logging
import asyncio
import os
import random
from datetime import datetime
from typing import List, Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = os.getenv('ADMIN_ID')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

BOT_OWNER_ID = int(BOT_OWNER_ID) if BOT_OWNER_ID else None

# ==================== EMOJIS ====================
WELCOME_EMOJIS = ["🎉", "🎊", "✨", "🌟", "⭐", "💫", "⚡", "🔥", "💥", "🎈", "🎀", "🎁", "🎂", "🍾", "🥳", "🤩", "😍", "🥰", "💖", "💝"]
USER_EMOJIS = ["👤", "🧑", "🙋", "🙌", "👋", "🤝", "💁", "🙆", "🙎", "💃", "🕺"]
TIME_EMOJIS = ["⏰", "🕐", "🕒", "🕔", "🕖", "🕘", "🕚", "⌚", "📅", "📆"]
ACTION_EMOJIS = ["✅", "❌", "⚠️", "🔔", "📢", "🔊", "🔈", "📣", "🎤"]
HEART_EMOJIS = ["💝", "💖", "💗", "💓", "💕", "💞", "💟", "❣️", "💔", "❤️", "🧡", "💛", "💚", "💙", "💜"]
STAR_EMOJIS = ["⭐", "🌟", "✨", "💫", "⚡", "🔥", "💥", "🎯", "🏆", "🎖️", "🏅", "🥇"]
ARROW_EMOJIS = ["➡️", "⬅️", "⬆️", "⬇️", "↗️", "↘️", "↙️", "↖️", "➰", "〰️"]

# ==================== STATS ====================
stats = {
    "total_welcomes": 0,
    "total_announcements": 0,
    "total_errors": 0,
    "groups": {},
    "start_time": datetime.now()
}

def random_emoji(emoji_list):
    return random.choice(emoji_list)

def format_number(num):
    return f"{num:,}"

async def send_to_owner(context, message):
    if BOT_OWNER_ID:
        try:
            await context.bot.send_message(chat_id=BOT_OWNER_ID, text=message, parse_mode='HTML')
        except:
            pass

async def get_user_profile_photo(user_id, context):
    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.photos:
            return photos.photos[0][-1].file_id
    except:
        pass
    return None

async def is_group_admin(chat_id, user_id, context):
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def get_group_members(chat_id, context):
    members = []
    try:
        async for member in context.bot.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user)
    except Exception as e:
        print(f"Error getting members: {e}")
    return members

# ==================== /all COMMAND ====================
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all members - Admin only"""
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    group_name = update.effective_chat.title
    
    if not await is_group_admin(chat_id, user_id, context):
        await update.message.reply_text(
            f"{random_emoji(ACTION_EMOJIS)} <b>ACCESS DENIED!</b>\n\n"
            f"This command is only for group administrators!",
            parse_mode='HTML'
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            f"<b>How to use /all:</b>\n\n"
            f"<code>/all Your message here</code>\n\n"
            f"<b>Example:</b>\n"
            f"<code>/all Hello everyone!</code>",
            parse_mode='HTML'
        )
        return
    
    message_text = ' '.join(context.args)
    
    processing_msg = await update.message.reply_text("⏳ Processing announcement...")
    
    try:
        members = await get_group_members(chat_id, context)
        
        if not members:
            await processing_msg.edit_text("❌ No members found!")
            return
        
        # Create tags for members (limit 50 per message)
        tags = []
        for member in members[:50]:
            tags.append(f"<a href='tg://user?id={member.id}'> </a>")
        
        announcement = f"""
{random_emoji(STAR_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(STAR_EMOJIS) * 8}

        {random_emoji(ACTION_EMOJIS)} 📢 GROUP ANNOUNCEMENT {random_emoji(ACTION_EMOJIS)}

{random_emoji(STAR_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(STAR_EMOJIS) * 8}

{random_emoji(USER_EMOJIS)} <b>Admin:</b> {user_name}
{random_emoji(HEART_EMOJIS)} <b>Group:</b> {group_name}
{random_emoji(TIME_EMOJIS)} <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
{random_emoji(STAR_EMOJIS)} <b>Members:</b> {len(members)}

{random_emoji(HEART_EMOJIS)} <b>MESSAGE:</b>
{random_emoji(ARROW_EMOJIS)} {message_text}

{''.join(tags)}

{random_emoji(STAR_EMOJIS)} <b>Please read carefully!</b> {random_emoji(STAR_EMOJIS)}

{random_emoji(HEART_EMOJIS) * 5} THANK YOU FOR YOUR ATTENTION! {random_emoji(HEART_EMOJIS) * 5}

{random_emoji(STAR_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(STAR_EMOJIS) * 8}
"""
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=announcement,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        stats["total_announcements"] += 1
        
        await processing_msg.delete()
        
        await update.message.reply_text(
            f"✅ Announcement sent!\n\n"
            f"👤 Members tagged: {len(members)}\n"
            f"💬 Message: {message_text[:50]}...",
            parse_mode='HTML'
        )
        
        if BOT_OWNER_ID:
            await send_to_owner(
                context,
                f"📢 /all COMMAND\n\n"
                f"Admin: {user_name}\n"
                f"Group: {group_name}\n"
                f"Members: {len(members)}\n"
                f"Message: {message_text[:100]}"
            )
            
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)[:100]}")
        stats["total_errors"] += 1

# ==================== WELCOME FUNCTION ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members"""
    
    if not update.message.new_chat_members:
        return
    
    chat = update.effective_chat
    chat_id = chat.id
    chat_title = chat.title
    
    try:
        bot_member = await chat.get_member(context.bot.id)
        is_bot_admin = bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_bot_admin = False
    
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            continue
        
        user_id = new_member.id
        user_name = new_member.full_name
        user_first = new_member.first_name or "Guest"
        user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
        username = f"@{new_member.username}" if new_member.username else "No username"
        
        profile_photo = await get_user_profile_photo(user_id, context)
        
        current_time = datetime.now().strftime("%I:%M:%S %p")
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        stats["total_welcomes"] += 1
        if chat_id not in stats["groups"]:
            stats["groups"][chat_id] = {"title": chat_title, "welcomes": 0}
        stats["groups"][chat_id]["welcomes"] += 1
        
        member_count = stats["groups"][chat_id]["welcomes"]
        
        # Welcome message without f-string issues
        welcome_msg = f"""
{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}

        {random_emoji(STAR_EMOJIS)} ✨ WELCOME TO THE FAMILY! ✨ {random_emoji(STAR_EMOJIS)}

{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}

┌─────────────────────────────────────────────────────────────────┐
│                    📋 MEMBER INFORMATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│        {random_emoji(USER_EMOJIS)}  Name       : {user_mention}                         │
│        🏷️  Username   : {username}                           │
│        🆔  User ID    : <code>{user_id}</code>                              │
│        {random_emoji(USER_EMOJIS)}  Group      : {chat_title}                           │
│        {random_emoji(TIME_EMOJIS)}  Time       : {current_time}                         │
│        📅  Date       : {current_date}                         │
│        📊  Member #   : {member_count}                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    💝 WELCOME NOTE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎉 Dear {user_first}, 🎉                                       │
│                                                                 │
│  ✨ A very warm welcome to our amazing community! ✨            │
│                                                                 │
│  🌟 We're so excited to have you here! 🌟                       │
│                                                                 │
│  💫 Feel free to introduce yourself! 💫                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}

                    {random_emoji(STAR_EMOJIS)} ENJOY YOUR STAY! {random_emoji(STAR_EMOJIS)}

{random_emoji(WELCOME_EMOJIS) * 8}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 8}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📜 RULES", url="https://t.me/telegram"),
                InlineKeyboardButton("💬 INTRO", url=f"tg://user?id={user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if is_bot_admin and profile_photo:
                await update.message.reply_photo(
                    photo=profile_photo,
                    caption=welcome_msg,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    welcome_msg,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as e:
            await update.message.reply_text(
                f"🎉✨ WELCOME {user_mention} ✨🎉\n\n🌟 To {chat_title} 🌟\n\n💫 We're glad to have you!",
                parse_mode='HTML'
            )
        
        if BOT_OWNER_ID:
            await send_to_owner(
                context,
                f"🎉 NEW MEMBER!\n\n"
                f"Name: {user_name}\n"
                f"ID: {user_id}\n"
                f"Group: {chat_title}\n"
                f"Time: {current_time}"
            )

# ==================== START COMMAND ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"""
🤖 <b>WELCOME BOT IS ACTIVE!</b> 🤖

✨ <b>Features:</b>
• 🎉 Professional Welcome Messages
• 👤 Profile Photo Display
• 📢 /all Command - Tag Everyone
• 👑 Group Admin Only Commands

<b>Commands:</b>
/all &lt;message&gt; - Tag all members (Admin only)
/start - Show this message

💡 <b>Add me to any group!</b>
""",
        parse_mode='HTML'
    )

# ==================== STATS COMMAND ====================
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if BOT_OWNER_ID and update.effective_user.id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Only bot owner can use this command!")
        return
    
    uptime = datetime.now() - stats["start_time"]
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    stats_msg = f"""
📊 <b>BOT STATISTICS</b>

📈 <b>Performance:</b>
• Uptime: {hours}h {minutes}m
• Total Welcomes: {stats['total_welcomes']}
• Total Announcements: {stats['total_announcements']}
• Total Errors: {stats['total_errors']}
• Active Groups: {len(stats['groups'])}

✨ Bot is running perfectly!
"""
    await update.message.reply_text(stats_msg, parse_mode='HTML')

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats["total_errors"] += 1
    print(f"Error: {context.error}")
    
    if BOT_OWNER_ID:
        await send_to_owner(context, f"⚠️ Error: {str(context.error)[:100]}")

# ==================== SETUP COMMANDS ====================
async def setup_commands(application: Application):
    commands = [
        BotCommand("start", "Show bot information"),
        BotCommand("help", "Show help message"),
        BotCommand("all", "Tag all members (Admin only)"),
    ]
    if BOT_OWNER_ID:
        commands.append(BotCommand("stats", "View bot statistics"))
    await application.bot.set_my_commands(commands)

# ==================== HELP COMMAND ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"""
📚 <b>BOT COMMANDS</b>

👥 <b>General Commands:</b>
/start - Show bot information
/help - Show this help message

👑 <b>Admin Commands (Group Admins Only):</b>
/all &lt;message&gt; - Tag all members with announcement

📝 <b>Example:</b>
<code>/all Hello everyone! Important announcement!</code>

⚠️ <b>Note:</b>
• /all command only works in groups
• Only group admins can use /all
• Use responsibly - don't spam
""",
        parse_mode='HTML'
    )

# ==================== MAIN ====================
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(CommandHandler("all", all_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    if BOT_OWNER_ID:
        application.add_handler(CommandHandler("stats", stats_command))
    application.add_error_handler(error_handler)
    application.post_init = setup_commands
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     🔥 WELCOME BOT - EXTREME EDITION 🔥                        ║
    ║     ✅ /all command tags all members                           ║
    ║     ✅ Professional welcome message                            ║
    ║     ✅ Profile photo display                                   ║
    ║     🚀 BOT IS RUNNING!                                         ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
