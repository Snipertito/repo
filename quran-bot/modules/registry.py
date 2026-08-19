
import logging
from modules.base import BaseModule

logger = logging.getLogger(__name__)

class ModuleRegistry:

    _instance: "ModuleRegistry | None" = None

    def __init__(self):
        self._modules: dict[str, BaseModule] = {}

    @classmethod
    def get(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_modules()
        return cls._instance

    def _load_modules(self):
        
        from modules.devpanel.handler      import DevPanelModule
        from modules.permissions.handler import PermissionsModule
        from modules.azkar.handler       import AzkarModule
        from modules.quran_text.handler  import QuranTextModule
        from modules.quran_audio.handler import QuranAudioModule

        for mod_class in [DevPanelModule, PermissionsModule, AzkarModule, QuranTextModule, QuranAudioModule]:
            instance = mod_class()
            self._modules[instance.KEY] = instance
            logger.debug(f"✅ وحدة محمّلة: {instance.KEY}")

        logger.info(f"✅ {len(self._modules)} وحدة محمّلة في Registry")

    def get_module(self, key: str) -> BaseModule | None:
        return self._modules.get(key)

    def all_modules(self) -> list[BaseModule]:
        
        order = ["devpanel", "permissions", "azkar", "quran_text", "quran_audio"]
        result = []
        for k in order:
            if k in self._modules:
                result.append(self._modules[k])
        
        for k, v in self._modules.items():
            if k not in order:
                result.append(v)
        return result
