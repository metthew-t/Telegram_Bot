import os
import requests
import base64
from dotenv import load_dotenv

# Load .env file
load_dotenv()
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

# On Render, gunicorn listens on $PORT, not 8000
_port = os.environ.get('PORT', '8000')
BACKEND_URL = os.environ.get('BACKEND_URL', f'http://127.0.0.1:{_port}')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN environment variable is required')

# Persistent main menu keyboard layout
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ['📝 New Case', '👁️ View Case'],
        ['💬 Reply', '🔄 Reopen Case'],
        ['❌ Close Case', '❓ Help']
    ],
    resize_keyboard=True,
    is_persistent=True  # Keep menu always visible
)

# ConversationHandler states
TITLE, DESCRIPTION, CONFIRM = range(3)
REPLY_CASE_ID, REPLY_CONTENT = range(10, 12)
VIEW_CASE_ID = 20
CLOSE_CASE_ID = 21


# ─── Backend helpers ───

def backend_request(path, method='post', token=None, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['Content-Type'] = 'application/json'
    headers['X-Forwarded-Proto'] = 'https'
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = BACKEND_URL.rstrip('/') + path
    try:
        response = requests.request(method, url, headers=headers, timeout=10, **kwargs)
        print(f"DEBUG: Backend request to {url} returned status {response.status_code}")
        if not response.ok:
            print(f"DEBUG: Error response body: {response.text}")
        return response
    except Exception as e:
        print(f"DEBUG: Exception during backend request to {url}: {str(e)}")
        class DummyResponse:
            ok = False
            status_code = 500
            text = str(e)
            def json(self):
                return {}
        return DummyResponse()



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
        '👁️ /viewcase — View your case history\n'
        '💬 /reply — Reply to your active case\n'
        '🔄 /reopen — Reopen a closed case\n'
        '❓ /help — Show all commands',
        parse_mode='Markdown',
        reply_markup=MAIN_MENU_KEYBOARD,
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
        reply_markup=ReplyKeyboardRemove(),
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
            reply_markup=MAIN_MENU_KEYBOARD,
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
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return ConversationHandler.END

    # Check for existing active cases (open or assigned)
    check_response = backend_request(
        '/api/cases/',
        method='get',
        token=token,
    )
    
    if check_response.ok:
        cases = check_response.json()
        active_cases = [c for c in cases if c.get('status') in ['open', 'assigned']]
        if active_cases:
            active_case = active_cases[0]
            case_num = active_case.get('user_case_number', active_case.get('id'))
            await update.message.reply_text(
                f'⚠️ *You already have an active case!*\n\n'
                f'📝 Case #{case_num}: {active_case.get("title")}\n'
                f'📊 Status: {active_case.get("status")}\n\n'
                f'Please close your current case before creating a new one.\n'
                f'At one time, you can only have one active case.',
                parse_mode='Markdown',
                reply_markup=MAIN_MENU_KEYBOARD,
            )
            return ConversationHandler.END

    response = backend_request(
        '/api/cases/',
        token=token,
        json={'title': title, 'description': description},
    )

    if response.ok:
        data = response.json()
        case_num = data.get('user_case_number', data.get('id'))
        await update.message.reply_text(
            f'✅ *Case created successfully!*\n\n'
            f'📝 Your Case *#{case_num}*\n'
            f'📌 Title: {data.get("title")}\n'
            f'📊 Status: {data.get("status")}\n\n'
            f'You\'ll be notified when support responds.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
    else:
        await update.message.reply_text(
            f'⚠️ Failed to create case: {response.text}',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
    return ConversationHandler.END


async def newcase_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('case_title', None)
    context.user_data.pop('case_description', None)
    await update.message.reply_text(
        '❌ Case creation cancelled.',
        reply_markup=MAIN_MENU_KEYBOARD,
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
    
    # Show all cases including closed
    for case in cases:
        icon = status_icons.get(case['status'], '⚪')
        case_num = case.get('user_case_number', case['id'])
        lines.append(f'{icon} *Your Case #{case_num}* — {case["title"]} (`{case["status"]}`)')

    lines.append(f'\n_Total: {len(cases)} case(s)_')
    lines.append('\nUse /viewcase to view messages on a case.')
    lines.append('Use /reopen to reopen a closed case.')
    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown', reply_markup=MAIN_MENU_KEYBOARD)


# ─── /reply — Multi-step ───

async def reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    await update.message.reply_text(
        '💬 *Reply to a Case*\n\n'
        'Send /cancel to abort.\n\n'
        '*Step 1/2:* Enter the case ID:',
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(),
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
        # Message sent - no confirmation needed, just return to menu
        await update.message.reply_text(
            '✅ Message sent.',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
    else:
        await update.message.reply_text(f'⚠️ Failed to send message: {response.text}', reply_markup=MAIN_MENU_KEYBOARD)
    return ConversationHandler.END


async def reply_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('reply_case_id', None)
    await update.message.reply_text('❌ Reply cancelled.', reply_markup=MAIN_MENU_KEYBOARD)
    return ConversationHandler.END


# ─── /viewcase ───

async def viewcase_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    token = get_access_token(update)
    
    # Check if case number provided inline: /viewcase 5
    if context.args:
        user_case_num = context.args[0].strip()
        if user_case_num.isdigit():
            # Fetch cases and find matching user_case_number
            cases_resp = backend_request('/api/cases/', method='get', token=token)
            if cases_resp.ok:
                all_cases = cases_resp.json()
                matching_case = next(
                    (c for c in all_cases if c.get('user_case_number') == int(user_case_num)),
                    None
                )
                if matching_case:
                    await show_case_messages(update, context, matching_case['id'])
                    return ConversationHandler.END

    # Show user's case history
    cases_resp = backend_request('/api/cases/', method='get', token=token)
    
    if not cases_resp.ok:
        await update.message.reply_text(
            '⚠️ Failed to fetch your cases.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    all_cases = cases_resp.json()
    
    if not all_cases:
        await update.message.reply_text(
            '📋 You have no cases yet.\n\nUse /newcase to create your first case.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    # Show case history
    lines = ['📋 *Your Case History:*\n']
    for case in all_cases:
        case_num = case.get('user_case_number', case['id'])
        status_icon = {'open': '🔵', 'assigned': '🟡', 'resolved': '🟢', 'closed': '⚪'}.get(case['status'], '⚪')
        lines.append(f'{status_icon} *Case #{case_num}*: {case["title"]} (`{case["status"]}`)')
    
    lines.append(f'\n_Total: {len(all_cases)} case(s)_')
    lines.append('\nEnter a case number to view its messages:')
    
    await update.message.reply_text(
        '\n'.join(lines),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(),
    )
    return VIEW_CASE_ID


async def viewcase_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text('⚠️ Please enter a valid numeric case number:')
        return VIEW_CASE_ID

    user_case_num = int(text)
    token = get_access_token(update)
    
    # Fetch all user's cases to find the one with matching user_case_number
    cases_resp = backend_request('/api/cases/', method='get', token=token)
    if not cases_resp.ok:
        await update.message.reply_text('⚠️ Failed to fetch your cases.')
        return ConversationHandler.END
    
    all_cases = cases_resp.json()
    matching_case = next(
        (c for c in all_cases if c.get('user_case_number') == user_case_num),
        None
    )
    
    if not matching_case:
        await update.message.reply_text(f'⚠️ Case #{user_case_num} not found in your cases.')
        return ConversationHandler.END
    
    # Use database ID for backend call
    await show_case_messages(update, context, matching_case['id'])
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
    
    # Mark case as viewed (for "seen" status tracking)
    backend_request(f'/api/cases/{case_id}/mark_viewed/', method='post', token=token)

    status_icons = {'open': '🔵', 'assigned': '🟡', 'closed': '🟢'}
    icon = status_icons.get(case['status'], '⚪')
    case_num = case.get('user_case_number', case['id'])

    lines = [
        f'📋 *Your Case #{case_num}:* {case["title"]}',
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
            
            # Determine read receipt status
            read_status = ''
            if role == 'user':  # Only show read receipts for user's own messages
                if msg.get('seen_by_admin_at'):
                    read_status = ' ✓✓'  # Seen by admin
                else:
                    read_status = ' ✓'   # Sent but not seen yet
            
            role_tag = f' [{role}]' if role else ''
            lines.append(f'*{label}*{role_tag}:')
            
            # Check if voice message
            if msg.get('message_type') == 'voice' and msg.get('voice_data'):
                duration = msg.get('voice_duration', 0)
                lines.append(f'🎤 Voice message ({duration}s){read_status}')
                lines.append('_[Voice messages can be played on the website]_')
            else:
                lines.append(f'{msg["content"]}{read_status}')
            
            lines.append(f'_{msg.get("timestamp", "")}_\n')

        if len(messages) > 10:
            lines.append(f'_... and {len(messages) - 10} earlier message(s)_')

    # Add appropriate action hint based on case status
    if case['status'] == 'closed':
        lines.append('\n🔒 *This case is closed.* You cannot reply to a closed case.')
        lines.append('Use /reopen to reopen this case if you need further assistance.')
    else:
        lines.append('\nUse /reply to respond to this case.')
    
    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown', reply_markup=MAIN_MENU_KEYBOARD)


async def viewcase_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Cancelled.', reply_markup=MAIN_MENU_KEYBOARD)
    return ConversationHandler.END


# ─── /help ───

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    await update.message.reply_text(
        '🆘 *Available Commands:*\n\n'
        '📝 *New Case* — Submit a new support case (step-by-step)\n'
        '   • Use this to create a new counseling request\n'
        '   • You\'ll be guided through title, description, and confirmation\n\n'
        '👁️ *View Case* — View your case history\n'
        '   • Shows all your cases (active and closed)\n'
        '   • Enter a case number to see conversation history\n\n'
        '💬 *Reply* — Send a message to your case\n'
        '   • Quick way to send messages\n\n'
        '🔓 *Reopen* — Reopen a closed case\n'
        '   • Continue work on a previously closed case\n'
        '   • Enter the case number when prompted\n\n'
        '❌ *Close Case* — Close your active case\n'
        '   • Mark your case as resolved\n'
        '   • You can reopen it later if needed\n\n'
        '❓ *Help* — Show this detailed help message\n\n'
        '---\n\n'
        '💡 *Quick Tips:*\n'
        '• You can only have ONE active case at a time\n'
        '• Just type your messages normally - they\'ll be sent automatically!\n'
        '• Use /cancel anytime to abort an operation\n'
        '• You can send voice messages too!\n'
        '• Your counselor will be notified when you send a message\n'
        '• Closed cases can be reopened anytime using 🔄 Reopen',
        parse_mode='Markdown',
        reply_markup=MAIN_MENU_KEYBOARD,
    )


# ─── /reopen ───

REOPEN_CASE_ID = 30

async def reopen_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the reopen case flow"""
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    await update.message.reply_text(
        '🔓 *Reopen a Closed Case*\n\n'
        'Send /cancel to abort.\n\n'
        'Enter the case ID you want to reopen:',
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(),
    )
    return REOPEN_CASE_ID


async def reopen_case_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the case ID and attempt to reopen"""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text('⚠️ Please enter a valid numeric case number:')
        return REOPEN_CASE_ID

    user_case_num = int(text)
    token = get_access_token(update)
    if token is None:
        await update.message.reply_text(
            '⚠️ Unable to authenticate. Please try /start first.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END

    # Fetch all user's cases to find the one with matching user_case_number
    cases_resp = backend_request('/api/cases/', method='get', token=token)
    if not cases_resp.ok:
        await update.message.reply_text(
            '⚠️ Failed to fetch your cases.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    all_cases = cases_resp.json()
    matching_case = next(
        (c for c in all_cases if c.get('user_case_number') == user_case_num),
        None
    )
    
    if not matching_case:
        await update.message.reply_text(
            f'⚠️ Case #{user_case_num} not found in your cases.\n\n'
            f'Use /viewcase to see your case history.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    case_id = matching_case['id']
    
    # Call the reopen API endpoint using database ID
    response = backend_request(f'/api/cases/{case_id}/reopen/', method='post', token=token)
    
    if response.ok:
        data = response.json()
        await update.message.reply_text(
            f'✅ *Case #{user_case_num} Reopened Successfully!*\n\n'
            f'📊 Status: {data.get("status", "assigned")}\n'
            f'👤 Assigned to: {data.get("assigned_admin", "Previous admin")}\n\n'
            f'You can now continue the conversation on this case.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        error_msg = response.json().get('error', response.text) if response.text else 'Unknown error'
        await update.message.reply_text(
            f'⚠️ Failed to reopen case:\n\n{error_msg}',
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


async def reopen_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Reopen cancelled.', reply_markup=MAIN_MENU_KEYBOARD)
    return ConversationHandler.END


# ─── /closecase ───

async def closecase_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the close case flow"""
    if update.effective_user is None or update.message is None:
        return ConversationHandler.END

    token = get_access_token(update)
    if token is None:
        await update.message.reply_text(
            '⚠️ Unable to authenticate. Please try /start first.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END

    # Fetch active cases (open or assigned)
    cases_resp = backend_request('/api/cases/', method='get', token=token)
    if not cases_resp.ok:
        await update.message.reply_text(
            '⚠️ Failed to fetch your cases.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    all_cases = cases_resp.json()
    active_cases = [c for c in all_cases if c.get('status') in ['open', 'assigned']]
    
    if not active_cases:
        await update.message.reply_text(
            '📋 You don\'t have any active cases to close.\n\n'
            'Only active cases (open or assigned) can be closed.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    # Show list of active cases
    lines = ['❌ *Close a Case*\n\nYour active cases:\n']
    for case in active_cases:
        case_num = case.get('user_case_number', case['id'])
        status_icon = '🔵' if case['status'] == 'open' else '🟡'
        lines.append(f'{status_icon} *Case #{case_num}*: {case["title"]} (`{case["status"]}`)')
    
    lines.append('\nEnter the case number you want to close:')
    lines.append('\nSend /cancel to abort.')
    
    await update.message.reply_text(
        '\n'.join(lines),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return CLOSE_CASE_ID


async def closecase_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the case number and close the case"""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text('⚠️ Please enter a valid numeric case number:')
        return CLOSE_CASE_ID

    user_case_num = int(text)
    token = get_access_token(update)
    if token is None:
        await update.message.reply_text(
            '⚠️ Unable to authenticate. Please try /start first.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END

    # Fetch all user's cases to find the one with matching user_case_number
    cases_resp = backend_request('/api/cases/', method='get', token=token)
    if not cases_resp.ok:
        await update.message.reply_text(
            '⚠️ Failed to fetch your cases.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    all_cases = cases_resp.json()
    matching_case = next(
        (c for c in all_cases if c.get('user_case_number') == user_case_num),
        None
    )
    
    if not matching_case:
        await update.message.reply_text(
            f'⚠️ Case #{user_case_num} not found in your cases.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    # Check if case is already closed
    if matching_case['status'] == 'closed':
        await update.message.reply_text(
            f'ℹ️ Case #{user_case_num} is already closed.',
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    case_id = matching_case['id']
    
    # Call the close API endpoint using database ID
    response = backend_request(f'/api/cases/{case_id}/close/', method='post', token=token)
    
    if response.ok:
        await update.message.reply_text(
            f'✅ *Case #{user_case_num} Closed Successfully!*\n\n'
            f'📝 {matching_case["title"]}\n\n'
            f'Thank you for using our counseling service!\n\n'
            f'💡 You can reopen this case anytime using 🔄 *Reopen Case*.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        error_msg = response.json().get('error', response.text) if response.text else 'Unknown error'
        await update.message.reply_text(
            f'⚠️ Failed to close case:\n\n{error_msg}',
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


async def closecase_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Close cancelled.', reply_markup=MAIN_MENU_KEYBOARD)
    return ConversationHandler.END


# ─── /cancel (global fallback) ───

async def check_for_feedback_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check if user's message is feedback for a recently closed case.
    This runs on every message and detects if we're waiting for feedback text.
    """
    if update.effective_user is None or update.message is None or not update.message.text:
        return False
    
    # Check if user has a pending feedback case stored in context
    feedback_case_id = context.user_data.get('feedback_case_id')
    feedback_step = context.user_data.get('feedback_step')
    
    if feedback_case_id and feedback_step == 'text':
        # User is providing text feedback (after selecting rating)
        feedback_text = update.message.text.strip()
        feedback_rating = context.user_data.get('feedback_rating')
        
        token = get_access_token(update)
        if not token:
            return False
        
        # Create feedback via API with both text and rating
        feedback_resp = backend_request(
            '/api/feedbacks/',
            method='post',
            token=token,
            json={
                'case': feedback_case_id,
                'content': feedback_text,
                'rating': feedback_rating  # Can be None if skipped
            }
        )
        
        if feedback_resp.ok:
            rating_text = f"⭐ {feedback_rating}/5" if feedback_rating else "No rating"
            await update.message.reply_text(
                f'✅ *Thank You for Your Detailed Feedback!*\n\n'
                f'🌟 Rating: {rating_text}\n'
                f'💬 Written feedback: Received\n\n'
                f'Your feedback has been successfully recorded and will help us improve our service.\n\n'
                f'We appreciate you taking the time to share your detailed experience!',
                parse_mode='Markdown',
                reply_markup=MAIN_MENU_KEYBOARD
            )
            # Clear the pending feedback flags
            context.user_data.pop('feedback_case_id', None)
            context.user_data.pop('feedback_rating', None)
            context.user_data.pop('feedback_step', None)
            return True
        else:
            print(f"DEBUG: Failed to submit feedback: {feedback_resp.text}")
            await update.message.reply_text(
                '⚠️ There was an issue saving your feedback. Please try again later.',
                reply_markup=MAIN_MENU_KEYBOARD
            )
            context.user_data.pop('feedback_case_id', None)
            context.user_data.pop('feedback_rating', None)
            context.user_data.pop('feedback_step', None)
            return True
    
    return False


async def handle_message_with_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced message handler that checks for feedback requests first"""
    # First check if this is feedback
    is_feedback = await check_for_feedback_request(update, context)
    if is_feedback:
        return
    
    # Otherwise, proceed with normal message handling
    await handle_message(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Seamlessly route plain text messages to the user's active case with smart case switching."""
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
    
    message_text = update.message.text.strip()
    
    # Single case - send directly
    if len(cases) == 1:
        case_id = cases[0]['id']
        case_num = cases[0].get('user_case_number', case_id)
        case_status = cases[0]['status']
        context.user_data['selected_case_id'] = case_id
        print(f"DEBUG: Routing message to case #{case_id}")
        
        # Check if case is closed
        if case_status == 'closed':
            await update.message.reply_text(
                f'🔒 Your case *#{case_num}* is closed.\n\n'
                f'You cannot send messages to a closed case.\n\n'
                f'💡 Use /reopen to reopen this case if you need further assistance.',
                parse_mode='Markdown'
            )
            return
        
        # Mark case as viewed (user is viewing/replying to their case)
        backend_request(f'/api/cases/{case_id}/mark_viewed/', method='post', token=token)
        
        msg_resp = backend_request(
            '/api/messages/',
            token=token,
            json={'case': case_id, 'content': message_text, 'message_type': 'text'},
        )
        if msg_resp.ok:
            # Message sent successfully - no confirmation needed, user just continues chatting
            # Read receipt: ✓ (sent) will be shown when user views their messages via /viewcase
            pass
        else:
            print(f"DEBUG: Failed to send message to backend: {msg_resp.text}")
            await update.message.reply_text(f'⚠️ Failed to send: {msg_resp.text}')
    
    # Multiple cases - smart routing with message saving
    elif len(cases) > 1:
        # Check if user has previously selected a case
        selected_case_id = context.user_data.get('selected_case_id')
        
        # NEW: Check for new response notification (admin replied to a different case)
        # If admin replied to a case that's NOT the currently selected one, ask to switch
        has_new_response_on_different_case = False
        response_case_id = None
        
        # This would require tracking which case got new admin responses
        # For now, skip this check and just use selected_case_id
        
        if selected_case_id:
            # Verify the case is still active
            matching_case = next((c for c in cases if c['id'] == selected_case_id), None)
            if matching_case:
                case_num = matching_case.get('user_case_number', selected_case_id)
                case_status = matching_case['status']
                print(f"DEBUG: Routing message to pre-selected case #{selected_case_id}")
                
                # Check if case is closed
                if case_status == 'closed':
                    await update.message.reply_text(
                        f'🔒 Your case *#{case_num}* is closed.\n\n'
                        f'You cannot send messages to a closed case.\n\n'
                        f'💡 Use /reopen to reopen this case if you need further assistance.',
                        parse_mode='Markdown'
                    )
                    return
                
                # Mark case as viewed (user is viewing/replying to their case)
                backend_request(f'/api/cases/{selected_case_id}/mark_viewed/', method='post', token=token)
                
                msg_resp = backend_request(
                    '/api/messages/',
                    token=token,
                    json={'case': selected_case_id, 'content': message_text, 'message_type': 'text'},
                )
                if msg_resp.ok:
                    # Message sent successfully - no confirmation
                    pass
                else:
                    print(f"DEBUG: Failed to send message to backend: {msg_resp.text}")
                    await update.message.reply_text(f'⚠️ Failed to send: {msg_resp.text}')
                return
            else:
                # Case no longer active, clear selection
                context.user_data.pop('selected_case_id', None)
        
    # Multiple cases - this shouldn't happen with new workflow!
    # Show error and tell user to close extra cases
    elif len(cases) > 1:
        case_list = '\n'.join([f"• Case #{c.get('user_case_number', c['id'])}: {c['title']} ({c['status']})" for c in cases[:10]])
        await update.message.reply_text(
            f'⚠️ *System Notice:* You have {len(cases)} active cases, but you should only have one.\n\n'
            f'Active cases:\n{case_list}\n\n'
            f'Please contact support or close the extra cases using the web interface.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return
        print("DEBUG: No active cases found")
        await update.message.reply_text(
            '👋 Welcome! You don\'t have any active cases right now.\n\n'
            'Use /newcase to start a support request.',
            parse_mode='Markdown'
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages from users and route to their active case."""
    if update.effective_user is None or update.message is None or not update.message.voice:
        print("DEBUG: Early return (user/message/voice is None)")
        return

    print(f"DEBUG: handle_voice triggered for user {update.effective_user.id}")

    token = get_access_token(update)
    if token is None:
        print("DEBUG: Failed to get access token")
        await update.message.reply_text('⚠️ Unable to authenticate. Please try /start first.')
        return

    # Check if user has an active case selected in context
    selected_case_id = context.user_data.get('selected_case_id')
    
    # Find active cases (open or assigned)
    response = backend_request('/api/cases/', method='get', token=token)
    if not response.ok:
        print(f"DEBUG: Failed to fetch cases: {response.text}")
        await update.message.reply_text('⚠️ Unable to fetch your cases.')
        return

    cases = [c for c in response.json() if c['status'] in ['open', 'assigned']]
    print(f"DEBUG: Found {len(cases)} active cases")
    
    # If only one case, use it
    if len(cases) == 1:
        case_id = cases[0]['id']
        case_num = cases[0].get('user_case_number', case_id)
        # Mark case as viewed (user is viewing/replying to their case)
        backend_request(f'/api/cases/{case_id}/mark_viewed/', method='post', token=token)
    # If user has selected a case previously, use it
    elif selected_case_id:
        # Verify the selected case is still active
        matching_case = next((c for c in cases if c['id'] == selected_case_id), None)
        if matching_case:
            case_id = matching_case['id']
            case_num = matching_case.get('user_case_number', case_id)
            # Mark case as viewed (user is viewing/replying to their case)
            backend_request(f'/api/cases/{case_id}/mark_viewed/', method='post', token=token)
        else:
            await update.message.reply_text(
                '📝 Your selected case is no longer active. Please send a text message with the case number to select a different case.',
                parse_mode='Markdown'
            )
            context.user_data.pop('selected_case_id', None)
            return
    # Multiple cases - this shouldn't happen with new workflow!
    elif len(cases) > 1:
        case_list = '\n'.join([f"• Case #{c.get('user_case_number', c['id'])}: {c['title']} ({c['status']})" for c in cases[:10]])
        await update.message.reply_text(
            f'⚠️ *System Notice:* You have {len(cases)} active cases, but you should only have one.\n\n'
            f'Active cases:\n{case_list}\n\n'
            f'Please contact support or close the extra cases using the web interface.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return
    # No cases
    else:
        await update.message.reply_text(
            '👋 You don\'t have any active cases right now.\n\nUse 📝 *New Case* to start a support request.',
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return

    voice = update.message.voice

    try:
        # Download voice file from Telegram
        print(f"DEBUG: Downloading voice file {voice.file_id}")
        file = await context.bot.get_file(voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        
        # Convert to base64
        voice_base64 = base64.b64encode(voice_bytes).decode('utf-8')
        
        print(f"DEBUG: Voice file downloaded, size: {len(voice_bytes)} bytes, duration: {voice.duration}s")
        
        # Send to backend
        msg_resp = backend_request(
            '/api/messages/',
            token=token,
            json={
                'case': case_id,
                'content': '[Voice Message]',
                'message_type': 'voice',
                'voice_data': voice_base64,
                'voice_duration': voice.duration
            },
        )
        
        if msg_resp.ok:
            # Voice message sent successfully - no confirmation needed
            pass
        else:
            print(f"DEBUG: Failed to send voice to backend: {msg_resp.text}")
            await update.message.reply_text(f'⚠️ Failed to send voice: {msg_resp.text}')
    
    except Exception as e:
        print(f"ERROR: Failed to process voice message: {str(e)}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f'⚠️ Error processing voice message: {str(e)}')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Operation cancelled.', reply_markup=MAIN_MENU_KEYBOARD)
    return ConversationHandler.END


# ─── Feedback Inline Button Handler ───

async def handle_feedback_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button click for feedback submission with rating system"""
    query = update.callback_query
    await query.answer()
    
    # Extract case ID from callback data (format: "feedback_123")
    callback_data = query.data
    
    # Handle initial feedback button click
    if callback_data.startswith('feedback_'):
        try:
            case_id = int(callback_data.split('_')[1])
        except (IndexError, ValueError):
            await query.edit_message_text("❌ Error processing feedback request.")
            return
        
        # Store case ID in user context
        context.user_data['feedback_case_id'] = case_id
        context.user_data['feedback_step'] = 'rating'  # First ask for rating
        
        # Show rating selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("⭐ 1", callback_data=f"rating_{case_id}_1"),
                InlineKeyboardButton("⭐⭐ 2", callback_data=f"rating_{case_id}_2"),
                InlineKeyboardButton("⭐⭐⭐ 3", callback_data=f"rating_{case_id}_3"),
            ],
            [
                InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data=f"rating_{case_id}_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐ 5", callback_data=f"rating_{case_id}_5"),
            ],
            [
                InlineKeyboardButton("⏭️ Skip Rating", callback_data=f"rating_{case_id}_skip")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=(
                "📝 *Feedback for Your Case*\n\n"
                "🌟 *Step 1 of 2: Rate Your Experience*\n\n"
                "How would you rate your counselor and overall experience?\n"
                "Choose from 1 star (poor) to 5 stars (excellent).\n\n"
                "_You can also skip the rating if you prefer._"
            ),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # Handle rating selection
    elif callback_data.startswith('rating_'):
        try:
            parts = callback_data.split('_')
            case_id = int(parts[1])
            rating_value = parts[2]
            
            if rating_value == 'skip':
                context.user_data['feedback_rating'] = None
                rating_text = "No rating"
            else:
                context.user_data['feedback_rating'] = int(rating_value)
                rating_text = "⭐" * int(rating_value)
        except (IndexError, ValueError):
            await query.edit_message_text("❌ Error processing rating.")
            return
        
        # Move to text feedback step
        context.user_data['feedback_step'] = 'text'
        
        # Show option to submit with rating only or add text
        keyboard = [
            [InlineKeyboardButton("✅ Submit (Rating Only)", callback_data=f"submit_rating_only_{case_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=(
                "📝 *Feedback for Your Case*\n\n"
                f"✅ *Rating Saved:* {rating_text}\n\n"
                "💬 *Step 2 of 2: Written Feedback (Optional)*\n\n"
                "Please type your detailed feedback about:\n"
                "• Your counselor's helpfulness\n"
                "• What went well\n"
                "• What could be improved\n"
                "• Any other comments\n\n"
                "_Or click the button below to submit your rating without text._"
            ),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # Handle submit rating only (no text)
    elif callback_data.startswith('submit_rating_only_'):
        try:
            case_id = int(callback_data.split('_')[-1])
            rating = context.user_data.get('feedback_rating')
            
            token = get_access_token(update)
            if not token:
                await query.edit_message_text("❌ Authentication error. Please try /start.")
                return
            
            # Submit feedback with rating only, no text
            feedback_resp = backend_request(
                '/api/feedbacks/',
                method='post',
                token=token,
                json={
                    'case': case_id,
                    'content': '(No written feedback provided)',
                    'rating': rating
                }
            )
            
            if feedback_resp.ok:
                rating_text = "⭐" * rating if rating else "No rating"
                await query.edit_message_text(
                    f"✅ *Thank You for Your Feedback!*\n\n"
                    f"🌟 Rating: {rating_text}\n\n"
                    f"Your feedback has been successfully recorded and will help us improve our service.\n\n"
                    f"We appreciate you taking the time to share your experience!",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to submit feedback. Please try again later."
                )
            
            # Clear feedback data
            context.user_data.pop('feedback_case_id', None)
            context.user_data.pop('feedback_rating', None)
            context.user_data.pop('feedback_step', None)
            
        except Exception as e:
            print(f"ERROR: Failed to submit rating-only feedback: {str(e)}")
            await query.edit_message_text("❌ Error submitting feedback.")


# ─── Main ───

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Multi-step conversation for /newcase
    newcase_handler = ConversationHandler(
        entry_points=[
            CommandHandler('newcase', newcase_start),
            MessageHandler(filters.Regex('^(📝 New Case|New Case)$'), newcase_start)
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_description)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_confirm)],
        },
        fallbacks=[CommandHandler('cancel', newcase_cancel)],
    )

    # Multi-step conversation for /reply
    reply_handler = ConversationHandler(
        entry_points=[
            CommandHandler('reply', reply_start),
            MessageHandler(filters.Regex('^(💬 Reply|Reply)$'), reply_start)
        ],
        states={
            REPLY_CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, reply_case_id)],
            REPLY_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reply_content)],
        },
        fallbacks=[CommandHandler('cancel', reply_cancel)],
    )

    # Multi-step (or inline) conversation for /viewcase
    viewcase_handler = ConversationHandler(
        entry_points=[
            CommandHandler('viewcase', viewcase_start),
            MessageHandler(filters.Regex('^(👁️ Viewcase|👁️ View Case|Viewcase|View Case)$'), viewcase_start)
        ],
        states={
            VIEW_CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, viewcase_id)],
        },
        fallbacks=[CommandHandler('cancel', viewcase_cancel)],
    )

    reopen_handler = ConversationHandler(
        entry_points=[
            CommandHandler('reopen', reopen_start),
            MessageHandler(filters.Regex('^(🔄 Reopen Case|Reopen Case|Reopen)$'), reopen_start)
        ],
        states={
            REOPEN_CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, reopen_case_id)],
        },
        fallbacks=[CommandHandler('cancel', reopen_cancel)],
    )

    closecase_handler = ConversationHandler(
        entry_points=[
            CommandHandler('closecase', closecase_start),
            MessageHandler(filters.Regex('^(❌ Close Case|Close Case|Close)$'), closecase_start)
        ],
        states={
            CLOSE_CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, closecase_confirm)],
        },
        fallbacks=[CommandHandler('cancel', closecase_cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(newcase_handler)
    
    # Feedback inline button handlers (must be before text handler)
    # Handle all feedback-related callbacks: feedback_, rating_, submit_rating_only_
    application.add_handler(CallbackQueryHandler(handle_feedback_button, pattern='^(feedback_|rating_|submit_rating_only_)'))
    
    # Removed /mycases and /switchcase commands as per new workflow
    
    application.add_handler(reply_handler)
    application.add_handler(viewcase_handler)
    application.add_handler(reopen_handler)
    application.add_handler(closecase_handler)
    
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.Regex('^(❓ Help|Help)$'), help_command))

    # Voice message handler
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # General text handler for seamless chat (with feedback support)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_with_feedback))

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
        await update.message.reply_text(f'✅ Message sent.')
    else:
        await update.message.reply_text(f'⚠️ Failed: {response.text}')


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("🤖 TELEGRAM BOT STARTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
        print("=" * 60)
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
