import os
import re
import sys
import subprocess
import httpx
from dotenv import load_dotenv

def main():
    # 1. Читаем .env стандартной библиотекой
    load_dotenv()
    
    tg_token = os.getenv("TG_BOT_TOKEN")
    if not tg_token:
        print("[Ошибка] TG_BOT_TOKEN не найден в .env!")
        sys.exit(1)
        
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"[1/3] Запуск localtunnel на порту {port}...")
    
    # 2. Запускаем npx
    cmd = ["npx.cmd" if os.name == "nt" else "npx", "lt", "--port", str(port)]
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True, 
        bufsize=1
    )
    
    url = None
    print("[2/3] Ожидание внешнего URL от localtunnel...")
    
    # 3. Читаем вывод localtunnel в реальном времени, ищем ссылку
    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if not line:
            continue
            
        print(f"  [lt] {line}")
        match = re.search(r'(https://[a-zA-Z0-9-]+\.loca\.lt)', line)
        if match:
            url = match.group(1).strip()
            # Как только нашли URL, выходим из цикла чтения
            break
            
    if not url:
        print("[Ошибка] Не удалось получить URL. Проверьте соединение или npm/npx.")
        process.kill()
        sys.exit(1)
        
    print(f"\n-> Успешно! Получен URL: {url}")
    
    # 4. Регистрируем вебхук
    webhook_url = f"{url}/webhook/telegram"
    print(f"[3/3] Регистрация Webhook в Telegram: {webhook_url}")
    
    tele_api = f"https://api.telegram.org/bot{tg_token}/setWebhook"
    try:
        response = httpx.get(tele_api, params={"url": webhook_url}, timeout=15.0)
        
        if response.status_code == 200 and response.json().get("ok"):
            print("-> Webhook успешно зарегистрирован!")
            print(f"   Детали: {response.json().get('description')}")
        else:
            print("-> Ошибка при регистрации Webhook:")
            print(response.text)
    except Exception as e:
        print(f"-> Ошибка HTTP запроса: {e}")
        
    print("\nВсе готово! Localtunnel пробрасывает порт. Нажмите Ctrl+C, чтобы остановить его.")
    
    # Туннель продолжает работать, в это время мы выводим оставшиеся логи если они есть
    try:
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                print(f"  [lt] {line.strip()}")
        process.wait()
    except KeyboardInterrupt:
        print("\nОстановка localtunnel...")
        process.kill()

if __name__ == "__main__":
    main()
