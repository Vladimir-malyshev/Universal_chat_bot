import sys
import os

# Добавляем корневую папку в path для импортов
sys.path.append(os.getcwd())

from services.persona_service import persona_service

def test_persona_loading():
    print("--- Тестирование загрузки персон ---")
    
    # 1. Проверка загрузки по умолчанию
    prompt = persona_service.get_persona_prompt()
    print(f"Текущая персона: {persona_service.current_persona_name}")
    print(f"Инструкции (первые 50 симв.): {prompt['instructions'][:50]}...")
    
    # 2. Проверка обновления
    print("\nСоздаем новую персону 'Morpheus'...")
    os.makedirs("person/Morpheus", exist_ok=True)
    with open("person/Morpheus/instructions.txt", "w", encoding="utf-8") as f:
        f.write("Ты — Морфеус из Матрицы. Говори загадками.")
    with open("person/Morpheus/knowledge_base.txt", "w", encoding="utf-8") as f:
        f.write("Матрица повсюду. Она окружает нас.")
    
    with open("person.set", "w", encoding="utf-8") as f:
        f.write("Morpheus")
    
    persona_service.refresh()
    print(f"После обновления персона: {persona_service.current_persona_name}")
    print(f"Полный системный промпт:\n{persona_service.get_full_system_prompt()}")

    # 3. Возвращаем как было
    with open("person.set", "w", encoding="utf-8") as f:
        f.write("Default")
    persona_service.refresh()
    print(f"\nВозврат к: {persona_service.current_persona_name}")

if __name__ == "__main__":
    test_persona_loading()
