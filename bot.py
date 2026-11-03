import asyncio
import logging
import os
from urllib.parse import urlsplit

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message


def required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Заполните переменную окружения {name}")
    return value


def get_proxy_url():
    value = required_env("PROXY_URL")
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "socks5"}:
            raise ValueError
        if not parsed.hostname or parsed.port is None:
            raise ValueError
        if not 1 <= parsed.port <= 65535:
            raise ValueError
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError
    except ValueError:
        raise SystemExit(
            "PROXY_URL должен иметь формат http://host:port "
            "или socks5://host:port. "
            "Для авторизации используйте protocol://user:password@host:port."
        ) from None
    return value


async def main():
    token = required_env("BOT_TOKEN")
    proxy_url = get_proxy_url()

    session = AiohttpSession(proxy=proxy_url)
    bot = Bot(token=token, session=session)
    dispatcher = Dispatcher()

    @dispatcher.message(F.chat.type == "private")
    async def reply(message: Message):
        await message.answer("Бот работает")

    try:
        webhook = await bot.get_webhook_info()
        if webhook.url:
            raise SystemExit(
                "У бота настроен Telegram webhook. "
                "Согласуйте отключение webhook с владельцем текущей интеграции "
                "или используйте отдельного тестового бота."
            )

        logging.info(
            "Подключение через прокси установлено. "
            "Запускается опрос сообщений."
        )
        await dispatcher.start_polling(
            bot,
            allowed_updates=["message"],
            close_bot_session=False,
        )
    finally:
        await session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
