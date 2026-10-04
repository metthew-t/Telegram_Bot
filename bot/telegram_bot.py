import os
import requests
import base64
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

# On Render, gunicorn listens on $PORT, not 8000
_port = os.environ.get('PORT', '8000')
BACKEND_URL = os.environ.get('BACKEND_URL', f'http://127.0.0.1:{_port}')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN environment variable is required')

# Persistent main menu keyboard layout
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ['📝 New Case', '📋 My Cases'],
        ['👁️ View Case', '💬 Reply'],
        ['❓ Help']
    ],
    resize_keyboard=True
)

# ConversationHandler states
TITLE, DESCRIPTION, CONFIRM = range(3)
REPLY_CASE_ID, REPLY_CONTENT = range(10, 12)
VIEW_CASE_ID = 20


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
        '📋 /mycases — View your cases\n'
        '💬 /reply — Reply to a case\n'
        '👁️ /viewcase — View messages on a case\n'
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
    for case in cases:
        icon = status_icons.get(case['status'], '⚪')
        case_num = case.get('user_case_number', case['id'])
        lines.append(f'{icon} *Your Case #{case_num}* — {case["title"]} (`{case["status"]}`)')

    lines.append(f'\n_Total: {len(cases)} case(s)_')
    lines.append('\nUse /viewcase to view messages on a case.')
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
        await update.message.reply_text(
            f'✅ Message sent to case *#{case_id}*.',
            parse_mode='Markdown',
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
        reply_markup=ReplyKeyboardRemove(),
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
            role_tag = f' [{role}]' if role else ''
            lines.append(f'*{label}*{role_tag}:')
            
            # Check if voice message
            if msg.get('message_type') == 'voice' and msg.get('voice_data'):
                duration = msg.get('voice_duration', 0)
                lines.append(f'🎤 Voice message ({duration}s)')
                lines.append('_[Voice messages can be played on the website]_')
            else:
                lines.append(f'{msg["content"]}')
            
            lines.append(f'_{msg.get("timestamp", "")}_\n')

        if len(messages) > 10:
            lines.append(f'_... and {len(messages) - 10} earlier message(s)_')

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
        '/start — Register & get started\n'
        '/newcase — Submit a new support case (step-by-step)\n'
        '/mycases — List all your cases\n'
        '/viewcase — View messages on a case\n'
        '/reply — Reply to a case\n'
        '/help — Show this help message\n'
        '/cancel — Cancel current operation',
        parse_mode='Markdown',
        reply_markup=MAIN_MENU_KEYBOARD,
    )


# ─── /cancel (global fallback) ───

