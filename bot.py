import logging
import asyncio
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = os.getenv('ADMIN_ID')  # Bot owner ID for notifications

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found!")

BOT_OWNER_ID = int(BOT_OWNER_ID) if BOT_OWNER_ID else None

# ==================== EMOJIS ====================
WELCOME_EMOJIS = ["🎉", "🎊", "✨", "🌟", "⭐", "💫", "⚡", "🔥", "💥", "🎈", "🎀", "🎁", "🎂", "🍾", "🥳", "🤩", "😍", "🥰", "💖", "💝"]
USER_EMOJIS = ["👤", "🧑", "🙋", "🙌", "👋", "🤝", "💁"]
TIME_EMOJIS = ["⏰", "🕐", "🕒", "🕔", "🕖", "🕘", "⌚", "📅"]
ACTION_EMOJIS = ["✅", "❌", "⚠️", "🔔", "📢", "🔊"]
HEART_EMOJIS = ["💝", "💖", "💗", "💓", "💕", "💞"]
STAR_EMOJIS = ["⭐", "🌟", "✨", "💫", "⚡", "🔥", "💥", "🎯"]

# ==================== ANIMATION GIFS ====================
ANIMATION_GIFS = [
    "https://media4.giphy.com/media/3o7abB06u9bNzA8LC8/giphy.gif",
    "https://media2.giphy.com/media/l0MYEqEzwMWFCg8rO/giphy.gif",
    "https://media1.giphy.com/media/26n6WywJyh39n1pBu/giphy.gif",
    "https://media3.giphy.com/media/3o6ZtaO9BZHcOjmErm/giphy.gif",
]

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== STATS ====================
stats = {"total_welcomes": 0, "groups": set()}

def random_emoji(emoji_list):
    return random.choice(emoji_list)

async def send_to_bot_owner(context, message):
    """Send notification to bot owner only"""
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
    """Check if user is admin in the specific group"""
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

# ==================== /all COMMAND - GROUP ADMIN KE LIYE ====================
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all members - Group Admin can use this"""
    
    # Check if in group
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    # Check if user is admin of THIS GROUP
    is_admin = await is_group_admin(chat_id, user_id, context)
    
    if not is_admin:
        await update.message.reply_text("""
╔══════════════════════════════════════╗
║  ❌ 𝐀𝐂𝐂𝐄𝐒𝐒 𝐃𝐄𝐍𝐈𝐄𝐃! ❌              ║
╚══════════════════════════════════════╝

🔒 <b>This command is only for group admins!</b>

👑 <b>You need to be an admin of this group to use /all</b>

💡 Contact group admin to send announcements
""", parse_mode='HTML')
        return
    
    # Check if message is provided
    if not context.args:
        await update.message.reply_text("""
📝 <b>How to use /all:</b>

<code>/all Your message here</code>

<b>Example:</b>
<code>/all Hello everyone! Welcome to the group!</code>

⚠️ <b>Note:</b> Only group admins can use this command
""", parse_mode='HTML')
        return
    
    message_text = ' '.join(context.args)
    group_name = update.effective_chat.title
    admin_name = user_name
    
    # Send announcement with professional design
    announcement = f"""
╔══════════════════════════════════════════════════════════════╗
║              📢 𝐆𝐑𝐎𝐔𝐏 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓 📢                    ║
╚══════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────┐
│  👑 <b>Admin:</b> {admin_name}                                 │
│  🏠 <b>Group:</b> {group_name}                                 │
│  🕐 <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}       │
│  📅 <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  💬 <b>MESSAGE:</b>                                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  {message_text}                                              │
│                                                               │
└──────────────────────────────────────────────────────────────┘

✨ <b>Please read the above announcement carefully!</b> ✨

{random_emoji(STAR_EMOJIS) * 5} <b>THANK YOU FOR YOUR ATTENTION!</b> {random_emoji(STAR_EMOJIS) * 5}
"""
    
    try:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=announcement, 
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        await update.message.reply_text(f"""
✅ <b>𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓 𝐒𝐄𝐍𝐓 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘!</b> ✅

