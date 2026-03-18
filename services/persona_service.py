import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class PersonaService:
    _instance: Optional['PersonaService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersonaService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.base_dir = "person"
        self.config_file = "person.set"
        self.current_persona_name: str = "Default"
        self.instructions: str = ""
        self.knowledge_base: str = ""
        self._initialized = True
        self.load_persona()

    def load_persona(self):
        """Читает person.set и загружает файлы персоны из папки."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.current_persona_name = f.read().strip()
            else:
                logger.warning(f"{self.config_file} not found. Using 'Default'.")
                self.current_persona_name = "Default"

            persona_path = os.path.join(self.base_dir, self.current_persona_name)
            
            # Пытаемся загрузить файлы
            instr_path = os.path.join(persona_path, "instructions.txt")
            kb_path = os.path.join(persona_path, "knowledge_base.txt")

            if not os.path.exists(instr_path) or not os.path.exists(kb_path):
                logger.error(f"Persona files for '{self.current_persona_name}' missing. Falling back to 'Default'.")
                self.current_persona_name = "Default"
                persona_path = os.path.join(self.base_dir, "Default")
                instr_path = os.path.join(persona_path, "instructions.txt")
                kb_path = os.path.join(persona_path, "knowledge_base.txt")

            with open(instr_path, "r", encoding="utf-8") as f:
                self.instructions = f.read().strip()
            
            with open(kb_path, "r", encoding="utf-8") as f:
                self.knowledge_base = f.read().strip()

            logger.info(f"Successfully loaded persona: {self.current_persona_name}")

        except Exception as e:
            logger.exception(f"Critical error loading persona: {e}")
            self.instructions = "Ты — вежливый помощник."
            self.knowledge_base = ""

    def get_persona_prompt(self) -> Dict[str, str]:
        """Возвращает системные инструкции и базу знаний."""
        return {
            "instructions": self.instructions,
            "knowledge_base": self.knowledge_base
        }

    def get_full_system_prompt(self) -> str:
        """Объединяет инструкции и базу знаний в один системный промпт."""
        return f"{self.instructions}\n\nБаза знаний:\n{self.knowledge_base}"

    def refresh(self):
        """Принудительное обновление кеша."""
        logger.info("Refreshing persona from disk...")
        self.load_persona()

# Singleton instance
persona_service = PersonaService()
