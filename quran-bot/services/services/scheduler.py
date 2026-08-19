
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from database import Database
from utils.helpers import interval_to_seconds

logger = logging.getLogger(__name__)

_bot_app = None

def set_bot_app(app):
    global _bot_app
    _bot_app = app

def get_bot():
    if _bot_app is None:
        raise RuntimeError("Bot application not set in scheduler")
    return _bot_app.bot

class SchedulerService:

    _instance: "SchedulerService | None" = None

    def __init__(self):
        self.db        = Database.get()
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._jobs: dict[int, str] = {}  

    @classmethod
    def get(cls) -> "SchedulerService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler بدأ")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def restore_all(self):
        
        schedules = await self.db.get_active_schedules()
        count = 0
        for sched in schedules:
            try:
                await self._schedule_job(sched)
                count += 1
            except Exception as e:
                logger.error(f"خطأ في استعادة الجدول {sched['id']}: {e}")
        logger.info(f"✅ تمت استعادة {count} مهمة مجدولة")

    async def add_schedule(self, chat_id: int, module_key: str, job_data: dict,
                           interval_type: str, interval_value: int,
                           start_time: str, end_time: str | None,
                           created_by: int) -> int:
        
        schedule_id = await self.db.add_schedule(
            chat_id, module_key, job_data,
            interval_type, interval_value,
            start_time, end_time, created_by
        )
        sched = {
            "id":             schedule_id,
            "chat_id":        chat_id,
            "module_key":     module_key,
            "job_data":       job_data,
            "interval_type":  interval_type,
            "interval_value": interval_value,
            "start_time":     start_time,
            "end_time":       end_time,
        }
        await self._schedule_job(sched)
        return schedule_id

    async def cancel_schedule(self, schedule_id: int):
        
        await self.db.deactivate_schedule(schedule_id)
        job_id = self._jobs.pop(schedule_id, None)
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
        logger.info(f"تم إلغاء الجدول {schedule_id}")

    async def _schedule_job(self, sched: dict):
        
        schedule_id    = sched["id"]
        interval_type  = sched["interval_type"]
        interval_value = sched["interval_value"]
        start_time     = sched["start_time"]
        end_time       = sched.get("end_time")

        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            except ValueError:
                start_dt = datetime.utcnow() + timedelta(seconds=60)

        end_dt = None
        if end_time:
            try:
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
                except ValueError:
                    end_dt = None

        seconds = interval_to_seconds(interval_type, interval_value)

        now = datetime.utcnow()
        next_run = start_dt
        if next_run <= now:
            elapsed = (now - start_dt).total_seconds()
            periods = int(elapsed / seconds) + 1
            next_run = start_dt + timedelta(seconds=seconds * periods)

        if end_dt and next_run > end_dt:
            logger.info(f"الجدول {schedule_id} انتهى وقته")
            await self.db.deactivate_schedule(schedule_id)
            return

        trigger = IntervalTrigger(
            seconds=seconds,
            start_date=next_run,
            end_date=end_dt,
            timezone="UTC"
        )

        job_id = f"sched_{schedule_id}"
        self.scheduler.add_job(
            _execute_scheduled_job,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={"schedule_id": schedule_id, "sched": sched}
        )
        self._jobs[schedule_id] = job_id
        logger.info(f"✅ جدول {schedule_id} مسجَّل، التشغيل التالي: {next_run}")

async def _execute_scheduled_job(schedule_id: int, sched: dict):
    
    from modules.registry import ModuleRegistry

    try:
        bot     = get_bot()
        db      = Database.get()
        module  = ModuleRegistry.get().get_module(sched["module_key"])

        if module is None:
            logger.error(f"الوحدة '{sched['module_key']}' غير موجودة")
            return

        end_time = sched.get("end_time")
        if end_time:
            try:
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                if datetime.utcnow() > end_dt:
                    await db.deactivate_schedule(schedule_id)
                    svc = SchedulerService.get()
                    svc._jobs.pop(schedule_id, None)
                    return
            except ValueError:
                pass

        await module.execute_scheduled_job(bot, sched["chat_id"], sched["job_data"])

        next_run = (datetime.utcnow() + timedelta(
            seconds=interval_to_seconds(sched["interval_type"], sched["interval_value"])
        )).strftime("%Y-%m-%d %H:%M:%S")
        await db.update_schedule_last_run(schedule_id, next_run)
        logger.info(f"✅ مهمة {schedule_id} نُفِّذت بنجاح")

    except Exception as e:
        logger.error(f"خطأ في تنفيذ المهمة {schedule_id}: {e}", exc_info=True)