📊 <b>Details:</b>
• 👑 Admin: {admin_name}
• 🏠 Group: {group_name}
• 💬 Message: {message_text[:50]}...
• 🕐 Time: {datetime.now().strftime('%I:%M:%S %p')}

✨ Announcement has been sent to the group!
""", parse_mode='HTML')
        
        # Notify bot owner (optional)
        if BOT_OWNER_ID:
            await send_to_bot_owner(context, f"""
📢 <b>/all COMMAND USED</b>

👑 <b>Admin:</b> {admin_name}
🆔 <b>Admin ID:</b> <code>{user_id}</code>
🏠 <b>Group:</b> {group_name}
🆔 <b>Group ID:</b> <code>{chat_id}</code>
💬 <b>Message:</b> {message_text[:100]}
🕐 <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
""")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending announcement: {str(e)[:100]}")

# ==================== WELCOME FUNCTION ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members"""
    
    if not update.message.new_chat_members:
        return
    
    chat = update.effective_chat
    stats["total_welcomes"] += 1
    stats["groups"].add(chat.id)
    
    # Check if bot is admin
    try:
        bot_member = await chat.get_member(context.bot.id)
        is_admin = bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            continue
        
        # User info
        user_name = new_member.full_name
        user_first = new_member.first_name or "Guest"
        user_mention = f"<a href='tg://user?id={new_member.id}'>{user_name}</a>"
        username = f"@{new_member.username}" if new_member.username else "No username"
        user_id = new_member.id
        
        # Get profile photo
        profile_photo = await get_user_profile_photo(user_id, context)
        
        # Time
        current_time = datetime.now().strftime("%I:%M:%S %p")
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Welcome message
        welcome_message = f"""
{random_emoji(WELCOME_EMOJIS) * 6}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 6}

         🎉✨ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐓𝐇𝐄 𝐅𝐀𝐌𝐈𝐋𝐘! ✨🎉

{random_emoji(WELCOME_EMOJIS) * 6}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 6}

┌─────────────────────────────────────────────────────────────────┐
│                    📋 𝐌𝐄𝐌𝐁𝐄𝐑 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│        {random_emoji(USER_EMOJIS)}  𝐍𝐚𝐦𝐞       : {user_mention}                         │
│        🏷️  𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞   : {username}                           │
│        🆔  𝐔𝐬𝐞𝐫 𝐈𝐃     : <code>{user_id}</code>                              │
│        {random_emoji(USER_EMOJIS)}  𝐆𝐫𝐨𝐮𝐩      : {chat.title}                           │
│        {random_emoji(TIME_EMOJIS)}  𝐓𝐢𝐦𝐞       : {current_time}                         │
│        📅  𝐃𝐚𝐭𝐞       : {current_date}                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    💝 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐍𝐎𝐓𝐄                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎉 <b>𝐃𝐞𝐚𝐫 {user_first},</b> 🎉                                 │
│                                                                 │
│  ✨ <b>𝐀 𝐯𝐞𝐫𝐲 𝐰𝐚𝐫𝐦 𝐰𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐨𝐮𝐫 𝐚𝐦𝐚𝐳𝐢𝐧𝐠 𝐜𝐨𝐦𝐦𝐮𝐧𝐢𝐭𝐲!</b> ✨    │
│                                                                 │
│  🌟 <b>𝐖𝐞'𝐫𝐞 𝐬𝐨 𝐡𝐚𝐩𝐩𝐲 𝐭𝐨 𝐡𝐚𝐯𝐞 𝐲𝐨𝐮 𝐡𝐞𝐫𝐞!</b> 🌟                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

{random_emoji(WELCOME_EMOJIS) * 6}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 6}

                    {random_emoji(STAR_EMOJIS)} <b>𝐄𝐍𝐉𝐎𝐘 𝐘𝐎𝐔𝐑 𝐒𝐓𝐀𝐘!</b> {random_emoji(STAR_EMOJIS)} 

{random_emoji(WELCOME_EMOJIS) * 6}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{random_emoji(WELCOME_EMOJIS) * 6}
        """
        
        # Buttons
        keyboard = [
            [
                InlineKeyboardButton("📜 𝐑𝐔𝐋𝐄𝐒", url="https://t.me/telegram"),
                InlineKeyboardButton("💬 𝐈𝐍𝐓𝐑𝐎", url=f"tg://user?id={user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send animation
        try:
            random_gif = random.choice(ANIMATION_GIFS)
            await update.message.reply_animation(
                animation=random_gif,
                caption=f"🎉 <b>𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐀𝐋𝐄𝐑𝐓!</b> 🎉\n\n✨ {user_mention} ✨ 𝐣𝐨𝐢𝐧𝐞𝐝!",
                parse_mode='HTML'
            )
            await asyncio.sleep(1)
        except:
            pass
        
        # Send welcome message
        try:
            if is_admin and profile_photo:
                await update.message.reply_photo(
                    photo=profile_photo,
                    caption=welcome_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    welcome_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as e:
            await update.message.reply_text(
                f"🎉✨ <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {user_mention}</b> ✨🎉\n\n🌟 <b>𝐓𝐨 {chat.title}</b> 🌟",
                parse_mode='HTML'
            )
        
        # Notify bot owner (optional)
        if BOT_OWNER_ID:
            await send_to_bot_owner(context, f"""
🎉 <b>𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑!</b> 🎉

👤 <b>Name:</b> {user_name}
🆔 <b>ID:</b> <code>{user_id}</code>
🏠 <b>Group:</b> {chat.title}
👑 <b>Admin Mode:</b> {'✅ Yes' if is_admin else '❌ No'}
⏰ <b>Time:</b> {current_time}
""")

# ==================== START COMMAND ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
🤖 <b>𝐔𝐋𝐓𝐑𝐀 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐁𝐎𝐓 𝐈𝐒 𝐀𝐂𝐓𝐈𝐕𝐄!</b> 🤖

✨ <b>Features:</b> ✨
• 🎬 Animation GIFs
• 🖼️ Profile Photo
• 💝 Maximum Emojis
• 📢 /all Command (Group Admins Only)

<b>📌 How to use /all:</b>
<code>/all Your announcement message</code>

<b>👑 Who can use:</b>
• Any group admin can use /all
• Bot owner gets notifications

💡 <b>Add me to any group and make me admin for full features!</b>
""", parse_mode='HTML')

# ==================== HELP COMMAND ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
╔══════════════════════════════════════╗
║  📚 <b>𝐁𝐎𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b>                  ║
╚══════════════════════════════════════╝

✨ <b>Available Commands:</b>

/start - Start the bot
/help - Show this help

👑 <b>Group Admin Commands:</b>

/all &lt;message&gt; - Send announcement to group

<b>📝 Example:</b>
<code>/all Hello everyone! Important announcement!</code>

⚠️ <b>Note:</b>
• Only group admins can use /all
• Bot owner gets notified when /all is used
• Works in any group where bot is added
""", parse_mode='HTML')

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if BOT_OWNER_ID:
        await send_to_bot_owner(context, f"⚠️ Error: {str(context.error)[:100]}")

# ==================== MAIN ====================
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(CommandHandler("all", all_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error_handler)
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     🔥 ULTRA WELCOME BOT - GROUP ADMIN SUPPORT 🔥             ║
    ║                                                                ║
    ║     ✨ Features:                                               ║
    ║     • Welcome message with animation & emojis                 ║
    ║     • /all command for ANY group admin                        ║
    ║     • Profile photo display                                   ║
    ║     • Bot owner notifications                                 ║
    ║                                                                ║
    ║     🚀 BOT IS RUNNING! 🚀                                     ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
