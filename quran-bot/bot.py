
import os
import html
import logging
import asyncio
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ChatMemberHandler
)

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# معالج أخطاء شبكة polling المؤقتة عشان البوت يرجع تلقائي
async def network_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"خطأ مؤقت في الاتصال: {context.error}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    if isinstance(error, (telegram.error.NetworkError, telegram.error.TimedOut)):
        logger.warning(f"خطأ شبكة مؤقت (سيتم الاستئناف تلقائياً): {error}")
    elif isinstance(error, telegram.error.Conflict):
        # تعارض getUpdates (مثلاً من عملية أخرى) — إعادة التشغيل تلقائيًا بعد انتظار قصير
        logger.warning(f"تعارض polling: {error} — إعادة الاتصال تلقائيًا...")
        try:
            await asyncio.sleep(10)
            await context.application.stop()
            await context.application.initialize()
            await context.application.start()
            logger.info("✅ تم استئناف عمل البوت بعد تعارض getUpdates")
        except Exception as e:
            logger.error(f"فشل استئناف البوت: {e}", exc_info=True)
            raise
    else:
        logger.error(f"خطأ غير متوقع: {error}", exc_info=True)


import telegram

from config          import BOT_TOKEN, OPENROUTER_API_KEY, WEBAPP_URL, INITIAL_OWNER_ID
from database        import Database
from services.roles  import RolesService
from services.scheduler import SchedulerService, set_bot_app

