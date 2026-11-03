import asyncio
import os
import re
from urllib.parse import parse_qs, urlsplit

from telethon import TelegramClient, connection, events
from telethon.sessions import MemorySession


def required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Заполните переменную {name}")
    return value


def parse_proxy(link):
    try:
        url = urlsplit(link)
        if url.scheme != "tg" or url.netloc != "proxy":
            raise ValueError

        params = parse_qs(url.query)
        host, = params["server"]
        port_text, = params["port"]
        secret, = params["secret"]
        port = int(port_text)

        if not 1 <= port <= 65535:
            raise ValueError
        if not re.fullmatch(r"(?:dd)?[0-9a-f]{32}", secret, re.IGNORECASE):
            raise ValueError
    except (KeyError, ValueError):
        raise SystemExit(
            "TG_PROXY_URL: нужна полная ссылка tg://proxy с HEX-секретом "
            "из 32 символов, опционально с префиксом dd."
        ) from None

    return host, port, secret.lower()


async def main():
    token = required_env("BOT_TOKEN")
    proxy = parse_proxy(required_env("TG_PROXY_URL"))
    try:
        api_id = int(required_env("TG_API_ID"))
    except ValueError:
        raise SystemExit("TG_API_ID должен быть числом") from None

    client = TelegramClient(
        MemorySession(),
        api_id,
        required_env("TG_API_HASH"),
        connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=proxy,
    )

    @client.on(events.NewMessage(incoming=True))
    async def reply(event):
        if event.is_private:
            await event.reply("Бот работает")

    try:
        await client.start(bot_token=token)
        print("Бот подключён и ждёт сообщений в личном чате.", flush=True)
        await client.run_until_disconnected()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
