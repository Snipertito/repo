
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.scheduler import SchedulerService
from utils.helpers      import parse_time, parse_date, next_occurrence, interval_label

logger = logging.getLogger(__name__)

async def sched_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    await query.answer()

    data  = (query.data or "").split("|")
    action = data[1] if len(data) > 1 else ""

    sched_ctx = context.user_data.get("sched")
    if not sched_ctx:
        await query.edit_message_text(
            "<b>⚠️ انتهـت جلسـة الجدولـة، ابـدأ مـن جديـد</b>",
            parse_mode="HTML"
        )
        return

    interval_map = {
        "min":     ("minutes", 1),
        "hr":      ("hours",   1),
        "daily":   ("daily",   1),
        "weekly":  ("weekly",  1),
        "monthly": ("monthly", 1),
        "yearly":  ("yearly",  1),
    }

    if action == "cust":
        
        sched_ctx["state"] = "waiting_custom_interval"
        context.user_data["sched"] = sched_ctx
        await query.edit_message_text(
            "<b>⏱ أدخـل عـدد الدقائـق بيـن كـل إرسـال:</b>\n"
            "<blockquote><b>مثـال: 30 (كـل نصـف ساعـة)</b></blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغـاء", callback_data="sch|cancel")
            ]])
        )
        return

    if action == "cancel":
        context.user_data.pop("sched", None)
        await query.edit_message_text("<b>✅ تـم إلغـاء الجدولـة</b>", parse_mode="HTML")
        return

    if action in interval_map:
        itype, ival = interval_map[action]
        sched_ctx["interval_type"]  = itype
        sched_ctx["interval_value"] = ival
        sched_ctx["state"]          = "waiting_start_time"
        context.user_data["sched"]  = sched_ctx

        await query.edit_message_text(
            f"<b>🗓 تكـرار الإرسـال: {interval_label(itype, ival)}</b>\n\n"
            f"<b>⏰ أدخـل وقـت البدايـة (بتوقيـت UTC):</b>\n"
            f"<blockquote><b>مثـال: 06:00</b></blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغـاء", callback_data="sch|cancel")
            ]])
        )
        return

    if action == "skip_end":
        await _finalize_schedule(query, context, sched_ctx, end_time=None)
        return

    if action == "confirm":
        end_time = sched_ctx.get("end_time")
        await _finalize_schedule(query, context, sched_ctx, end_time=end_time)
        return

