
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes

from database       import Database
from services.roles import RolesService

logger = logging.getLogger(__name__)
db     = Database.get()
roles  = RolesService()

async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    result = update.my_chat_member
    if not result:
        return

    new_status  = result.new_chat_member.status
    old_status  = result.old_chat_member.status
    chat        = result.chat
    added_by    = result.from_user

    if new_status in (ChatMember.ADMINISTRATOR, ChatMember.MEMBER) and \
       old_status in (ChatMember.LEFT, ChatMember.BANNED, "kicked"):

        await db.upsert_group(chat.id, chat.title or str(chat.id), chat.type)
        logger.info(f"✅ البوت أضيف إلى: {chat.title} ({chat.id})")

        try:
            bot_me       = await context.bot.get_me()
            bot_username = bot_me.username
            panel_link   = f"https://t.me/{bot_username}?start=panel_{chat.id}"

            keyboard = [
                [
                    InlineKeyboardButton("➕ أضف البوت لمجموعتك",
                                         url=f"https://t.me/{bot_username}?startgroup=true"),
                    InlineKeyboardButton("⚙️ Custom", url=panel_link),
                ]
            ]

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "<b>بسم الله الرحمن الرحيم</b>\n\n"
                    "<b>🕌 السلام عليكم ورحمة الله وبركاته</b>\n\n"
                    "<blockquote>"
                    "<b>تم إضافة بوت القرآن الكريم لهذه المجموعة 🎉</b>\n\n"
                    "<b>• 📖 تصفح المصحف الشريف</b>\n"
                    "<b>• 📿 إرسال الأذكار والتسبيح</b>\n"
                    "<b>• 🎵 إرسال التلاوات الصوتية</b>\n"
                    "<b>• 🗓 جدولة الإرسال التلقائي</b>"
                    "</blockquote>\n\n"
                    "<b>للوصول للوحة التحكم اضغط ⚙️ Custom</b>"
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة ترحيب للمجموعة {chat.id}: {e}")

    elif new_status in (ChatMember.LEFT, ChatMember.BANNED) and \
         old_status in (ChatMember.ADMINISTRATOR, ChatMember.MEMBER):
        logger.info(f"⚠️ البوت أزيل من: {chat.title} ({chat.id})")
