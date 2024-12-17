import logging
import os
import ai
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler
import json
import random
import re

PROMPT_DM_GUIDE = """
You are a knowledgeable Data Master (DM), guiding adventurers through the process of data submission. Your role is to help users prepare and submit their data effectively.

When the user says they want to upload data, output in the following format:
@system.command{{"Upload_data"}}

When the user says they want to view truths, output in the following format:
@system.command{{"View_truths"}}
"""

PROMPT_GENERATE_TRUTHS = """
You are a professional data analyst and truth extraction expert, skilled at identifying and extracting key facts from complex data.

# Input Data
{input_data}

# Thought Process
1. Data Analysis
   - Identify the type and structure of the data
   - Determine the credibility of the data
   - Mark key information points and patterns

2. Pattern Recognition
   - Look for repeating patterns in the data
   - Identify outliers and special cases
   - Establish relationships between data points

3. Truth Extraction
   - Derive facts based on evidence
   - Distinguish between certain and speculative conclusions
   - Verify the consistency of the truths

4. Cross-Verification
   - Use multiple data points to verify each truth
   - Check the logical relationships between truths
   - Eliminate contradictory conclusions

5. Quality Check
   - Verify the reliability of each truth
   - Ensure accuracy and objectivity in expression
   - Check for over-interpretation

# Extraction Requirements
1. Truth Standards
   - Must be clearly supported by data
   - Avoid subjective judgments and speculation
   - Use precise and neutral language

2. Completeness Requirements
   - Include key information on time, place, and objects
   - Clearly indicate the source of information
   - Indicate the level of confidence

3. Format Specifications
   - Each truth should be in a separate paragraph
   - Include supporting evidence
   - Indicate the confidence level

# Output Format
<truths_start>
truth: [Truth 1]
evidence: [Specific data supporting the truth]
confidence: [High/Medium/Low]
source: [Data location/number]

truth: [Truth 2]
evidence: [Specific data supporting the truth]
confidence: [High/Medium/Low]
source: [Data location/number]

...
<truths_end>

# Notes
1. Only output truths with sufficient evidence
2. Clearly mark uncertain inferences
3. List similar truths with slight differences separately
"""







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



WAITING_FOR_DATA = 0

# Add new command handler for truth generation
async def generate_truths_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /truths command to start truth generation process"""
    print("Generating truths...")
    await update.message.reply_text(
        "Please provide the data you want to analyze for truth extraction. "
        "Send your data as text message."
    )
    return WAITING_FOR_DATA

# Add global truths storage
truths_storage = []


# Modify process_data_for_truths
async def process_data_for_truths(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process received data and generate truths"""
    user_data = update.message.text
    user_id = str(update.effective_user.id)
    
    # Prepare prompt with user data
    formatted_prompt = PROMPT_GENERATE_TRUTHS.format(input_data=user_data)
    
    try:
        ai_response = await ai.ai_chat(formatted_prompt, model='gpt-4o-mini')
        truths_text = extract_truths_section(ai_response)
        
        # Store truths 
        individual_truths = [truth.strip() for truth in truths_text.split('\n\n') if truth.strip()]
        truths_storage.extend(individual_truths)
        
        await update.message.reply_text("Your data has been processed and truths have been stored successfully!")
            
    except Exception as e:
        await update.message.reply_text(f"Error processing data: {str(e)}")
    
    return ConversationHandler.END

def extract_truths_section(response: str) -> str:
    """Extract the truths section from AI response"""
    start_marker = "<truths_start>"
    end_marker = "<truths_end>"
    
    try:
        start_idx = response.index(start_marker) + len(start_marker)
        end_idx = response.index(end_marker)
        return response[start_idx:end_idx].strip()
    except ValueError:
        return "No valid truths section found in response"

# Add function to handle viewing truths
async def view_truths(update: Update) -> None:
    """Handle viewing a random truth"""
    if not truths_storage:
        await update.message.reply_text("No truths available for viewing.")
        return
    
    # Get random truth and remove it
    truth = random.choice(truths_storage)
    truths_storage.remove(truth)
    
    # Send truth to user
    await update.message.reply_text(truth)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all messages and integrate with AI chat"""
    try:
        # Check if we're waiting for data
        if context.user_data.get('state') == WAITING_FOR_DATA:
            await process_data_for_truths(update, context)
            context.user_data['state'] = None  # Reset state
            return

        # Get AI response using DM guide
        ai_response = await ai.ai_chat(PROMPT_DM_GUIDE + "\n\nUser: " + update.message.text)
        print("AI response:", ai_response)  # Debug output
        
        # Simple command checking
        if '@system.command{{"Upload_data"}}' in ai_response:
            context.user_data['state'] = WAITING_FOR_DATA
            await update.message.reply_text(
                "Please provide the data you want to analyze for truth extraction. "
                "Send your data as text message."
            )
        elif '@system.command{{"View_truths"}}' in ai_response:
            await view_truths(update)
        else:
            # If no command, just send AI response
            await update.message.reply_text(ai_response)
            
    except Exception as e:
        await update.message.reply_text(f"Error processing message: {str(e)}")


def main() -> None:
    """Start the bot."""
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    application = Application.builder().token(BOT_TOKEN).build()

    # Basic command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add general message handler for AI chat
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()


