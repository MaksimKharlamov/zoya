import subprocess
import time
import sys
import datetime
import traceback

LOG_FILE = "bot_restarter.log"
BOT_FILENAME = "main.py"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def run_bot():
    restart_count = 0
    while True:
        try:
            restart_count += 1
            log(f"Запуск бота номер {restart_count}")
            process = subprocess.Popen([sys.executable, BOT_FILENAME])
            process.wait()
        except KeyboardInterrupt:
            log("Остановка по запросу пользователя")
            return
        except Exception as e:
            log(f"Критическая ошибка: {str(e)}\n{traceback.format_exc()}")
        log(f"Бот завершил работу. Перезапуск через 1 секунду...")
        time.sleep(1)

if __name__ == "__main__":

    try:
        log("Скрипт перезапуска запущен")
        run_bot()
    except Exception as e:
        log(f"Фатальная ошибка в скрипте перезапуска: {str(e)}")
    finally:
        log("Скрипт перезапуска бота остановлен")
