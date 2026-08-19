
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes

from modules.base              import BaseModule
from modules.quran_audio.data  import SURAHS, RECITERS, RECITER_KEYS, get_audio_url, is_surah_available
from config                    import BOT_CHANNEL_URL
from utils.emojis              import HOME, SCHEDULE, SEND, DIV, NEXT_PAGE, PREV_PAGE, CHECK

logger = logging.getLogger(__name__)

SURAHS_PER_PAGE = 10
TOTAL_SURAHS    = len(SURAHS)
TOTAL_PAGES     = (TOTAL_SURAHS + SURAHS_PER_PAGE - 1) // SURAHS_PER_PAGE

async def send_quran_audio(bot: Bot, chat_id: int, surah_num: int, reciter_key: str):
    
    reciter    = RECITERS.get(reciter_key)
    surah_name = next((n for num, n in SURAHS if num == surah_num), str(surah_num))

    if not reciter:
        logger.error(f"قارئ غير موجود: {reciter_key}")
        return

    if not is_surah_available(reciter_key, surah_num):
        logger.warning(f"سورة {surah_num} غير متوفرة لقارئ {reciter_key}")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⚠️ عذرًا، سورة <b>{surah_name}</b> غير متوفرة بصوت الشيخ "
                    f"<b>{reciter['name_ar']}</b> — مصحفه يحتوي على عدد محدود من السور."
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"خطأ إرسال رسالة عدم التوفر: {e}")
        return

    audio_url = get_audio_url(reciter_key, surah_num)
    caption   = (
        f"<b>🎵 سـورة {surah_name}</b>\n\n"
        f"<b>🎙 القـارئ: {reciter['name_ar']}</b>\n\n"
        f"{DIV}"
    )

    keyboard = []
    if BOT_CHANNEL_URL:
        keyboard.append([InlineKeyboardButton("📢 قنـاة البـوت", url=BOT_CHANNEL_URL)])

    try:
        await bot.send_audio(
            chat_id=chat_id,
            audio=audio_url,
            caption=caption,
            parse_mode="HTML",
            title=f"سورة {surah_name}",
            performer=reciter["name_ar"],
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        logger.info(f"✅ تم إرسال صوت سورة {surah_num} ({reciter_key}) إلى {chat_id}")
    except Exception as e:
        logger.error(f"خطأ إرسال صوت: {e}")
        raise

class QuranAudioModule(BaseModule):
    KEY   = "qa"
    NAME  = "القرآن (صوت)"
    EMOJI = "🎵"

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
            await self._show_reciters(query, context, chat_id, surah_num)

        elif action == "rc" and len(path) >= 3:
            try:
                rec_key   = path[1]
                surah_num = int(path[2])
            except (ValueError, IndexError):
                await query.answer("❌ بيانات غير صالحة", show_alert=True)
                return
            await self._show_send_confirm(query, context, chat_id, surah_num, rec_key)

        elif action == "snd" and len(path) >= 3:
            try:
                rec_key   = path[1]
                surah_num = int(path[2])
            except (ValueError, IndexError):
                await query.answer("❌ بيانات غير صالحة", show_alert=True)
                return
            try:
                await send_quran_audio(context.bot, chat_id, surah_num, rec_key)
                await query.answer("✅ تـم الإرسـال")
                await self._show_send_confirm(query, context, chat_id, surah_num, rec_key, sent=True)
            except Exception as e:
                logger.error(f"خطأ إرسال صوت: {e}")
                await query.answer("❌ فشـل الإرسـال، تأكـد مـن صلاحيـات البـوت", show_alert=True)

        elif action == "na" and len(path) >= 3:
            try:
                rec_key   = path[1]
                surah_num = int(path[2])
            except (ValueError, IndexError):
                await self._show_surah_list(query, chat_id, 0)
                return
            rec = RECITERS.get(rec_key, {})
            surah_name = next((n for num, n in SURAHS if num == surah_num), str(surah_num))
            await query.answer(
                f"⚠️ سورة {surah_name} غير متوفرة بصوت {rec.get('name_ar', rec_key)}",
                show_alert=True
            )

        elif action == "sch" and len(path) >= 3:
            rec_key   = path[1]
            surah_num = int(path[2])
            await self._start_schedule_wizard(query, context, chat_id, surah_num, rec_key)

        else:
            await self._show_surah_list(query, chat_id, 0)

    async def execute_scheduled_job(self, bot: Bot, chat_id: int, job_data: dict):
        surah_num  = job_data.get("surah_num", 1)
        reciter_key = job_data.get("reciter_key", "alaf")
        await send_quran_audio(bot, chat_id, surah_num, reciter_key)

    async def _show_surah_list(self, query, chat_id: int, page: int):
        start = page * SURAHS_PER_PAGE
        end   = min(start + SURAHS_PER_PAGE, TOTAL_SURAHS)
        chunk = SURAHS[start:end]

        keyboard = []
        for i in range(0, len(chunk), 2):
            row = []
            for num, name in chunk[i:i + 2]:
                row.append(InlineKeyboardButton(
                    f"🎵 {num}. {name}",
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
                f"<b>🎵 القـرآن الكريـم (صـوت)</b>\n\n"
                f"<blockquote><b>اختـر السـورة — الصفحـة {page + 1}/{TOTAL_PAGES}</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _show_reciters(self, query, context, chat_id: int, surah_num: int):
        surah_name = next((n for num, n in SURAHS if num == surah_num), str(surah_num))

        keyboard = []
        for key in RECITER_KEYS:
            rec = RECITERS[key]
            if not is_surah_available(key, surah_num):
                keyboard.append([InlineKeyboardButton(
                    f"🎙 {rec['name_ar']} (غير متوفرة هذه السورة)",
                    callback_data=self.cb(chat_id, "na", key, str(surah_num))
                )])
                continue
            row_cb = self.cb(chat_id, "rc", key, str(surah_num))
            if len(row_cb.encode()) <= 64:
                keyboard.append([InlineKeyboardButton(
                    f"🎙 {rec['name_ar']}",
                    callback_data=row_cb
                )])

        keyboard.append([InlineKeyboardButton("⬅️ رجـوع للسـور", callback_data=self.cb(chat_id))])

        await query.edit_message_text(
            text=(
                f"<b>🎵 سـورة {surah_name}</b>\n\n"
                f"<blockquote><b>اختـر القـارئ:</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _show_send_confirm(self, query, context, chat_id: int,
                                  surah_num: int, rec_key: str, sent: bool = False):
        surah_name  = next((n for num, n in SURAHS if num == surah_num), str(surah_num))
        reciter     = RECITERS.get(rec_key, {})
        rec_name    = reciter.get("name_ar", rec_key)

        try:
            chat_name = (await context.bot.get_chat(chat_id)).title or str(chat_id)
        except Exception:
            chat_name = str(chat_id)

        status = f"\n\n<b>✅ تـم الإرسـال إلـى {chat_name}</b>" if sent else ""

        snd_cb = self.cb(chat_id, "snd", rec_key, str(surah_num))
        sch_cb = self.cb(chat_id, "sch", rec_key, str(surah_num))

        keyboard = [
            [InlineKeyboardButton("📤 إرسـال الآن",     callback_data=snd_cb)],
            [InlineKeyboardButton("🗓 جدولـة الإرسـال", callback_data=sch_cb)],
            [InlineKeyboardButton("⬅️ تغييـر القـارئ",  callback_data=self.cb(chat_id, "sl", str(surah_num)))],
        ]

        await query.edit_message_text(
            text=(
                f"<b>🎵 سـورة {surah_name}</b>\n"
                f"<b>🎙 القـارئ: {rec_name}</b>\n\n"
                f"<b>📍 المجموعـة: {chat_name}</b>\n\n"
                f"<blockquote>"
                f"<b>• تنسيـق الإرسـال: ملـف صوتـي MP3</b>\n"
                f"<b>• الجـودة: 64kbps</b>\n"
                f"<b>• المصـدر: Islamic Network CDN</b>"
                if not reciter.get("base_url") else
                f"<b>• تنسيـق الإرسـال: ملـف صوتـي MP3</b>\n"
                f"<b>• الجـودة: 128kbps</b>\n"
                f"<b>• المصـدر: mp3quran.net / way2quran</b>"
                f"</blockquote>"
                f"{status}"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _start_schedule_wizard(self, query, context, chat_id: int,
                                      surah_num: int, rec_key: str):
        surah_name = next((n for num, n in SURAHS if num == surah_num), str(surah_num))
        context.user_data["sched"] = {
            "state":   "interval_type",
            "chat_id": chat_id,
            "module":  self.KEY,
            "data":    {"surah_num": surah_num, "reciter_key": rec_key},
        }

        keyboard = [
            [InlineKeyboardButton("كـل دقيقـة", callback_data="sch|min"),
             InlineKeyboardButton("كـل ساعـة",  callback_data="sch|hr")],
            [InlineKeyboardButton("يوميـا",     callback_data="sch|daily"),
             InlineKeyboardButton("أسبوعيـا",  callback_data="sch|weekly")],
            [InlineKeyboardButton("شهريـا",     callback_data="sch|monthly"),
             InlineKeyboardButton("سنويـا",     callback_data="sch|yearly")],
            [InlineKeyboardButton("مخصـص (أدخـل الدقائـق)", callback_data="sch|cust")],
            [InlineKeyboardButton("❌ إلغـاء", callback_data=self.cb(chat_id, "rc", rec_key, str(surah_num)))],
        ]

        await query.edit_message_text(
            text=(
                f"<b>🗓 جدولـة سـورة {surah_name}</b>\n\n"
                f"<blockquote><b>اختـر تكـرار الإرسـال:</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
