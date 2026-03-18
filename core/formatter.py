import re
import html
import logging

logger = logging.getLogger(__name__)

def md_to_html(text: str) -> str:
    """
    Конвертирует стандартный Markdown в HTML, поддерживаемый Telegram.
    Безопасно экранирует спецсимволы, кроме самих HTML-тегов.
    """
    if not text:
        return ""

    # 1. Сначала экранируем спецсимволы HTML
    # Telegram требует экранировать <, > и &
    text = html.escape(text, quote=False)

    # 2. Жирный: **текст** или __текст__ -> <b>текст</b>
    text = re.sub(r'(\*\*|__)(.*?)\1', r'<b>\2</b>', text)

    # 3. Курсив: *текст* или _текст_ -> <i>текст</i>
    # Используем \b для границ слов, чтобы не ломать курсив внутри слов с _ (но в MD это обычно не так)
    # Однако стандартный MD просит аккуратности.
    text = re.sub(r'(\*|_)(.*?)\1', r'<i>\2</i>', text)

    # 4. Код в строке: `текст` -> <code>текст</code>
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # 5. Многострочный код: ```текст``` -> <pre>текст</pre>
    text = re.sub(r'```(?:[a-z]*\n)?([\s\S]*?)```', r'<pre>\1</pre>', text)

    # 6. Ссылки: [текст](url) -> <a href="url">текст</a>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # 7. Заголовки: # Текст -> <b>Текст</b>
    text = re.sub(r'^#+\s+(.*)$', r'<b>\1</b>', text, flags=re.MULTILINE)

    # 8. Списки: * или - -> •
    text = re.sub(r'^\s*[\*\-]\s+(.*)$', r'• \1', text, flags=re.MULTILINE)

    return text

def strip_all_tags(text: str) -> str:
    """
    Удаляет все HTML-теги из текста. Используется как fallback.
    """
    if not text:
        return ""
    # Простое удаление всего, что похоже на теги
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
