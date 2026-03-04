import json
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def load_shops():
    with open("shops.json", "r", encoding="utf-8") as f:
        return json.load(f)


def shop_keyboard(shop):
    buttons = []

    if shop.get("contact_tg"):
        buttons.append(
            [InlineKeyboardButton(text="💬 联系TG", url=shop["contact_tg"])]
        )

    if shop.get("contact_wa"):
        buttons.append(
            [InlineKeyboardButton(text="📱 WhatsApp", url=shop["contact_wa"])]
        )

    if shop.get("channel"):
        buttons.append(
            [InlineKeyboardButton(text="📢 查看频道", url=shop["channel"])]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def start(message: Message):
    shops = load_shops()

    args = message.text.split(maxsplit=1)
    key = args[1] if len(args) > 1 else None

    if not key:
        await message.answer("欢迎使用商家导航机器人")
        return

    shop = shops.get(key)

    if not shop:
        await message.answer("未找到该商家")
        return

    caption = f"{shop['name']}\n\n{shop['desc']}"

    keyboard = shop_keyboard(shop)

    await message.answer_photo(
        photo=shop["photo"],
        caption=caption,
        reply_markup=keyboard
    )


# 获取图片 file_id 用
@dp.message(lambda m: m.photo)
async def get_photo_id(message: Message):
    file_id = message.photo[-1].file_id
    await message.answer(
        f"图片file_id如下：\n\n{file_id}"
    )


async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()


async def handle_webhook(request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response(text="ok")


def create_app():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)