def ce(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

LINE  = ce("5382360493161725288", "➖")
CLOCK = ce("5258258882022612173", "⏲")
PEN   = ce("5852614525370503272", "📝")
PRAY2 = ce("5859341586617340244", "🤲")
INFO  = ce("5224688446974475279", "ℹ️")

WAITING_QUESTION = "waiting_religious_question"

from handlers.start        import start, main_menu_keyboard, back_keyboard, build_welcome
from handlers.group_events import my_chat_member_handler
from handlers.owner_cmds   import (
    cmd_owners, cmd_addowner, cmd_removeowner,
    cmd_admins, cmd_addadmin, cmd_removeadmin,
    cmd_setperms, cmd_panel, cmd_devpanel
)
from modules.devpanel.handler import devpanel_callback_handler
from handlers.sched_handler   import sched_callback_handler, sched_text_handler
from modules.panel.handler    import panel_callback_handler
from modules.registry         import ModuleRegistry

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    QUESTION = ce("5783013214539225637", "❔")
    BACK     = ce("5960671702059848143", "⬅️")
    FAQ2     = ce("5776056162088652694", "❓")
    PRAY3    = ce("5289949229496671641", "🤲")
    DOWN     = ce("5409210859169787977", "⬇️")
    PC       = ce("5870692618244984670", "💻")
    NUM1     = ce("5798796566516993587", "1⃣")
    NUM2     = ce("5798643450932891251", "2⃣")
    NUM3     = ce("5798439598900125383", "3⃣")
    NUM4     = ce("5798618995389112011", "4⃣")
    WAVE     = ce("5413554183502572090", "👋")
    BEADS    = ce("5996581850607261681", "📿")

    if query.data == "questions":
        context.user_data["state"] = WAITING_QUESTION
        await query.edit_message_text(
            text=(
                f"<b>{QUESTION} اسئـلة دينيـة</b>\n\n"
                f"<blockquote><b>اكتـب سؤالـك الدينـي وسأجيبـك باذن الله {PRAY2}</b></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

    elif query.data == "back_main":
        context.user_data.pop("state", None)
        context.user_data.pop("sched", None)
        await query.edit_message_text(
            text=build_welcome(update.effective_user),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )

    elif query.data == "about":
        DIV_LINE = f"{LINE}{LINE}{LINE}{LINE}{DOWN}{LINE}{LINE}{LINE}{LINE}"
        faq_text = (
            f"<b>• عـن البـوت {FAQ2}</b>\n\n"
            f"<b>بـوت القـران الكـريم هـو بـوت تيليجـرام متخصـص في خدمـة كتـاب الله والمحتـوى الدينـي الاسلامـي {PRAY3}</b>\n\n"
            f"<b>{DIV_LINE}</b>\n\n"
            f"<b>اقسـام البـوت {PC}</b>\n\n"
            f"<b>{NUM1} المصحـف الكـريم</b>\n\n"
            f"<b>• يتيـح لـك تصفـح القـران الكـريم كاملا مـن داخـل تيليجـرام</b>\n"
            f"<b>• يمكنـك البحـث عـن اي سـورة والانتقـال اليهـا مباشـرة وعـرض الايـات بشكـل واضـح ومريـح</b>\n\n"
            f"<b>{DIV_LINE}</b>\n\n"
            f"<b>{NUM2} الاذكـار</b>\n\n"
            f"<b>• يحتـوي علـى مجموعـة متنوعـة مـن الاذكـار اليوميـة</b>\n"
            f"<b>• اذكـار الصبـاح والمسـاء واذكـار النـوم والاستيقـاظ</b>\n"
            f"<b>• وغيرهـا مـن الاذكـار الماثـورة</b>\n\n"
            f"<b>{DIV_LINE}</b>\n\n"
            f"<b>{NUM3} الاسئـلة الدينيـة</b>\n\n"
            f"<b>• اضغـط علـى الـزر ثـم اكتـب سؤالـك الدينـي مباشـرة</b>\n"
            f"<b>• هيجاوبـك البـوت باستخـدام الذكـاء الاصطناعـي</b>\n\n"
            f"<b>{DIV_LINE}</b>\n\n"
            f"<b>{NUM4} قنـاة البـوت</b>\n\n"
            f"<b>• تابـع قنـاة البـوت للحصـول علـى اخـر التحديثـات والمحتـوى الدينـي</b>\n\n"
            f"<b>{DIV_LINE}</b>\n\n"
            f"<b>• للبـدء مـن جديـد في اي وقـت ارسـل {WAVE} /start</b>"
        )
        await query.edit_message_text(
            text=faq_text,
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

    elif query.data == "channel":
        await query.edit_message_text(
            text=f"<b>{INFO} قنـاة البـوت\n\nقريبـا...</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if await sched_text_handler(update, context):
        return

    if context.user_data.get("state") != WAITING_QUESTION:
        return

    QUESTION = ce("5783013214539225637", "❔")
    question = update.message.text
    thinking_msg = await update.message.reply_text(
        f"<b>{CLOCK} جـاري البحـث عـن الاجابـة...</b>",
        parse_mode="HTML"
    )

    try:
        answer = await ask_openrouter(question)
    except Exception as e:
        logger.error(f"[OpenRouter Error] {type(e).__name__}: {e}")
        answer = "<b>حـدث خطـا اثنـاء الاتصـال بالخادم. حـاول مـرة اخـرى.</b>"

    await thinking_msg.edit_text(
        text=(
            f"<b>{QUESTION} سؤالـك :</b>\n"
            f"<blockquote>{html.escape(question)}</blockquote>\n\n"
            f"<b>{PEN} الاجابـة :</b>\n{answer}"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("سؤال آخـر",       callback_data="questions", icon_custom_emoji_id="5382187118216879236")],
            [InlineKeyboardButton("رجـوع للقائمـة", callback_data="back_main", icon_custom_emoji_id="5960671702059848143")],
        ]),
    )
    context.user_data.pop("state", None)

async def ask_openrouter(question: str) -> str:
    system_prompt = (
        "انت مساعد اسلامي متخصص في الاجابة على الاسئلة الدينية الاسلامية فقط.\n"
        "قواعدك:\n"
        "1. اجب فقط على الاسئلة المتعلقة بالقران الكريم والسنة النبوية والفقه الاسلامي والعقيدة والاخلاق والتاريخ الاسلامي.\n"
        "2. اذا كان السؤال غير ديني، اعتذر بلطف واخبر المستخدم انك متخصص في الاسئلة الدينية الاسلامية فقط.\n"
        "3. اجب باللغة العربية دايما.\n"
        "4. ادعم اجاباتك بالايات القرانية والاحاديث النبوية عند الامكان.\n"
        "5. كن موضوعيا ومختصرا وواضحا."
    )
    client = AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    response = await client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": question},
        ],
        timeout=30.0,
    )
    return response.choices[0].message.content

async def post_init(application: Application):
    
    db      = Database.get()
    roles   = RolesService()
    sched   = SchedulerService.get()

    await db.init()

    if INITIAL_OWNER_ID and not await db.is_owner(INITIAL_OWNER_ID):
        try:
            user_info = await application.bot.get_chat(INITIAL_OWNER_ID)
            full_name = user_info.full_name or str(INITIAL_OWNER_ID)
            username  = user_info.username or ""
        except Exception:
            full_name = str(INITIAL_OWNER_ID)
            username  = ""
        await roles.add_owner(INITIAL_OWNER_ID, username, full_name)
        logger.info(f"✅ تمت إضافة المالك الأولي: {INITIAL_OWNER_ID}")

    set_bot_app(application)

    sched.start()

    await sched.restore_all()

    ModuleRegistry.get()

    logger.info("✅ البوت جاهز تماما")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN غير موجود في Secrets")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        # مهلات أطول لمواجهة بطء الشبكة مع خوادم تليجرام
        .get_updates_read_timeout(60)
        .get_updates_connect_timeout(30)
        .get_updates_pool_timeout(30)
        .get_updates_write_timeout(60)
        .read_timeout(30)
        .connect_timeout(15)
        .build()
    )

    app.add_error_handler(error_handler)

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("owners",      cmd_owners),      group=0)
    app.add_handler(CommandHandler("addowner",    cmd_addowner),    group=0)
    app.add_handler(CommandHandler("removeowner", cmd_removeowner), group=0)
    app.add_handler(CommandHandler("admins",      cmd_admins),      group=0)
    app.add_handler(CommandHandler("addadmin",    cmd_addadmin),    group=0)
    app.add_handler(CommandHandler("removeadmin", cmd_removeadmin), group=0)
    app.add_handler(CommandHandler("setperms",    cmd_setperms),    group=0)
    app.add_handler(CommandHandler("panel",       cmd_panel),       group=0)
    app.add_handler(CommandHandler("devpanel",    cmd_devpanel),    group=0)

    app.add_handler(CallbackQueryHandler(panel_callback_handler,      pattern=r"^cp\|"), group=0)
    app.add_handler(CallbackQueryHandler(devpanel_callback_handler,   pattern=r"^dv\|"), group=0)

    app.add_handler(CallbackQueryHandler(sched_callback_handler,  pattern=r"^sch\|"), group=0)

    app.add_handler(CallbackQueryHandler(button_handler), group=1)

    app.add_handler(ChatMemberHandler(my_chat_member_handler,
                                      ChatMemberHandler.MY_CHAT_MEMBER), group=0)

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, message_handler
    ), group=1)

    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
