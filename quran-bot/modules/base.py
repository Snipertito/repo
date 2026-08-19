
from abc import ABC, abstractmethod
from telegram import InlineKeyboardButton, Bot

class BaseModule(ABC):

    KEY: str   = ""   
    NAME: str  = ""   
    EMOJI: str = ""   

    @abstractmethod
    async def handle_callback(
        self,
        update,
        context,
        chat_id: int,
        path: list[str]
    ) -> None:
        
        ...

    async def execute_scheduled_job(
        self,
        bot: Bot,
        chat_id: int,
        job_data: dict
    ) -> None:
        
        pass

    def get_menu_button(self, chat_id: int) -> InlineKeyboardButton:
        
        return InlineKeyboardButton(
            f"{self.EMOJI} {self.NAME}",
            callback_data=f"cp|{chat_id}|{self.KEY}"
        )

    def cb(self, chat_id: int, *parts: str) -> str:
        
        data = f"cp|{chat_id}|{self.KEY}"
        if parts:
            data += "|" + "|".join(str(p) for p in parts)
        assert len(data.encode()) <= 64, f"callback_data طويل جداً: {data}"
        return data
