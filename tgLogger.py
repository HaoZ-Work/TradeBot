import logging
import asyncio
from telegram import Bot

class TelegramBotHandler(logging.Handler):
    def __init__(self, bot_token, chat_id):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=self.bot_token)
        self.loop = asyncio.get_event_loop()

    async def send_message(self, log_entry):
        await self.bot.send_message(chat_id=self.chat_id, text=log_entry)

    def emit(self, record):
        log_entry = self.format(record)
        if self.loop.is_running():
            asyncio.create_task(self.send_message(log_entry))
        else:
            self.loop.run_until_complete(self.send_message(log_entry))

