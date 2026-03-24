# -*- coding: utf-8 -*-
"""
Скрипт проверки подключения к Яндекс Диску.
Запустите: venv/Scripts/python.exe bot/test_disk.py
"""

import sys
from pathlib import Path

# Добавляем bot в путь
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import YANDEX_DISK_TOKEN, YANDEX_DISK_FILE_PATH
    import yadisk
except Exception as e:
    print(f"Ошибка загрузки: {e}")
    sys.exit(1)

def main():
    print("Проверка Яндекс Диска...")
    print(f"Путь к файлу: {YANDEX_DISK_FILE_PATH}")
    print()
    
    try:
        client = yadisk.Client(token=YANDEX_DISK_TOKEN)
        
        # Проверка токена
        if not client.check_token():
            print("ОШИБКА: Токен недействителен или истёк.")
            return
        
        print("Токен действителен.")
        
        disk_path = YANDEX_DISK_FILE_PATH
        if not disk_path.startswith("/"):
            disk_path = "/" + disk_path
        
        # Проверка существования файла
        if client.exists(disk_path):
            print(f"Файл существует: {disk_path}")
            import tempfile
            tmp = tempfile.mktemp(suffix=".xlsx")
            client.download(disk_path, tmp)
            print("Файл успешно читается.")
        else:
            print(f"Файл не существует. Будет создан при первой заявке.")
            # Проверяем, можем ли создать папку
            parts = [p for p in disk_path.split("/") if p]
            if len(parts) > 1:
                parent = "/" + "/".join(parts[:-1])
                if not client.exists(parent):
                    print(f"Создаём папку: {parent}")
                    client.makedirs(parent)
                    print("Папка создана.")
                else:
                    print(f"Родительская папка существует: {parent}")
        
        # Пробуем реальную запись (как при заявке)
        print()
        print("Тест записи заказа...")
        try:
            from sheets import append_order
            ok, _ = append_order(
                "Тест", "89001234567", "Окна Rehau Standard", "2",
                "ул. Примерная 1", "наличными при получении", "Тест",
                telegram_user_id=0
            )
            if ok:
                print("Заказ успешно сохранён!")
            else:
                print("Ошибка сохранения (смотрите логи выше).")
        except Exception as e:
            print(f"Ошибка: {e}")

        print()
        print("Проверка завершена.")
        
    except yadisk.exceptions.UnauthorizedError as e:
        print(f"ОШИБКА авторизации: {e}")
        print("Проверьте YANDEX_DISK_TOKEN. Токен мог истечь — получите новый.")
    except yadisk.exceptions.BadRequestError as e:
        print(f"ОШИБКА запроса: {e}")
    except yadisk.exceptions.ForbiddenError as e:
        print(f"ОШИБКА доступа: {e}")
        print("У приложения нет прав на запись. Добавьте «Запись в любом месте на диске».")
    except Exception as e:
        print(f"ОШИБКА: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
