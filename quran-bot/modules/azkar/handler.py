
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes

from modules.base         import BaseModule
from modules.azkar.data   import AZKAR_DATA, AZKAR_CATEGORY_KEYS
from services.scheduler   import SchedulerService
from config               import BOT_CHANNEL_URL
from utils.emojis         import (
    BEADS, HOME, SCHEDULE, SEND, DIV, CHECK, TIMER
)

logger = logging.getLogger(__name__)

def _build_azkar_message(category: str, zikr: dict, cat_data: dict) -> str:
    
    quote = cat_data["quote"]
    return (
        f"<b>{cat_data['emoji']} {cat_data['name']}</b>\n\n"
        f"{DIV}\n\n"
        f"<b>📿 الذكـر:</b>\n"
        f"<blockquote><b>« {zikr['text']} »</b></blockquote>\n\n"
        f"<b>🔢 العـدد:</b> <b>{zikr['count']}</b>\n"
        f"<b>📚 المصـدر:</b> <b>{zikr['source']}</b>\n\n"
        f"{DIV}\n\n"
        f"<b>💬 قـال رسـول الله ﷺ:</b>\n"
        f"<blockquote><b>« {quote['text']} »</b>\n"
        f"<b>— {quote['source']}</b></blockquote>"
    )

async def send_azkar_to_chat(bot: Bot, chat_id: int, category: str):
    
    cat_data = AZKAR_DATA.get(category)
    if not cat_data:
        logger.error(f"فئة أذكار غير موجودة: {category}")
        return

    zikr = random.choice(cat_data["azkar"])
    text = _build_azkar_message(category, zikr, cat_data)

    keyboard = []
    if BOT_CHANNEL_URL:
        keyboard.append([InlineKeyboardButton("📢 قنـاة البـوت", url=BOT_CHANNEL_URL)])

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )
    logger.info(f"✅ تم إرسال أذكار ({category}) إلى {chat_id}")

class AzkarModule(BaseModule):
    KEY   = "azkar"
    NAME  = "الأذكار"
    EMOJI = "📿"

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               chat_id: int, path: list[str]):
        query = update.callback_query

        if not path:
            await self._show_categories(query, chat_id)
            return

        action = path[0]

        if action == "cat" and len(path) >= 2:
            await self._show_category(query, context, chat_id, path[1])

        elif action == "snd" and len(path) >= 2:
            category = path[1]
            try:
                await send_azkar_to_chat(context.bot, chat_id, category)
                await query.answer(f"✅ تـم الإرسـال", show_alert=False)
                
                await self._show_category(query, context, chat_id, category, sent=True)
            except Exception as e:
                logger.error(f"خطأ في إرسال الأذكار: {e}")
                await query.answer("❌ فشـل الإرسـال، تأكـد مـن صلاحيـات البـوت في المجموعـة", show_alert=True)

        elif action == "sch" and len(path) >= 2:
            await self._start_schedule_wizard(query, context, chat_id, path[1])

        elif action == "schd":
            
            await self._handle_schedule_type(query, context, chat_id, path)

        else:
            await self._show_categories(query, chat_id)

    async def execute_scheduled_job(self, bot: Bot, chat_id: int, job_data: dict):
        category = job_data.get("category", "morning")
        await send_azkar_to_chat(bot, chat_id, category)

    async def _show_categories(self, query, chat_id: int):
        keyboard = []
        for key in AZKAR_CATEGORY_KEYS:
            cat = AZKAR_DATA[key]
            keyboard.append([InlineKeyboardButton(
                f"{cat['emoji']} {cat['name']}",
                callback_data=self.cb(chat_id, "cat", key)
            )])
        keyboard.append([InlineKeyboardButton(f"{HOME} رجوع", callback_data=f"cp|{chat_id}|main")])

        await query.edit_message_text(
            text=(
                f"<b>{self.EMOJI} {self.NAME}</b>\n\n"
                f"<blockquote><b>اختـر نـوع الذكـر الـذي تريـد إرسالـه للمجموعـة</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _show_category(self, query, context, chat_id: int, category: str, sent: bool = False):
        cat_data = AZKAR_DATA.get(category)
        if not cat_data:
            await query.answer("❌ الفئـة غيـر موجـودة", show_alert=True)
            return

        try:
            chat = await context.bot.get_chat(chat_id)
            chat_name = chat.title or str(chat_id)
        except Exception:
            chat_name = str(chat_id)

        status = f"\n\n<b>{CHECK} تـم الإرسـال إلـى {chat_name} ✅</b>" if sent else ""

        keyboard = [
            [InlineKeyboardButton(f"📤 إرسـال ذكـر الآن",    callback_data=self.cb(chat_id, "snd", category))],
            [InlineKeyboardButton(f"🗓 جدولـة الإرسـال",      callback_data=self.cb(chat_id, "sch", category))],
            [InlineKeyboardButton(f"⬅️ رجـوع للأذكـار",      callback_data=self.cb(chat_id))],
        ]

        preview_zikr = AZKAR_DATA[category]["azkar"][0]
        text = (
            f"<b>{cat_data['emoji']} {cat_data['name']}</b>\n\n"
            f"<b>📍 المجموعـة المستهدفـة: {chat_name}</b>\n\n"
            f"<b>مثـال علـى الذكـر:</b>\n"
            f"<blockquote><b>« {preview_zikr['text'][:120]}{'...' if len(preview_zikr['text']) > 120 else ''} »</b></blockquote>"
            f"{status}"
        )

        await query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _start_schedule_wizard(self, query, context, chat_id: int, category: str):

        context.user_data["sched"] = {
            "state":    "interval_type",
            "chat_id":  chat_id,
            "module":   self.KEY,
            "data":     {"category": category},
        }

        keyboard = [
            [InlineKeyboardButton("كـل دقيقـة",  callback_data="sch|min"),
             InlineKeyboardButton("كـل ساعـة",   callback_data="sch|hr")],
            [InlineKeyboardButton("يوميـا",      callback_data="sch|daily"),
             InlineKeyboardButton("أسبوعيـا",   callback_data="sch|weekly")],
            [InlineKeyboardButton("شهريـا",      callback_data="sch|monthly"),
             InlineKeyboardButton("سنويـا",      callback_data="sch|yearly")],
            [InlineKeyboardButton("مخصـص (أدخـل الدقائـق)", callback_data="sch|cust")],
            [InlineKeyboardButton("❌ إلغـاء",   callback_data=self.cb(chat_id, "cat", category))],
        ]

        cat = AZKAR_DATA.get(category, {})
        await query.edit_message_text(
            text=(
                f"<b>🗓 جدولـة {cat.get('name', 'الأذكـار')}</b>\n\n"
                f"<blockquote><b>اختـر تكـرار الإرسـال:</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _handle_schedule_type(self, query, context, chat_id: int, path: list[str]):

        await self._show_categories(query, chat_id)
