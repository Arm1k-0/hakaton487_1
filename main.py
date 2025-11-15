from bot import MaxBot
import time


def main():
    bot = MaxBot("f9LHodD0cOJUQpSlJfzSMrL4QsafDBZzFUpfqRiVtADDJZA7iZoj-zRn3m9s__Edi_lO9O8QYP_jMo7jzkOx")

    print("Бот СоседиРядом запущен для MAX")
    print("Ожидание сообщений...")

    last_update_id = None

    while True:
        try:
            updates_data = {
                "offset": last_update_id,
                "timeout": 30
            }

            updates = bot.send_api_request("getUpdates", updates_data)

            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    if "message" in update:
                        bot.process_message(update["message"])
                    last_update_id = update["update_id"] + 1

            time.sleep(1)

        except KeyboardInterrupt:
            print("Бот остановлен")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()