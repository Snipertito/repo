
import threading
import logging

logger = logging.getLogger(__name__)

def run_flask():
    from server import app as flask_app
    logger.info("🌐 السيرفر يعمل على المنفذ 5000...")
    flask_app.run(host="0.0.0.0", port=5000, use_reloader=False)

if __name__ == "__main__":

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # خيط مراقبة حيوية البوت (يعيد تشغيله عند انقطاع طويل مع تليجرام)
    from health_check import run_health
    threading.Thread(target=run_health, daemon=True).start()

    from bot import main as bot_main
    bot_main()
