import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN environment variable is required')

# ConversationHandler states
TITLE, DESCRIPTION, CONFIRM = range(3)
REPLY_CASE_ID, REPLY_CONTENT = range(10, 12)
VIEW_CASE_ID = 20


# ─── Backend helpers ───

def backend_request(path, method='post', token=None, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['Content-Type'] = 'application/json'
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = BACKEND_URL.rstrip('/') + path
    return requests.request(method, url, headers=headers, **kwargs)


def login_or_register(telegram_id: str, username: str):
    return backend_request(
        '/api/telegram-login/',
        json={'telegram_id': str(telegram_id), 'username': username},
    )


def get_access_token(update: Update):
    if update.effective_user is None:
        return None
    username = (
        update.effective_user.username
        or update.effective_user.first_name
        or f'user_{update.effective_user.id}'
    )
    response = login_or_register(update.effective_user.id, username)
    if not response.ok:
        return None
    return response.json().get('access')


# ─── /start ───

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        return

    response = login_or_register(
        update.effective_user.id,
        update.effective_user.username
        or update.effective_user.first_name
        or f'user_{update.effective_user.id}',
    )

    if not response.ok:
        await update.message.reply_text(
            '⚠️ Unable to reach the backend. Please try again later.'
        )
        return

    await update.message.reply_text(
        '👋 *Welcome to the Counselling Support Bot!*\n\n'
        'Your account is ready. Here\'s what you can do:\n\n'
        '📝 /newcase — Submit a new support case\n'
        '📋 /mycases — View your cases\n'
        '💬 /reply — Reply to a case\n'
        '👁️ /viewcase — View messages on a case\n'
        '❓ /help — Show all commands',
        parse_mode='Markdown',
    )


# ─── /newcase — Multi-step ConversationHandler ───

async def newcase_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    await update.message.reply_text(
        '📝 *New Support Case*\n\n'
        'Let\'s create your case step by step.\n'
        'Send /cancel at any time to abort.\n\n'
        '*Step 1/2:* Please enter a short title for your case:',
        parse_mode='Markdown',
    )
    return TITLE


async def newcase_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    if len(title) < 5:
        await update.message.reply_text(
            '⚠️ Title is too short. Please enter at least 3 characters:'
        )
        return TITLE

    if len(title) > 200:
        await update.message.reply_text(
            '⚠️ Title is too long (max 200 characters). Please shorten it:'
        )
        return TITLE

    context.user_data['case_title'] = title
    await update.message.reply_text(
        f'✅ Title: *{title}*\n\n'
        '*Step 2/2:* Now please describe your issue in detail:',
        parse_mode='Markdown',
    )
    return DESCRIPTION


async def newcase_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text.strip()
    if len(description) < 10:
        await update.message.reply_text(
            '⚠️ Description is too short. Please provide more detail (at least 10 characters):'
        )
        return DESCRIPTION

    context.user_data['case_description'] = description
    title = context.user_data['case_title']

    keyboard = [['✅ Submit', '❌ Cancel']]
    await update.message.reply_text(
        f'📋 *Review your case:*\n\n'
        f'*Title:* {title}\n'
        f'*Description:* {description}\n\n'
        f'Please confirm:',
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM


async def newcase_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice != '✅ Submit':
        await update.message.reply_text(
            '❌ Case creation cancelled.',
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data.pop('case_title', None)
        context.user_data.pop('case_description', None)
        return ConversationHandler.END

    title = context.user_data.pop('case_title', '')
    description = context.user_data.pop('case_description', '')
    token = get_access_token(update)

    if token is None:
        await update.message.reply_text(
            '⚠️ Unable to authenticate. Please try /start first.',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    response = backend_request(
        '/api/cases/',
        token=token,
        json={'title': title, 'description': description},
    )

    if response.ok:
        data = response.json()
        await update.message.reply_text(
            f'✅ *Case created successfully!*\n\n'
            f'🆔 Case ID: *{data.get("id")}*\n'
            f'📝 Title: {data.get("title")}\n'
            f'📊 Status: {data.get("status")}\n\n'
            f'You\'ll be notified when support responds.',
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            f'⚠️ Failed to create case: {response.text}',
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END


async def newcase_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('case_title', None)
    context.user_data.pop('case_description', None)
    await update.message.reply_text(
        '❌ Case creation cancelled.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── /mycases ───

async def list_cases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('⚠️ Unable to authenticate. Please try /start first.')
        return

    response = backend_request('/api/cases/', method='get', token=token)
    if not response.ok:
        await update.message.reply_text('⚠️ Unable to fetch your cases.')
        return

    cases = response.json()
    if not cases:
        await update.message.reply_text(
            '📋 You have no cases yet.\n\nUse /newcase to create one!'
        )
        return

    status_icons = {'open': '🔵', 'assigned': '🟡', 'closed': '🟢'}
    lines = ['📋 *Your Cases:*\n']
    for case in cases:
        icon = status_icons.get(case['status'], '⚪')
        lines.append(f'{icon} *#{case["id"]}* — {case["title"]} (`{case["status"]}`)')

    lines.append(f'\n_Total: {len(cases)} case(s)_')
    lines.append('\nUse /viewcase to view messages on a case.')
    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')


# ─── /reply — Multi-step ───

async def reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    await update.message.reply_text(
        '💬 *Reply to a Case*\n\n'
        'Send /cancel to abort.\n\n'
        '*Step 1/2:* Enter the case ID:',
        parse_mode='Markdown',
    )
    return REPLY_CASE_ID


async def reply_case_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text('⚠️ Please enter a valid numeric case ID:')
        return REPLY_CASE_ID

    context.user_data['reply_case_id'] = text
    await update.message.reply_text(
        f'📝 Replying to case *#{text}*.\n\n'
        f'*Step 2/2:* Type your message:',
        parse_mode='Markdown',
    )
    return REPLY_CONTENT


async def reply_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = update.message.text.strip()
    case_id = context.user_data.pop('reply_case_id', None)

    if not content:
        await update.message.reply_text('⚠️ Message cannot be empty. Please type your message:')
        return REPLY_CONTENT

    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('⚠️ Unable to authenticate. Please try /start first.')
        return ConversationHandler.END

    response = backend_request(
        '/api/messages/',
        token=token,
        json={'case': case_id, 'content': content},
    )

    if response.ok:
        await update.message.reply_text(
            f'✅ Message sent to case *#{case_id}*.',
            parse_mode='Markdown',
        )
    else:
        await update.message.reply_text(f'⚠️ Failed to send message: {response.text}')
    return ConversationHandler.END


async def reply_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('reply_case_id', None)
    await update.message.reply_text('❌ Reply cancelled.')
    return ConversationHandler.END


# ─── /viewcase ───

async def viewcase_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    # Check if case ID provided inline: /viewcase 5
    if context.args:
        case_id = context.args[0].strip()
        if case_id.isdigit():
            await show_case_messages(update, context, case_id)
            return ConversationHandler.END

    await update.message.reply_text(
        '👁️ *View Case Messages*\n\n'
        'Send /cancel to abort.\n\n'
        'Enter the case ID:',
        parse_mode='Markdown',
    )
    return VIEW_CASE_ID


async def viewcase_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text('⚠️ Please enter a valid numeric case ID:')
        return VIEW_CASE_ID

    await show_case_messages(update, context, text)
    return ConversationHandler.END


async def show_case_messages(update, context, case_id):
    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('⚠️ Unable to authenticate. Please try /start first.')
        return

    # Fetch case info
    case_resp = backend_request(f'/api/cases/{case_id}/', method='get', token=token)
    if not case_resp.ok:
        await update.message.reply_text(f'⚠️ Case #{case_id} not found or access denied.')
        return

    case = case_resp.json()

    # Fetch messages
    msg_resp = backend_request(f'/api/messages/?case={case_id}', method='get', token=token)
    messages = msg_resp.json() if msg_resp.ok else []

    status_icons = {'open': '🔵', 'assigned': '🟡', 'closed': '🟢'}
    icon = status_icons.get(case['status'], '⚪')

    lines = [
        f'📋 *Case #{case["id"]}:* {case["title"]}',
        f'{icon} Status: `{case["status"]}`',
        '',
    ]

    if not messages:
        lines.append('_No messages yet._')
    else:
        lines.append(f'💬 *Messages ({len(messages)}):*\n')
        for msg in messages[-10:]:  # Show last 10 messages
            sender = msg.get('sender', {})
            label = sender.get('label', sender.get('username', 'Unknown'))
            role = msg.get('sender_role', '')
            role_tag = f' [{role}]' if role else ''
            lines.append(f'*{label}*{role_tag}:')
            lines.append(f'{msg["content"]}')
            lines.append(f'_{msg.get("timestamp", "")}_\n')

        if len(messages) > 10:
            lines.append(f'_... and {len(messages) - 10} earlier message(s)_')

    lines.append('\nUse /reply to respond to this case.')
    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')


async def viewcase_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Cancelled.')
    return ConversationHandler.END


# ─── /help ───

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    await update.message.reply_text(
        '🆘 *Available Commands:*\n\n'
        '/start — Register & get started\n'
        '/newcase — Submit a new support case (step-by-step)\n'
        '/mycases — List all your cases\n'
        '/viewcase — View messages on a case\n'
        '/reply — Reply to a case\n'
        '/help — Show this help message\n'
        '/cancel — Cancel current operation',
        parse_mode='Markdown',
    )


# ─── /cancel (global fallback) ───

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Seamlessly route plain text messages to the user's active case."""
    if update.effective_user is None or update.message is None or not update.message.text:
        print("DEBUG: Early return (user/message/text is None)")
        return

    if update.message.text.startswith('/'):
        print("DEBUG: Early return (command)")
        return

    print(f"DEBUG: handle_message triggered for user {update.effective_user.id}")

    token = get_access_token(update)
    if token is None:
        print("DEBUG: Failed to get access token")
        return

    # Find active cases (open or assigned)
    response = backend_request('/api/cases/', method='get', token=token)
    if not response.ok:
        print(f"DEBUG: Failed to fetch cases: {response.text}")
        return

    cases = [c for c in response.json() if c['status'] in ['open', 'assigned']]
    print(f"DEBUG: Found {len(cases)} active cases")
    
    if len(cases) == 1:
        case_id = cases[0]['id']
        print(f"DEBUG: Routing message to case #{case_id}")
        msg_resp = backend_request(
            '/api/messages/',
            token=token,
            json={'case': case_id, 'content': update.message.text},
        )
        if msg_resp.ok:
            await update.message.reply_text(f'✅ Sent to case *#{case_id}*.', parse_mode='Markdown')
        else:
            print(f"DEBUG: Failed to send message to backend: {msg_resp.text}")
            await update.message.reply_text(f'⚠️ Failed to send: {msg_resp.text}')
    elif len(cases) > 1:
        await update.message.reply_text(
            '📝 You have multiple active cases. Please use `/reply <case_id>` to specify which one you are talking about.',
            parse_mode='Markdown'
        )
    else:
        print("DEBUG: No active cases found")
        await update.message.reply_text(
            '👋 Welcome! You don\'t have any active cases right now.\n\n'
            'Use /newcase to start a support request.',
            parse_mode='Markdown'
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── Main ───

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Multi-step conversation for /newcase
    newcase_handler = ConversationHandler(
        entry_points=[CommandHandler('newcase', newcase_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_description)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_confirm)],
        },
        fallbacks=[CommandHandler('cancel', newcase_cancel)],
    )

    # Multi-step conversation for /reply
    reply_handler = ConversationHandler(
        entry_points=[CommandHandler('reply', reply_start)],
        states={
            REPLY_CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, reply_case_id)],
            REPLY_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reply_content)],
        },
        fallbacks=[CommandHandler('cancel', reply_cancel)],
    )

    # Multi-step (or inline) conversation for /viewcase
    viewcase_handler = ConversationHandler(
        entry_points=[CommandHandler('viewcase', viewcase_start)],
        states={
            VIEW_CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, viewcase_id)],
        },
        fallbacks=[CommandHandler('cancel', viewcase_cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(newcase_handler)
    application.add_handler(CommandHandler('mycases', list_cases))
    application.add_handler(reply_handler)
    application.add_handler(viewcase_handler)
    application.add_handler(CommandHandler('help', help_command))

    # General text handler for seamless chat
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Legacy single-line /message command (backward compat)
    application.add_handler(CommandHandler('message', legacy_message))

    application.run_polling()


async def legacy_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Backward-compatible single-line /message <case_id> | <content>"""
    if update.effective_user is None or update.message is None:
        return

    payload = ' '.join(context.args)
    if '|' not in payload:
        await update.message.reply_text(
            'Usage: /message <case_id> | <message>\n'
            'Or use /reply for the step-by-step flow.'
        )
        return

    case_id, content = [part.strip() for part in payload.split('|', 1)]
    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('⚠️ Unable to authenticate.')
        return

    response = backend_request(
        '/api/messages/',
        token=token,
        json={'case': case_id, 'content': content},
    )
    if response.ok:
        await update.message.reply_text(f'✅ Message sent to case #{case_id}.')
    else:
        await update.message.reply_text(f'⚠️ Failed: {response.text}')


if __name__ == '__main__':
    main()
