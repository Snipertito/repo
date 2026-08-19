
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes

from modules.base              import BaseModule
from modules.quran_text.data   import SURAHS, SURAHS_PER_PAGE, AYAHS_PER_MSG, QURAN_API_BASE
from config                    import BOT_CHANNEL_URL
from utils.emojis              import HOME, SCHEDULE, SEND, DIV, NEXT_PAGE, PREV_PAGE, CHECK

logger = logging.getLogger(__name__)

TOTAL_SURAHS = len(SURAHS)
TOTAL_PAGES  = (TOTAL_SURAHS + SURAHS_PER_PAGE - 1) // SURAHS_PER_PAGE

async def _fetch_surah(surah_num: int, page: int = 0) -> dict | None:
    
    url = f"{QURAN_API_BASE}/surah/{surah_num}/ar.asem"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()["data"]

        ayahs      = data["ayahs"]
        start      = page * AYAHS_PER_MSG
        end        = min(start + AYAHS_PER_MSG, len(ayahs))
        total_pages = (len(ayahs) + AYAHS_PER_MSG - 1) // AYAHS_PER_MSG

        return {
            "name":        data["name"],
            "ayahs":       ayahs[start:end],
            "total_ayahs": len(ayahs),
            "total_pages": total_pages,
            "page":        page,
        }
    except Exception as e:
        logger.error(f"خطأ في جلب سورة {surah_num}: {e}")
        return None

def _build_quran_message(surah_data: dict) -> str:
    
    name = surah_data["name"]
    page = surah_data["page"]
    total = surah_data["total_pages"]

    lines = [
        f"<b>📖 {name}</b>",
        f"<b>الصفحـة {page + 1} مـن {total}</b>",
        f"\n{DIV}\n",
        "<b>بسم الله الرحمن الرحيم</b>\n" if page == 0 else "",
    ]

    for ayah in surah_data["ayahs"]:
        lines.append(f"<b>﴿ {ayah['text']} ﴾</b>")
        lines.append(f"<b>({ayah['numberInSurah']})</b>\n")

    lines.append(DIV)
    lines.append(f"\n<i>📝 نـص القـرآن الكريـم — برواية حفص عن عاصم</i>")
    return "\n".join(l for l in lines if l)

async def send_quran_text(bot: Bot, chat_id: int, surah_num: int, page: int = 0):
    
    surah_data = await _fetch_surah(surah_num, page)
    if not surah_data:
        await bot.send_message(
            chat_id=chat_id,
            text="<b>❌ تعـذر جلـب القـرآن الكريـم، يرجـى المحاولـة لاحقـا</b>",
            parse_mode="HTML"
        )
        return

    text = _build_quran_message(surah_data)

    keyboard = []
    if BOT_CHANNEL_URL:
        keyboard.append([InlineKeyboardButton("📢 قنـاة البـوت", url=BOT_CHANNEL_URL)])

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )
    logger.info(f"✅ تم إرسال سورة {surah_num} صفحة {page} إلى {chat_id}")

