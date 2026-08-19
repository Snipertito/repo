#!/usr/bin/env python3
"""فاحص حيوية البوت: إذا لم يستطع الاتصال بتليجرام بعد عدة محاولات،
يقتل عملية run.py ويترك السكربت الرئيسي (cron/systemd خارجي) يعيد تشغيلها.
يُشغَّل كل 2 دقيقة من run.py كخيط مراقبة."""
import os, time, logging, subprocess, sys
import requests

logger = logging.getLogger("health")

TOKEN = os.environ.get("BOT_TOKEN", "")
MAX_FAIL = 5
WAIT = 45  # ثانية بين المحاولات


def run_health():
    fails = 0
    while True:
        time.sleep(WAIT)
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=20)
            if r.ok:
                if fails > 0:
                    logger.info("✓ الاتصال بتليجرام عاد مجددًا (كانت %d محاولة فاشلة)", fails)
                fails = 0
            else:
                fails += 1
                logger.warning("✗ getMe ردّ بخطأ %s (%d/%d)", r.status_code, fails, MAX_FAIL)
        except Exception as e:
            fails += 1
            logger.warning("✗ فشل فحص getMe: %s (%d/%d)", type(e).__name__, fails, MAX_FAIL)

        if fails >= MAX_FAIL:
            logger.critical("✗ فشل الاتصال بتليجرام %d مرات متتالية — إعادة تشغيل البوت...", MAX_FAIL)
            my_pid = os.getpid()
            for line in subprocess.run(["pgrep", "-f", "python3 run.py"], capture_output=True, text=True).stdout.splitlines():
                pid = int(line.strip())
                if pid != my_pid:
                    os.kill(pid, 9)
                    logger.info("تم قتل عملية البوت %d", pid)
            time.sleep(3)
            # إعادة تشغيل البوت باستخدام نفس سكربت الإعادة الرسمي
            subprocess.Popen(
                ["bash", "/home/ubuntu/quran_bot/restart_clean.sh"],
                cwd="/home/ubuntu/quran_bot",
                stdout=open("/home/ubuntu/quran_bot/bot_restart.log", "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            logger.info("✓ تم إعادة تشغيل البوت تلقائيًا — إنهاء فاحص الحيوية القديم")
            os._exit(0)


if __name__ == "__main__":
    run_health()