async def sched_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    
    sched_ctx = context.user_data.get("sched")
    if not sched_ctx:
        return False

    state = sched_ctx.get("state", "")
    text  = update.message.text.strip()

    if state == "waiting_custom_interval":
        try:
            minutes = int(text)
            if minutes < 1:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(
                "<b>❌ أدخـل رقمـا صحيحـا أكبـر مـن 0</b>",
                parse_mode="HTML"
            )
            return True

        sched_ctx["interval_type"]  = "minutes"
        sched_ctx["interval_value"] = minutes
        sched_ctx["state"]          = "waiting_start_time"
        context.user_data["sched"]  = sched_ctx

        await update.message.reply_text(
            f"<b>⏱ التكـرار: كـل {minutes} دقيقـة</b>\n\n"
            f"<b>⏰ أدخـل وقـت البدايـة (بتوقيـت UTC):</b>\n"
            f"<blockquote><b>مثـال: 06:00</b></blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغـاء", callback_data="sch|cancel")
            ]])
        )
        return True

    if state == "waiting_start_time":
        parsed = parse_time(text)
        if not parsed:
            await update.message.reply_text(
                "<b>❌ صيغـة الوقـت غيـر صحيحـة</b>\n"
                "<blockquote><b>أدخـل الوقـت بصيغـة HH:MM — مثـال: 07:30</b></blockquote>",
                parse_mode="HTML"
            )
            return True

        hour, minute   = parsed
        start_dt       = next_occurrence(hour, minute)
        sched_ctx["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        sched_ctx["state"]      = "waiting_end_date"
        context.user_data["sched"] = sched_ctx

        await update.message.reply_text(
            f"<b>⏰ وقـت البدايـة: {start_dt.strftime('%Y-%m-%d %H:%M')} UTC</b>\n\n"
            f"<b>📅 هـل تريـد تحديـد تاريـخ الانتهـاء؟</b>\n"
            f"<blockquote><b>أدخـل التاريـخ (مثـال: 2025-12-31) أو اضغـط تخطـي</b></blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭ تخطـي (بـلا انتهـاء)", callback_data="sch|skip_end")],
                [InlineKeyboardButton("❌ إلغـاء",                callback_data="sch|cancel")],
            ])
        )
        return True

    if state == "waiting_end_date":
        parsed_date = parse_date(text)
        if not parsed_date:
            await update.message.reply_text(
                "<b>❌ صيغـة التاريـخ غيـر صحيحـة</b>\n"
                "<blockquote><b>مثـال: 2025-12-31 أو اضغـط تخطـي</b></blockquote>",
                parse_mode="HTML"
            )
            return True

        sched_ctx["end_time"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
        context.user_data["sched"] = sched_ctx

        await _finalize_schedule_from_message(update, context, sched_ctx)
        return True

    return False

async def _finalize_schedule(query, context, sched_ctx: dict, end_time: str | None):
    
    svc = SchedulerService.get()
    try:
        sched_id = await svc.add_schedule(
            chat_id        = sched_ctx["chat_id"],
            module_key     = sched_ctx["module"],
            job_data       = sched_ctx["data"],
            interval_type  = sched_ctx["interval_type"],
            interval_value = sched_ctx["interval_value"],
            start_time     = sched_ctx["start_time"],
            end_time       = end_time,
            created_by     = query.from_user.id,
        )
        context.user_data.pop("sched", None)
        label = interval_label(sched_ctx["interval_type"], sched_ctx["interval_value"])
        await query.edit_message_text(
            f"<b>✅ تـم إنشـاء الجـدول بنجـاح</b>\n\n"
            f"<b>🆔 رقـم الجـدول: {sched_id}</b>\n"
            f"<b>⏰ البدايـة: {sched_ctx['start_time']}</b>\n"
            f"<b>🔁 التكـرار: {label}</b>\n"
            f"<b>📅 الانتهـاء: {end_time or 'بـلا انتهـاء'}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"خطأ في إنشاء الجدول: {e}", exc_info=True)
        await query.edit_message_text(
            "<b>❌ حـدث خطـأ أثنـاء إنشـاء الجـدول</b>",
            parse_mode="HTML"
        )

async def _finalize_schedule_from_message(update, context, sched_ctx: dict):
    
    svc = SchedulerService.get()
    try:
        sched_id = await svc.add_schedule(
            chat_id        = sched_ctx["chat_id"],
            module_key     = sched_ctx["module"],
            job_data       = sched_ctx["data"],
            interval_type  = sched_ctx["interval_type"],
            interval_value = sched_ctx["interval_value"],
            start_time     = sched_ctx["start_time"],
            end_time       = sched_ctx.get("end_time"),
            created_by     = update.effective_user.id,
        )
        context.user_data.pop("sched", None)
        label = interval_label(sched_ctx["interval_type"], sched_ctx["interval_value"])
        await update.message.reply_text(
            f"<b>✅ تـم إنشـاء الجـدول بنجـاح</b>\n\n"
            f"<b>🆔 رقـم الجـدول: {sched_id}</b>\n"
            f"<b>⏰ البدايـة: {sched_ctx['start_time']}</b>\n"
            f"<b>🔁 التكـرار: {label}</b>\n"
            f"<b>📅 الانتهـاء: {sched_ctx.get('end_time') or 'بـلا انتهـاء'}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"خطأ في إنشاء الجدول: {e}", exc_info=True)
        await update.message.reply_text(
            "<b>❌ حـدث خطـأ أثنـاء إنشـاء الجـدول</b>",
            parse_mode="HTML"
        )
