# 🔧 FIX TELEGRAM NOTIFICATIONS - Step by Step

## 🎯 THE ISSUE:
Text from admin is not reaching the user on Telegram.

## 🔍 MOST COMMON CAUSES:

### 1. User Hasn't Sent /start to Bot (90% of cases)
**Why:** Bot can only send messages to users who have started a conversation with it first.

**Solution:**
1. User opens Telegram
2. User searches for your bot
3. User sends `/start`
4. Bot responds with welcome message
5. **NOW** admin replies will reach the user!

---

### 2. User Created Case on Website (Not Telegram)
**Why:** If user registered on website directly, they don't have telegram_id.

**Solution:**
1. User must send `/start` to bot on Telegram
2. Bot will link their Telegram account
3. Admin replies will now reach them

---

### 3. Telegram ID Not Saved in Database
**Why:** Sometimes the /start command doesn't save the telegram_id properly.

**Solution:**
Run this on Render Shell:

```bash
# Check which users have telegram_id
python backend/check_telegram_ids.py
```

This will show you:
- Which users have telegram_id ✅
- Which users need to /start bot ❌
- All cases and notification status

---

## ✅ STEP-BY-STEP FIX:

### Step 1: Check Render Logs
1. Go to: https://dashboard.render.com
2. Click your service
3. Click "Logs" tab
4. Admin sends a message to a case
5. Look for these lines:

```
[TELEGRAM NOTIFICATION] Admin/Owner replied to case #1
[TELEGRAM NOTIFICATION] Case user: username
[TELEGRAM NOTIFICATION] Case user telegram_id: 123456789
[send_telegram_notification] CALLED
[send_telegram_notification] HTTP Response status: 200
✅ Message sent successfully!
```

**If you see:**
- `telegram_id: None` → User needs to /start bot
- `chat not found` → User needs to /start bot
- `bot was blocked` → User blocked the bot (unblock it)
- `HTTP Response status: 200` → Message WAS sent! Check Telegram

---

### Step 2: User Must Send /start

**Critical:** User MUST send `/start` BEFORE creating cases or BEFORE admin replies.

**The correct flow:**
1. ✅ User sends `/start` to bot
2. ✅ Bot responds (saves telegram_id)
3. ✅ User creates case with `/newcase`
4. ✅ Admin replies on website
5. ✅ User receives notification!

**Wrong flow (won't work):**
1. ❌ User creates case on website
2. ❌ Admin replies
3. ❌ User doesn't receive notification (no telegram_id!)

**Fix:** User sends `/start` to bot now, then it will work for future messages.

---

### Step 3: Verify telegram_id is Saved

**On Render:**

```bash
# Open Render Shell
python backend/manage.py shell

# Run this:
from counselling.models import User
users = User.objects.filter(role='user')
for u in users:
    print(f"{u.username}: telegram_id={u.telegram_id}")
```

**Expected output:**
```
john_doe: telegram_id=123456789
mary_jane: telegram_id=987654321
test_user: telegram_id=None  ← This user needs to /start bot!
```

---

### Step 4: Test Notification Manually

**Test if notification works:**

```bash
# On Render Shell
python backend/manage.py shell

# Run this (replace with real telegram_id):
from counselling.views import send_telegram_notification
send_telegram_notification('123456789', 'Test message from admin!')
```

**If this works:** The issue is that telegram_id is not saved for the user.
**If this fails:** Token might be wrong or Telegram API issue.

---

## 🎯 QUICK DIAGNOSTIC:

### Scenario A: User Created Case via Telegram Bot
**Should work!** telegram_id is saved automatically.

**If not working:**
1. Check Render logs for error messages
2. User might have blocked the bot → Unblock it
3. Bot token might be wrong → Regenerate

---

### Scenario B: User Created Case via Website
**Won't work until:** User sends `/start` to bot on Telegram.

**Solution:**
Tell user to:
1. Open Telegram
2. Search for the bot
3. Send `/start`
4. From now on, notifications will work!

---

## 🔧 RENDER SHELL COMMANDS:

### Check Users:
```bash
python backend/manage.py shell
```

Then run:
```python
from counselling.models import User
User.objects.filter(role='user').values('username', 'telegram_id')
```

### Check Cases:
```python
from counselling.models import Case
for case in Case.objects.all():
    print(f"Case #{case.id}: {case.user.username} - telegram_id: {case.user.telegram_id}")
```

### Test Notification:
```python
from counselling.views import send_telegram_notification
send_telegram_notification('YOUR_TELEGRAM_ID', 'Test!')
```

---

## 💡 COMMON ERRORS IN LOGS:

### Error: "chat not found"
**Meaning:** User hasn't started conversation with bot.
**Fix:** User sends `/start` to bot.

### Error: "bot was blocked by the user"
**Meaning:** User blocked the bot.
**Fix:** User unblocks the bot in Telegram.

### Error: "Forbidden: bot can't initiate conversation"
**Meaning:** Bot can't message users who haven't messaged it first.
**Fix:** User sends `/start` to bot.

### Success: "HTTP Response status: 200"
**Meaning:** Message WAS sent successfully!
**Fix:** Check user's Telegram - message should be there.

---

## 🎯 MOST LIKELY SOLUTION:

**90% of the time, the fix is:**

1. User opens Telegram
2. User searches for bot
3. User sends `/start`
4. Bot responds
5. **NOW** notifications work!

**Even if user already has a case, they must /start the bot for notifications to work.**

---

## 🆘 STILL NOT WORKING?

If you've tried everything above and it's still not working:

### Option 1: Check Environment Variables
On Render:
1. Click "Environment" tab
2. Check `TELEGRAM_BOT_TOKEN` is correct
3. Check `BACKEND_URL` points to your Render backend

### Option 2: Generate New Bot Token
1. Message @BotFather on Telegram
2. Send `/mybots`
3. Select your bot
4. Click "API Token"
5. Click "Revoke current token"
6. Copy new token
7. Update on Render
8. Save and redeploy

**Then give me the new token and I'll update everything!**

---

## ✅ CHECKLIST:

Before saying "it's not working," verify:

- [ ] User has sent `/start` to bot on Telegram
- [ ] Bot responded to `/start` (if not, bot isn't running)
- [ ] Admin sent message to the case on website
- [ ] Checked Render logs for notification attempt
- [ ] Telegram_id is not None in database
- [ ] User hasn't blocked the bot
- [ ] Bot token is correct in Render environment

---

## 🎊 WHEN IT'S WORKING:

You'll know notifications work when:
1. Admin sends message on website
2. User immediately gets notification on Telegram
3. Render logs show "✅ Message sent successfully!"
4. No errors in logs

---

**Next step:** Check Render logs when admin sends a message and send me the output!
