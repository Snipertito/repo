
import logging
from config import MAX_OWNERS, ALL_PERMISSIONS, DEFAULT_ADMIN_PERMISSIONS
from database import Database

logger = logging.getLogger(__name__)

class RolesService:

    def __init__(self):
        self.db = Database.get()

    async def add_owner(self, user_id: int, username: str, full_name: str,
                        added_by: int | None = None) -> tuple[bool, str]:
        
        if await self.db.is_owner(user_id):
            return False, "هذا المستخدم مالك بالفعل"

        count = await self.db.count_owners()
        if count >= MAX_OWNERS:
            return False, f"تم الوصول للحد الأقصى ({MAX_OWNERS} مالكين)"

        await self.db.add_owner(user_id, username, full_name, added_by)
        logger.info(f"تمت إضافة مالك جديد: {user_id} ({full_name})")
        return True, ""

    async def remove_owner(self, user_id: int, removed_by: int) -> tuple[bool, str]:
        
        if not await self.db.is_owner(user_id):
            return False, "هذا المستخدم ليس مالكاً"

        count = await self.db.count_owners()
        if count <= 1 and user_id == removed_by:
            return False, "لا يمكنك إزالة نفسك وأنت المالك الوحيد"

        await self.db.remove_owner(user_id)
        logger.info(f"تمت إزالة المالك: {user_id} بواسطة {removed_by}")
        return True, ""

    async def is_owner(self, user_id: int) -> bool:
        return await self.db.is_owner(user_id)

    async def get_owners(self) -> list[dict]:
        return await self.db.get_owners()

    async def add_admin(self, user_id: int, username: str, full_name: str,
                        permissions: dict | None = None,
                        added_by: int | None = None) -> tuple[bool, str]:
        if await self.db.is_owner(user_id):
            return False, "هذا المستخدم مالك، لا يحتاج لإضافته كمشرف"

        await self.db.add_bot_admin(
            user_id, username, full_name,
            permissions or DEFAULT_ADMIN_PERMISSIONS,
            added_by
        )
        logger.info(f"تمت إضافة مشرف: {user_id} ({full_name})")
        return True, ""

    async def remove_admin(self, user_id: int) -> tuple[bool, str]:
        if not await self.db.is_bot_admin(user_id):
            return False, "هذا المستخدم ليس مشرفاً"
        await self.db.remove_bot_admin(user_id)
        logger.info(f"تمت إزالة المشرف: {user_id}")
        return True, ""

    async def is_admin(self, user_id: int) -> bool:
        return await self.db.is_bot_admin(user_id)

    async def is_owner_or_admin(self, user_id: int) -> bool:
        return await self.is_owner(user_id) or await self.is_admin(user_id)

    async def get_admins(self) -> list[dict]:
        return await self.db.get_admins()

    async def has_permission(self, user_id: int, permission: str) -> bool:
        
        if await self.is_owner(user_id):
            return True
        perms = await self.db.get_admin_permissions(user_id)
        return bool(perms.get(permission, False))

    async def update_admin_permissions(self, user_id: int, permissions: dict) -> tuple[bool, str]:
        if not await self.db.is_bot_admin(user_id):
            return False, "هذا المستخدم ليس مشرفاً"

        invalid = [k for k in permissions if k not in ALL_PERMISSIONS]
        if invalid:
            return False, f"صلاحيات غير معروفة: {', '.join(invalid)}"

        await self.db.update_admin_permissions(user_id, permissions)
        return True, ""