class QuranTextModule(BaseModule):
    KEY   = "qt"
    NAME  = "القرآن (نص)"
    EMOJI = "📖"

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               chat_id: int, path: list[str]):
        query = update.callback_query

        if not path:
            await self._show_surah_list(query, chat_id, 0)
            return

        action = path[0]

        if action == "pg" and len(path) >= 2:
            try:
                page = int(path[1])
            except ValueError:
                page = 0
            await self._show_surah_list(query, chat_id, page)

        elif action == "sl" and len(path) >= 2:
            try:
                surah_num = int(path[1])
            except ValueError:
                await self._show_surah_list(query, chat_id, 0)
                return
            await self._show_surah_detail(query, context, chat_id, surah_num)

        elif action == "snd" and len(path) >= 2:
            try:
                surah_num = int(path[1])
                pg        = int(path[2]) if len(path) >= 3 else 0
            except (ValueError, IndexError):
                await query.answer("❌ بيانات غير صالحة", show_alert=True)
                return
            try:
                await send_quran_text(context.bot, chat_id, surah_num, pg)
                await query.answer("✅ تـم الإرسـال")
                await self._show_surah_detail(query, context, chat_id, surah_num, sent=True)
            except Exception as e:
                logger.error(f"خطأ إرسال قرآن نص: {e}")
                await query.answer("❌ فشـل الإرسـال، تأكـد مـن صلاحيـات البـوت", show_alert=True)

        elif action == "sch" and len(path) >= 2:
            await self._start_schedule_wizard(query, context, chat_id, int(path[1]))

        else:
            await self._show_surah_list(query, chat_id, 0)

    async def execute_scheduled_job(self, bot: Bot, chat_id: int, job_data: dict):
        surah_num = job_data.get("surah_num", 1)
        page      = job_data.get("page", 0)
        await send_quran_text(bot, chat_id, surah_num, page)

    async def _show_surah_list(self, query, chat_id: int, page: int):
        start = page * SURAHS_PER_PAGE
        end   = min(start + SURAHS_PER_PAGE, TOTAL_SURAHS)
        chunk = SURAHS[start:end]

        keyboard = []
        
        for i in range(0, len(chunk), 2):
            row = []
            for num, name in chunk[i:i + 2]:
                row.append(InlineKeyboardButton(
                    f"{num}. {name}",
                    callback_data=self.cb(chat_id, "sl", str(num))
                ))
            keyboard.append(row)

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(f"{PREV_PAGE} السابـق", callback_data=self.cb(chat_id, "pg", str(page - 1))))
        if end < TOTAL_SURAHS:
            nav.append(InlineKeyboardButton(f"التالـي {NEXT_PAGE}", callback_data=self.cb(chat_id, "pg", str(page + 1))))
        if nav:
            keyboard.append(nav)

        keyboard.append([InlineKeyboardButton(f"{HOME} رجـوع", callback_data=f"cp|{chat_id}|main")])

        await query.edit_message_text(
            text=(
                f"<b>📖 القـرآن الكريـم (نـص)</b>\n\n"
                f"<blockquote><b>اختـر السـورة — الصفحـة {page + 1}/{TOTAL_PAGES}</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _show_surah_detail(self, query, context, chat_id: int,
                                  surah_num: int, sent: bool = False):
        surah_name = next((n for num, n in SURAHS if num == surah_num), str(surah_num))

        try:
            chat_name = (await context.bot.get_chat(chat_id)).title or str(chat_id)
        except Exception:
            chat_name = str(chat_id)

        status = f"\n\n<b>✅ تـم الإرسـال إلـى {chat_name}</b>" if sent else ""

        keyboard = [
            [InlineKeyboardButton("📤 إرسـال أول ٥ آيـات الآن", callback_data=self.cb(chat_id, "snd", str(surah_num), "0"))],
            [InlineKeyboardButton("🗓 جدولـة الإرسـال",          callback_data=self.cb(chat_id, "sch", str(surah_num)))],
            [InlineKeyboardButton("⬅️ رجـوع للسـور",             callback_data=self.cb(chat_id))],
        ]

        await query.edit_message_text(
            text=(
                f"<b>📖 سـورة {surah_name}</b>\n\n"
                f"<b>📍 المجموعـة: {chat_name}</b>\n\n"
                f"<blockquote>"
                f"<b>• سيتـم إرسـال أول ٥ آيـات مـن السـورة</b>\n"
                f"<b>• التنسيـق: نـص عربـي بتشكيـل كامـل</b>\n"
                f"<b>• المصـدر: برواية حفص عن عاصم</b>"
                f"</blockquote>"
                f"{status}"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _start_schedule_wizard(self, query, context, chat_id: int, surah_num: int):
        surah_name = next((n for num, n in SURAHS if num == surah_num), str(surah_num))
        context.user_data["sched"] = {
            "state":   "interval_type",
            "chat_id": chat_id,
            "module":  self.KEY,
            "data":    {"surah_num": surah_num, "page": 0},
        }

        keyboard = [
            [InlineKeyboardButton("كـل دقيقـة",  callback_data="sch|min"),
             InlineKeyboardButton("كـل ساعـة",   callback_data="sch|hr")],
            [InlineKeyboardButton("يوميـا",      callback_data="sch|daily"),
             InlineKeyboardButton("أسبوعيـا",   callback_data="sch|weekly")],
            [InlineKeyboardButton("شهريـا",      callback_data="sch|monthly"),
             InlineKeyboardButton("سنويـا",      callback_data="sch|yearly")],
            [InlineKeyboardButton("مخصـص (أدخـل الدقائـق)", callback_data="sch|cust")],
            [InlineKeyboardButton("❌ إلغـاء", callback_data=self.cb(chat_id, "sl", str(surah_num)))],
        ]

        await query.edit_message_text(
            text=(
                f"<b>🗓 جدولـة سـورة {surah_name}</b>\n\n"
                f"<blockquote><b>اختـر تكـرار الإرسـال:</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
