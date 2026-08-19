
import logging
from config import (
    PANEL_ACCESS_ALL_ADMINS, PANEL_ACCESS_SPECIFIC, PANEL_ACCESS_OWNER_ONLY
)
from database import Database
from utils.helpers import is_group_admin, is_group_creator
from services.roles import RolesService

logger = logging.getLogger(__name__)

class PanelAccessService:

    def __init__(self):
        self.db    = Database.get()
        self.roles = RolesService()

    async def can_access_panel(self, bot, chat_id: int, user_id: int) -> bool:

        if await self.roles.is_owner(user_id):
            return True

        if not await is_group_admin(bot, chat_id, user_id):
            return False

        mode = await self.db.get_panel_access(chat_id)

        if mode == PANEL_ACCESS_ALL_ADMINS:
            return True

        if mode == PANEL_ACCESS_OWNER_ONLY:
            return await is_group_creator(bot, chat_id, user_id)

        if mode == PANEL_ACCESS_SPECIFIC:
            access = await self.db.get_group_panel_access_type(chat_id, user_id)
            if access == "denied":
                return False
            if access == "allowed":
                return True
            
            return await is_group_creator(bot, chat_id, user_id)

        return False

    async def set_mode(self, chat_id: int, mode: str):
        await self.db.set_panel_access(chat_id, mode)

    async def allow_user(self, chat_id: int, user_id: int):
        await self.db.add_group_panel_admin(chat_id, user_id, "allowed")

    async def deny_user(self, chat_id: int, user_id: int):
        await self.db.add_group_panel_admin(chat_id, user_id, "denied")

    async def remove_user(self, chat_id: int, user_id: int):
        await self.db.remove_group_panel_admin(chat_id, user_id)

    async def get_specific_list(self, chat_id: int) -> list[dict]:
        return await self.db.get_group_panel_admins(chat_id)

    async def get_mode(self, chat_id: int) -> str:
        return await self.db.get_panel_access(chat_id)
