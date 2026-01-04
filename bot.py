import logging
import os
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from content import MENUS, START_TEXT, THEORY_TEXT, CODE_EXPLANATION, CHOOSE_MODE_TEXT, SOLVE_PROMPT_SIMPLE, SOLVE_PROMPT_PARAMETRIC, EXAMPLES_TEXT, EXAMPLES_SIMPLE, EXAMPLES_PARAMETRIC, ERROR_FILE_FORMAT, ERROR_SORTED, ERROR_MIN_POINTS
from spline_logic import CubicSplineSolver, ParametricSplineSolver
import io

# Load environment variables
load_dotenv()

# Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in .env file")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# User states to track mode (Simple vs Parametric)
MODE_KEY = "spline_mode"
MODE_SIMPLE = "simple"
MODE_PARAMETRIC = "parametric"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Default to simple mode
    context.user_data[MODE_KEY] = MODE_SIMPLE
    
    keyboard = [
        [KeyboardButton(MENUS["theory"]), KeyboardButton(MENUS["code"])],
        [KeyboardButton(MENUS["solve"]), KeyboardButton(MENUS["examples"])],
        [KeyboardButton(MENUS["about"])]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(START_TEXT, reply_markup=reply_markup)

async def show_solve_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(MENUS["mode_simple"]), KeyboardButton(MENUS["mode_parametric"])],
        [KeyboardButton(MENUS["back"])]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(CHOOSE_MODE_TEXT, reply_markup=reply_markup)

async def show_examples_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(MENUS["mode_simple"]), KeyboardButton(MENUS["mode_parametric"])],
        [KeyboardButton(MENUS["back"])]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(EXAMPLES_TEXT, reply_markup=reply_markup)

async def solve_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, content: str):
    """Parses content as points and solves the spline problem based on mode."""
    points_x = []
    points_y = []
    
    mode = context.user_data.get(MODE_KEY, MODE_SIMPLE)
    
    try:
        lines = content.strip().split('\n')
        lines = [l for l in lines if l.strip()]
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 1 and ',' in parts[0]:
                 parts = parts[0].split(',')
                 
            if len(parts) >= 2:
                points_x.append(float(parts[0]))
                points_y.append(float(parts[1]))
                
        if len(points_x) < 3:
            if len(points_x) > 0:
                await update.message.reply_text(ERROR_MIN_POINTS)
                return False
            return False 
            
        # Validation based on mode
        if mode == MODE_SIMPLE:
            # Check sorted for simple function
            if any(points_x[i] >= points_x[i+1] for i in range(len(points_x)-1)):
                 await update.message.reply_text(ERROR_SORTED)
                 return True
            solver = CubicSplineSolver(points_x, points_y)
            caption = "نمودار درونیابی اسپلاین (ساده)"
        else:
            # Parametric mode: no sorting check needed
            solver = ParametricSplineSolver(points_x, points_y)
            caption = "نمودار درونیابی اسپلاین (پارامتری)"

        result_text = solver.solve()
        steps_text = solver.get_steps()
        
        # Send steps
        if len(steps_text) > 3000:
             steps_text = steps_text[:3000] + "\n...(truncated)..."
        await update.message.reply_text(f"🔢 **مراحل حل ({mode}):**\n\n{steps_text}")
        
        # Send final equations
        if len(result_text) > 3000:
             result_text = result_text[:3000] + "\n...(truncated)..."
        await update.message.reply_text(f"✅ **معادلات نهایی:**\n\n{result_text}")
        
        # Send plot
        plot_buf = solver.plot_spline()
        await update.message.reply_photo(photo=plot_buf, caption=caption)
        return True
        
    except ValueError:
        return False
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در محاسبات: {str(e)}")
        return True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == MENUS["back"]:
        context.user_data['viewing_examples'] = False
        await start(update, context)
        return

    # Use HTML for both theory and code to avoid Markdown issues
    if text == MENUS["theory"]:
        await update.message.reply_text(THEORY_TEXT, parse_mode="HTML")
        return
    elif text == MENUS["code"]:
        await update.message.reply_text(CODE_EXPLANATION, parse_mode="HTML")
        return
    elif text == MENUS["about"]:
        await update.message.reply_text("🤖 ربات آموزشی Cubic Spline\nطراحی شده برای درس محاسبات عددی.")
        return

    # Entry points
    elif text == MENUS["solve"]:
        context.user_data['viewing_examples'] = False
        await show_solve_menu(update, context)
        return
    elif text == MENUS["examples"]:
        context.user_data['viewing_examples'] = True
        await show_examples_menu(update, context)
        return

    # Sub-menu selections
    elif text == MENUS["mode_simple"]:
        context.user_data[MODE_KEY] = MODE_SIMPLE
        if context.user_data.get('viewing_examples'):
            await update.message.reply_text(EXAMPLES_SIMPLE, parse_mode="Markdown")
            context.user_data['viewing_examples'] = False # Reset after showing
        else:
            await update.message.reply_text(SOLVE_PROMPT_SIMPLE, parse_mode="Markdown")
        return

    elif text == MENUS["mode_parametric"]:
        context.user_data[MODE_KEY] = MODE_PARAMETRIC
        if context.user_data.get('viewing_examples'):
            await update.message.reply_text(EXAMPLES_PARAMETRIC, parse_mode="Markdown")
            context.user_data['viewing_examples'] = False
        else:
            await update.message.reply_text(SOLVE_PROMPT_PARAMETRIC, parse_mode="Markdown")
        return

    # Fallback: check for data
    is_data = await solve_and_reply(update, context, text)
    if not is_data:
         await update.message.reply_text("لطفا از منو انتخاب کنید یا نقاط را ارسال کنید.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ لطفا فقط فایل .txt ارسال کنید.")
        return

    file = await document.get_file()
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode('utf-8')
    
    success = await solve_and_reply(update, context, content)
    if not success:
         await update.message.reply_text(ERROR_FILE_FORMAT)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    application.run_polling()

if __name__ == "__main__":
    main()
