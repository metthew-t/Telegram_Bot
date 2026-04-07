import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN environment variable is required')


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
    username = update.effective_user.username or update.effective_user.first_name or f'user_{update.effective_user.id}'
    response = login_or_register(update.effective_user.id, username)
    if not response.ok:
        return None
    return response.json().get('access')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        return

    response = login_or_register(update.effective_user.id, update.effective_user.username or update.effective_user.first_name or f'user_{update.effective_user.id}')
    if not response.ok:
        await update.message.reply_text('Unable to reach the backend. Please try again later.')
        return

    await update.message.reply_text(
        'Welcome! Your Telegram support account is ready.\n'
        'Use /newcase <title> | <description> to open a new case.\n'
        'Use /mycases to review your cases.\n'
        'Use /message <case_id> | <message> to send an update to a case.'
    )


async def newcase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    payload = ' '.join(context.args)
    if '|' not in payload:
        await update.message.reply_text('Usage: /newcase <title> | <description>')
        return

    title, description = [part.strip() for part in payload.split('|', 1)]
    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('Unable to authenticate with the backend.')
        return

    response = backend_request('/api/cases/', token=token, json={'title': title, 'description': description})
    if response.ok:
        data = response.json()
        await update.message.reply_text(f'Case created: {data.get("id")} - {data.get("title")}')
    else:
        await update.message.reply_text(f'Failed to create case: {response.text}')


async def list_cases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('Unable to authenticate with the backend.')
        return

    response = backend_request('/api/cases/', method='get', token=token)
    if not response.ok:
        await update.message.reply_text('Unable to fetch your cases.')
        return

    cases = response.json()
    if not cases:
        await update.message.reply_text('You have no open cases yet.')
        return

    message_lines = ['Your cases:']
    for case in cases:
        message_lines.append(f"{case['id']}: {case['title']} ({case['status']})")
    await update.message.reply_text('\n'.join(message_lines))


async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    payload = ' '.join(context.args)
    if '|' not in payload:
        await update.message.reply_text('Usage: /message <case_id> | <message>')
        return

    case_id, content = [part.strip() for part in payload.split('|', 1)]
    token = get_access_token(update)
    if token is None:
        await update.message.reply_text('Unable to authenticate with the backend.')
        return

    response = backend_request(
        '/api/messages/',
        token=token,
        json={'case': case_id, 'content': content},
    )
    if response.ok:
        await update.message.reply_text('Message sent successfully.')
    else:
        await update.message.reply_text(f'Failed to send message: {response.text}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    await update.message.reply_text(
        '/start - Register your Telegram account\n'
        '/newcase <title> | <description> - Open a new support case\n'
        '/mycases - List your cases\n'
        '/message <case_id> | <message> - Send a message to a case'
    )


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('newcase', newcase))
    application.add_handler(CommandHandler('mycases', list_cases))
    application.add_handler(CommandHandler('message', send_message))
    application.add_handler(CommandHandler('help', help_command))

    application.run_polling()


if __name__ == '__main__':
    main()
