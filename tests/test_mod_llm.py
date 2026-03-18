import sys
import os

sys.path.append(os.getcwd())

import mod_llm

def test_mod_llm():
    print("--- Тестирование mod_llm (Chutes) ---")
    
    default_id = mod_llm.get_default_model()
    print(f"Дефолтная модель: {default_id}")
    
    model_info = mod_llm.get_model_info(default_id)
    print(f"Инфо о модели: {model_info}")
    
    # Проверка обязательных полей
    required = ["id", "name", "context_length", "vision_support"]
    for field in required:
        if field in model_info:
            print(f"Поле {field}: OK")
        else:
            print(f"Ошибка: поле {field} отсутствует!")

    print(f"Base URL: {mod_llm.CHUTES_BASE_URL}")

if __name__ == "__main__":
    test_mod_llm()