async def check_for_feedback_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check if user's message is feedback for a recently closed case.
    This runs on every message and detects if we're waiting for feedback.
    """
    if update.effective_user is None or update.message is None or not update.message.text:
        return False
    
    # Check if user has a pending feedback case stored in context
    feedback_case_id = context.user_data.get('feedback_case_id')
    
    if feedback_case_id:
        # User is providing feedback
        feedback_text = update.message.text.strip()
        
        token = get_access_token(update)
        if not token:
            return False
        
        # Create feedback via API
        feedback_resp = backend_request(
            '/api/feedbacks/',
            method='post',
            token=token,
            json={
                'case': feedback_case_id,
                'content': feedback_text,
                'user': update.effective_user.id
            }
        )
        
        if feedback_resp.ok:
            await update.message.reply_text(
                '✅ Thank you for your feedback! Your input helps us improve our service.\n\n'
                'Your feedback has been recorded and shared with your counselor.',
                reply_markup=MAIN_MENU_KEYBOARD
            )
            # Clear the pending feedback flag
            context.user_data.pop('feedback_case_id', None)
            return True
        else:
            print(f"DEBUG: Failed to submit feedback: {feedback_resp.text}")
            await update.message.reply_text(
                '⚠️ There was an issue saving your feedback. Please try again later.',
                reply_markup=MAIN_MENU_KEYBOARD
            )
            context.user_data.pop('feedback_case_id', None)
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
    """Seamlessly route plain text messages to the user's active case with simplified case selection."""
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
    
    # Single case - send directly
    if len(cases) == 1:
        case_id = cases[0]['id']
        case_num = cases[0].get('user_case_number', case_id)
        context.user_data['selected_case_id'] = case_id
        print(f"DEBUG: Routing message to case #{case_id}")
        msg_resp = backend_request(
            '/api/messages/',
            token=token,
            json={'case': case_id, 'content': update.message.text, 'message_type': 'text'},
        )
        if msg_resp.ok:
            await update.message.reply_text(f'✅ Sent to your case *#{case_num}*.', parse_mode='Markdown')
        else:
            print(f"DEBUG: Failed to send message to backend: {msg_resp.text}")
            await update.message.reply_text(f'⚠️ Failed to send: {msg_resp.text}')
    
    # Multiple cases - check for case selection
    elif len(cases) > 1:
        message_text = update.message.text.strip()
        
        # Check if user is entering just a case number to select
        if message_text.isdigit():
            case_num = int(message_text)
            # Find case by user_case_number or database ID
            matching_case = next(
                (c for c in cases if c.get('user_case_number') == case_num or c['id'] == case_num),
                None
            )
            
            if matching_case:
                context.user_data['selected_case_id'] = matching_case['id']
                
                # Check if there's a pending message to send
                pending_message = context.user_data.pop('pending_message', None)
                pending_voice = context.user_data.pop('pending_voice', None)
                
                if pending_voice:
                    # Send the pending voice message immediately
                    try:
                        print(f"DEBUG: Sending pending voice to case #{matching_case['id']}")
                        file = await context.bot.get_file(pending_voice['file_id'])
                        voice_bytes = await file.download_as_bytearray()
                        voice_base64 = base64.b64encode(voice_bytes).decode('utf-8')
                        
                        msg_resp = backend_request(
                            '/api/messages/',
                            token=token,
                            json={
                                'case': matching_case['id'],
                                'content': '[Voice Message]',
                                'message_type': 'voice',
                                'voice_data': voice_base64,
                                'voice_duration': pending_voice['duration']
                            },
                        )
                        
                        if msg_resp.ok:
                            await update.message.reply_text(
                                f'✅ 🎤 Voice message sent to case *#{case_num}*: *{matching_case["title"]}*\n\n'
                                f'All future messages will go to this case.',
                                parse_mode='Markdown'
                            )
                        else:
                            await update.message.reply_text(
                                f'✅ Case *#{case_num}* selected: *{matching_case["title"]}*\n\n'
                                f'⚠️ But failed to send voice: {msg_resp.text}',
                                parse_mode='Markdown'
                            )
                    except Exception as e:
                        print(f"ERROR: Failed to send pending voice: {str(e)}")
                        await update.message.reply_text(
                            f'✅ Case *#{case_num}* selected: *{matching_case["title"]}*\n\n'
                            f'⚠️ But failed to send voice message.',
                            parse_mode='Markdown'
                        )
                elif pending_message:
                    # Send the pending message immediately
                    print(f"DEBUG: Sending pending message to case #{matching_case['id']}")
                    msg_resp = backend_request(
                        '/api/messages/',
                        token=token,
                        json={'case': matching_case['id'], 'content': pending_message, 'message_type': 'text'},
                    )
                    if msg_resp.ok:
                        await update.message.reply_text(
                            f'✅ Message sent to case *#{case_num}*: *{matching_case["title"]}*\n\n'
                            f'All future messages will go to this case.',
                            parse_mode='Markdown'
                        )
                    else:
                        print(f"DEBUG: Failed to send pending message: {msg_resp.text}")
                        await update.message.reply_text(
                            f'✅ Case *#{case_num}* selected: *{matching_case["title"]}*\n\n'
                            f'⚠️ But failed to send your message: {msg_resp.text}',
                            parse_mode='Markdown'
                        )
                else:
                    # No pending message, just confirm selection
                    await update.message.reply_text(
                        f'✅ Case *#{case_num}* selected: *{matching_case["title"]}*\n\n'
                        f'All your messages will now go to this case.',
                        parse_mode='Markdown'
                    )
                return
            else:
                await update.message.reply_text(
                    f'⚠️ Case #{case_num} not found in your active cases.',
                    parse_mode='Markdown'
                )
                return
        
        # Check if user has previously selected a case
        selected_case_id = context.user_data.get('selected_case_id')
        if selected_case_id:
            # Verify the case is still active
            matching_case = next((c for c in cases if c['id'] == selected_case_id), None)
            if matching_case:
                case_num = matching_case.get('user_case_number', selected_case_id)
                print(f"DEBUG: Routing message to pre-selected case #{selected_case_id}")
                msg_resp = backend_request(
                    '/api/messages/',
                    token=token,
                    json={'case': selected_case_id, 'content': update.message.text, 'message_type': 'text'},
                )
                if msg_resp.ok:
                    await update.message.reply_text(f'✅ Sent to your case *#{case_num}*.', parse_mode='Markdown')
                else:
                    print(f"DEBUG: Failed to send message to backend: {msg_resp.text}")
                    await update.message.reply_text(f'⚠️ Failed to send: {msg_resp.text}')
                return
            else:
                # Case no longer active, clear selection
                context.user_data.pop('selected_case_id', None)
        
        # No case selected - ask user to select and store the message for later
        context.user_data['pending_message'] = message_text
        case_list = '\n'.join([f"• Case *#{c.get('user_case_number', c['id'])}*: {c['title']}" for c in cases[:10]])
        await update.message.reply_text(
            f'📝 You have {len(cases)} active cases:\n\n{case_list}\n\n'
            f'Please send just the case number (e.g., "1") to send your message.',
            parse_mode='Markdown'
        )
    
    # No cases
    else:
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
    # If user has selected a case previously, use it
    elif selected_case_id:
        # Verify the selected case is still active
        matching_case = next((c for c in cases if c['id'] == selected_case_id), None)
        if matching_case:
            case_id = matching_case['id']
            case_num = matching_case.get('user_case_number', case_id)
        else:
            await update.message.reply_text(
                '📝 Your selected case is no longer active. Please send a text message with the case number to select a different case.',
                parse_mode='Markdown'
            )
            context.user_data.pop('selected_case_id', None)
            return
    # Multiple cases and no selection
    elif len(cases) > 1:
        # Store the voice data for after case selection
        context.user_data['pending_voice'] = {
            'file_id': voice.file_id,
            'duration': voice.duration
        }
        case_list = '\n'.join([f"• Case *#{c.get('user_case_number', c['id'])}*: {c['title']}" for c in cases[:5]])
        await update.message.reply_text(
            f'🎤 Voice message received!\n\n'
            f'📝 You have {len(cases)} active cases:\n\n{case_list}\n\n'
            'Please send the case number (e.g., "1") to send your voice message.',
            parse_mode='Markdown'
        )
        return
    # No cases
    else:
        await update.message.reply_text(
            '👋 You don\'t have any active cases right now.\n\nUse /newcase to start a support request.'
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
            await update.message.reply_text(
                f'✅ 🎤 Voice message sent to your case *#{case_num}*.',
                parse_mode='Markdown'
            )
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

    application.add_handler(CommandHandler('start', start))
    application.add_handler(newcase_handler)
    
    application.add_handler(CommandHandler('mycases', list_cases))
    application.add_handler(MessageHandler(filters.Regex('^(📋 My Cases|My Cases)$'), list_cases))
    
    application.add_handler(reply_handler)
    application.add_handler(viewcase_handler)
    
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
        await update.message.reply_text(f'✅ Message sent to case #{case_id}.')
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
