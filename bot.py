import logging
import os
import ai
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
load_dotenv()

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

import prompt

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = prompt.prompt_user(user_input=update.message.text, point=ai.record_point, level=round(int(ai.record_point)/2000))
    chatgpt_response = await ai.ai_chat(user_message, model='gpt-4o')
    await update.message.reply_text(chatgpt_response)
    await ai.run_conversation(chatgpt_response)



async def handle_count(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    # chatgpt_response = await ai.ai_enhance(user_message)
    chatgpt_response = await ai.ai_chat(user_message, model='gpt-4o')
    await update.message.reply_text(chatgpt_response)
    return ConversationHandler.END



COUNT = 0

def main() -> None:
    """Start the bot."""
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(~filters.COMMAND, echo))

    # conv_handler = ConversationHandler(
    #     entry_points=[
    #         CommandHandler('count', enhance_command),
    #     ],
    #     states={
    #         COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_count)],
    #     },
    #     fallbacks=[],
    # )
    # application.add_handler(conv_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()