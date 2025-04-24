import os
import json
from jinja2 import Environment, FileSystemLoader
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

# Этапы диалога
NAME, PRICE, DESCRIPTION, IMAGE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь /new чтобы добавить новый товар.")

async def new_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи название товара:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Теперь введи цену:")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    await update.message.reply_text("Теперь введи описание:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Пришли фото товара:")
    return IMAGE

async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_path = f"public/{file.file_unique_id}.jpg"
    await file.download_to_drive(image_path)

    product = {
        "name": context.user_data["name"],
        "price": context.user_data["price"],
        "description": context.user_data["description"],
        "image": image_path.replace("public/", "")
    }

    # Сохраняем продукт в JSON
    products = []
    if os.path.exists("products.json"):
        with open("products.json", "r", encoding="utf-8") as f:
            try:
                products = json.load(f)
            except json.JSONDecodeError:
                products = []

    products.append(product)

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    # Генерируем HTML
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("Template.html")
    html_content = template.render(products=products)

    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    await update.message.reply_text("Товар добавлен и сайт обновлён!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token("7772105188:AAGsjeL4YIBWbTDcMtmzYimwawV8ALbhn7g").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new", new_product)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            IMAGE: [MessageHandler(filters.PHOTO, get_image)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
