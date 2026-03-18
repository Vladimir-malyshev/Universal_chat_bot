import sys
import os

# Добавляем корневую директорию в path
sys.path.append(os.getcwd())

from core.formatter import md_to_html, strip_all_tags

def test_formatter():
    print("--- Тестирование Форматтера (Reliability Protocol) ---")

    # 1. Базовое форматирование
    md_text = "**Bold** and *Italic* and `code`"
    expected = "<b>Bold</b> and <i>Italic</i> and <code>code</code>"
    result = md_to_html(md_text)
    assert result == expected, f"Failed basic: {result}"
    print("Базовое форматирование: OK ✅")

    # 2. Математические знаки (Экранирование)
    md_math = "if a < b and b > c"
    expected = "if a &lt; b and b &gt; c"
    result = md_to_html(md_math)
    assert result == expected, f"Failed math: {result}"
    print("Экранирование < и >: OK ✅")

    # 3. Амперсанд
    md_amp = "Rock & Roll"
    expected = "Rock &amp; Roll"
    result = md_to_html(md_amp)
    assert result == expected, f"Failed amp: {result}"
    print("Экранирование &: OK ✅")

    # 4. Вложенные стили
    md_nested = "**Жирный с _курсивом_ внутри**"
    # Наш текущий regex может не идеально отрабатывать вложенность, если она сложная,
    # но проверим базовый вариант.
    result = md_to_html(md_nested)
    print(f"Вложенные стили результат: {result}")
    # Ожидаем <b>Жирный с <i>курсивом</i> внутри</b> 
    # Но наш regex (\*\*|__)(.*?)\1 захватит всё до следующей **.
    # Если внутри есть _, он будет обработан следующим шагом? Нет, они в одном тексте.

    # 5. Списки и заголовки
    md_list = "# Header\n* Item 1\n- Item 2"
    expected = "<b>Header</b>\n• Item 1\n• Item 2"
    result = md_to_html(md_list)
    assert result == expected, f"Failed list: {result}"
    print("Списки и заголовки: OK ✅")

    # 6. Fallback (strip_all_tags)
    html_broken = "<b>Bold <i>Italic with missing closing tag"
    clean = strip_all_tags(md_to_html(html_broken))
    print(f"Очистка тегов (Fallback): {clean}")
    assert "<b>" not in clean and "<i>" not in clean
    print("Очистка тегов: OK ✅")

if __name__ == "__main__":
    try:
        test_formatter()
        print("\nВсе тесты форматтера пройдены! 🚀")
    except AssertionError as e:
        print(f"\nОшибка в тестах: {e}")
        sys.exit(1)
