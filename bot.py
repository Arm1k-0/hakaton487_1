import requests
import json
from database import Database


class MaxBot:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://max.ru/t487_hakaton_bot"
        self.db = Database()
        self.user_states = {}

    def send_api_request(self, method, data):
        url = f"{self.api_url}/{method}"
        data["token"] = self.token

        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except:
            return None

    def send_message(self, chat_id, text, keyboard=None):
        data = {
            "chat_id": str(chat_id),
            "text": text
        }
        if keyboard:
            data["keyboard"] = keyboard
        return self.send_api_request("sendMessage", data)

    def create_keyboard(self, buttons, one_time=True):
        keyboard_buttons = []
        for row in buttons:
            if isinstance(row, list):
                button_row = [{"text": btn} for btn in row]
                keyboard_buttons.append(button_row)
            else:
                keyboard_buttons.append([{"text": row}])

        return {
            "one_time": one_time,
            "buttons": keyboard_buttons
        }

    def create_location_keyboard(self):
        return {
            "one_time": True,
            "buttons": [[{
                "text": "📍 Определить местоположение",
                "request_location": True
            }]]
        }

    def handle_start(self, chat_id, user_data):
        self.db.add_user(chat_id, user_data.get("username"), user_data.get("first_name"), user_data.get("last_name"))
        self.user_states[chat_id] = {}

        welcome_text = "👋 Добро пожаловать в бот «СоседиРядом»!\n\nЯ помогу найти помощь или стать волонтером в вашем районе.\n\nВыберите действие:"

        keyboard = self.create_keyboard([
            ["📍 Определить местоположение"],
            ["🙋 Мне нужна помощь", "🤝 Я могу оказать помощь"],
            ["📊 Мои активность", "🗑️ Удалить запросы"],
            ["👥 Найти помощь рядом"]
        ])

        self.send_message(chat_id, welcome_text, keyboard)

    def handle_location(self, chat_id, lat, lon):
        self.db.update_user_location(chat_id, lat, lon)
        self.send_message(chat_id, "✅ Отлично! Местоположение сохранено. Теперь я могу искать помощь в вашем районе!")

    def handle_need_help(self, chat_id):
        self.user_states[chat_id] = {"action": "need_help", "step": "category"}

        categories = [
            ["🛒 Сходить в магазин", "💊 Купить лекарства"],
            ["🔧 Мелкий ремонт", "💬 Пообщаться"],
            ["🐕 Выгулять собаку", "📦 Доставить продукты"],
            ["❓ Другое", "🔙 Главное меню"]
        ]

        self.send_message(chat_id, "🙋 Выберите категорию помощи:", self.create_keyboard(categories))

    def handle_can_help(self, chat_id):
        self.user_states[chat_id] = {"action": "can_help", "step": "category"}

        categories = [
            ["🛒 Сходить в магазин", "💊 Купить лекарства"],
            ["🔧 Мелкий ремонт", "💬 Пообщаться"],
            ["🐕 Выгулять собаку", "📦 Доставить продукты"],
            ["❓ Другое", "🔙 Главное меню"]
        ]

        self.send_message(chat_id, "🤝 Выберите категорию, в которой можете помочь:", self.create_keyboard(categories))

    def handle_category(self, chat_id, category_text):
        user_state = self.user_states.get(chat_id, {})

        if category_text == "🔙 Главное меню":
            self.handle_start(chat_id, {})
            return

        category_map = {
            "🛒 Сходить в магазин": "shopping",
            "💊 Купить лекарства": "pharmacy",
            "🔧 Мелкий ремонт": "repairs",
            "💬 Пообщаться": "communication",
            "🐕 Выгулять собаку": "walk",
            "📦 Доставить продукты": "delivery",
            "❓ Другое": "other"
        }

        category_key = category_map.get(category_text)
        if category_key:
            user_state["category"] = category_key
            user_state["step"] = "details"

            if user_state["action"] == "need_help":
                prompt = "💬 Опишите подробнее, какая именно помощь вам нужна:"
            else:
                prompt = "💬 Опишите, как именно вы можете помочь:"

            self.send_message(chat_id, prompt, self.create_keyboard([["🔙 Главное меню"]]))

    def handle_details(self, chat_id, details_text):
        user_state = self.user_states.get(chat_id, {})

        if details_text == "🔙 Главное меню":
            self.handle_start(chat_id, {})
            return

        category_key = user_state.get("category")
        action = user_state.get("action")

        if action == "need_help":
            request_id = self.db.create_help_request(chat_id, category_key, details_text, details_text)
            volunteers = self.db.find_matches(chat_id, category_key)

            response = f"✅ Ваш запрос помощи сохранен!\n\n📝 Детали: {details_text}"
            if volunteers:
                response += f"\n\n🎉 Нашлось {len(volunteers)} волонтеров готовых помочь!"
            else:
                response += "\n\nКак только волонтеры появятся nearby, я вас уведомлю!"

        else:
            offer_id = self.db.create_help_offer(chat_id, category_key, details_text, details_text)
            requests = self.db.find_help_requests_nearby(chat_id, category_key)

            response = f"✅ Вы зарегистрированы как волонтер!\n\n📝 Детали: {details_text}"
            if requests:
                response += f"\n\n🎉 Нашлось {len(requests)} запросов помощи nearby!"
            else:
                response += "\n\nСпасибо за готовность помогать! ❤️"

        self.send_message(chat_id, response)
        self.user_states[chat_id] = {}

    def handle_my_activity(self, chat_id):
        requests = self.db.get_user_requests(chat_id)
        offers = self.db.get_user_offers(chat_id)

        response = "📊 Ваша активность:\n\n"

        if requests:
            response += "🙋 Мои запросы помощи:\n"
            for req in requests:
                status = "✅" if req["status"] == "completed" else "🟡"
                response += f"{status} {req['description']}\n"
                if req.get("details"):
                    response += f"   📝 {req['details']}\n"

        if offers:
            response += "\n🤝 Мои предложения помощи:\n"
            for offer in offers:
                status = "✅" if offer["status"] == "completed" else "🟡"
                response += f"{status} {offer['description']}\n"
                if offer.get("details"):
                    response += f"   📝 {offer['details']}\n"

        if not requests and not offers:
            response += "У вас пока нет активных запросов или предложений."

        self.send_message(chat_id, response)

    def handle_find_help(self, chat_id):
        requests = self.db.find_help_requests_nearby(chat_id)

        if not requests:
            self.send_message(chat_id, "😔 Поблизости пока нет запросов помощи.")
            return

        response = f"🎉 Найдено запросов помощи nearby: {len(requests)}\n\n"
        for req in requests[:5]:
            response += f"🙋 {req['description']}\n👤 {req['first_name']}\n💬 {req['details']}\n\n"

        response += "Хотите помочь кому-то из них? Нажмите '🤝 Я могу оказать помощь'"
        self.send_message(chat_id, response)

    def handle_delete_requests(self, chat_id):
        requests = self.db.get_user_requests(chat_id)
        offers = self.db.get_user_offers(chat_id)

        active_requests = [r for r in requests if r["status"] == "active"]
        active_offers = [o for o in offers if o["status"] == "active"]

        if not active_requests and not active_offers:
            self.send_message(chat_id, "❌ У вас нет активных запросов или предложений для удаления.")
            return

        keyboard_buttons = []
        for req in active_requests:
            keyboard_buttons.append([{"text": f"🗑️ Запрос: {req['description'][:30]}..."}])

        for offer in active_offers:
            keyboard_buttons.append([{"text": f"🗑️ Предложение: {offer['description'][:30]}..."}])

        keyboard = {"one_time": True, "buttons": keyboard_buttons}
        self.send_message(chat_id, "🗑️ Выберите что хотите удалить:", keyboard)

    def process_message(self, message):
        chat_id = message.get("from", {}).get("id")
        text = message.get("text", "").strip()
        user_data = message.get("from", {})

        if not chat_id:
            return

        if text == "/start":
            self.handle_start(chat_id, user_data)

        elif message.get("location"):
            location = message["location"]
            self.handle_location(chat_id, location["latitude"], location["longitude"])

        elif text == "🙋 Мне нужна помощь":
            self.handle_need_help(chat_id)

        elif text == "🤝 Я могу оказать помощь":
            self.handle_can_help(chat_id)

        elif text == "📊 Мои активность":
            self.handle_my_activity(chat_id)

        elif text == "🗑️ Удалить запросы":
            self.handle_delete_requests(chat_id)

        elif text == "👥 Найти помощь рядом":
            self.handle_find_help(chat_id)

        elif text == "🔙 Главное меню":
            self.handle_start(chat_id, user_data)

        else:
            user_state = self.user_states.get(chat_id, {})

            if user_state.get("step") == "category":
                self.handle_category(chat_id, text)

            elif user_state.get("step") == "details":
                self.handle_details(chat_id, text)

            else:
                self.send_message(chat_id, "Используйте кнопки для навигации 👇")