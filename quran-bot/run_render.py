import os, threading, logging
logger = logging.getLogger(__name__)

def run_flask():
    from server import app as flask_app
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🌐 السيرفر يعمل على المنفذ {port}...")
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    from bot import main as bot_main
    bot_main()
