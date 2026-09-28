# 🔧 RENDER ENVIRONMENT VARIABLES - COMPLETE SETUP

## 📋 REQUIRED ENVIRONMENT VARIABLES ON RENDER:

Go to Render Dashboard → Your Service → Environment Tab

### 1. Django Settings:
```
SECRET_KEY=your-secure-random-key-here-min-50-chars
DEBUG=False
ALLOWED_HOSTS=telegram-bot-backend-bwu4.onrender.com,.onrender.com
```

### 2. Database:
```
DATABASE_URL=<automatically set by Render if PostgreSQL attached>
```

### 3. Telegram Bot (CRITICAL!):
```
TELEGRAM_BOT_TOKEN=8734303504:AAHKMNuQgutfBpfVGUuutb82rTfQBGAcqTc
BACKEND_URL=https://telegram-bot-backend-bwu4.onrender.com
```

### 4. Frontend:
```
FRONTEND_URL=https://astu-counselling-platform.vercel.app
```

### 5. Email (Optional but recommended):
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=astucounselplatform@gmail.com
EMAIL_HOST_PASSWORD=uuojgdrbxojqtbac
DEFAULT_FROM_EMAIL=Counsel Support <astucounselplatform@gmail.com>
```

---

## ⚠️ CRITICAL CHECKS:

### Check 1: TELEGRAM_BOT_TOKEN
**Must be EXACTLY:**
```
8734303504:AAHKMNuQgutfBpfVGUuutb82rTfQBGAcqTc
```

**Common mistakes:**
- Extra spaces at beginning or end ❌
- Missing colon `:` ❌
- Truncated token ❌

**How to verify:**
1. Copy token from Render
2. Paste in notepad
3. Check length: Should be 46 characters
4. Check format: `numbers:letters`

---

### Check 2: BACKEND_URL
**Must be EXACTLY:**
```
https://telegram-bot-backend-bwu4.onrender.com
```

**Common mistakes:**
- Missing `https://` ❌
- Wrong subdomain ❌
- Trailing slash `/` (should NOT have it) ❌

---

### Check 3: FRONTEND_URL
**Must be EXACTLY:**
```
https://astu-counselling-platform.vercel.app
```

**No trailing slash!**

---

## 🔍 HOW TO CHECK CURRENT VALUES:

### Method 1: Render Dashboard
1. Go to: https://dashboard.render.com
2. Click your service
3. Click "Environment" tab
4. Check each variable

### Method 2: Render Shell
```bash
# In Render Shell
echo "Bot Token: $TELEGRAM_BOT_TOKEN"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
```

---

## 🎯 MOST LIKELY ISSUE:

Based on the error pattern, one of these is wrong:

### Scenario A: TELEGRAM_BOT_TOKEN is wrong
**Symptoms:** Bot can't send notifications
**Check:** Token matches BotFather token exactly
**Fix:** Copy token from BotFather, paste in Render

### Scenario B: BACKEND_URL is wrong
**Symptoms:** Bot can't reach backend API
**Check:** URL is exactly `https://telegram-bot-backend-bwu4.onrender.com`
**Fix:** Update BACKEND_URL environment variable

### Scenario C: Bot is using old environment
**Symptoms:** Changes not taking effect
**Check:** Service restarted after variable changes
**Fix:** Manual redeploy after changing variables

---

## 🔧 STEP-BY-STEP FIX:

### Step 1: Verify Bot Token

**Get token from BotFather:**
1. Open Telegram
2. Message @BotFather
3. Send `/mybots`
4. Select your bot
5. Click "API Token"
6. Copy the FULL token

**Update on Render:**
1. Go to Environment tab
2. Find `TELEGRAM_BOT_TOKEN`
3. Paste the full token (no spaces!)
4. Click "Save Changes"
5. Wait for auto-redeploy

---

### Step 2: Verify BACKEND_URL

**On Render Environment tab:**
```
Key: BACKEND_URL
Value: https://telegram-bot-backend-bwu4.onrender.com
```

**Important:**
- Must have `https://` ✅
- Must NOT have trailing `/` ✅
- Must be YOUR render URL ✅

---

### Step 3: Force Redeploy

After changing any environment variable:
1. Click "Manual Deploy" button
2. Select "Clear build cache & deploy"
3. Wait 3-5 minutes
4. Check logs for bot startup

---

## 📊 VERIFY DEPLOYMENT:

### Check Logs:
Look for these messages in Render logs:
```
🤖 Starting Telegram Bot...
✅ Bot started with PID: 63
🚀 Starting Django Web Server on port 10000...
[INFO] Booting worker with pid: 67
```

**Good signs:** ✅
- No "Conflict" errors
- Bot PID shows
- Workers booted

**Bad signs:** ❌
- "Conflict: terminated by other getUpdates"
- "Invalid token"
- "Connection refused"

---

## 🧪 TEST AFTER FIXING:

### Test 1: Bot Responds
```
User sends: /start
Bot should respond: Welcome message
```

### Test 2: Notification Test
```bash
# In Render Shell
cd backend
python manage.py shell

# Run:
from counselling.views import send_telegram_notification
send_telegram_notification('YOUR_USER_TELEGRAM_ID', 'Test from Render!')
```

**Replace `YOUR_USER_TELEGRAM_ID` with actual user's Telegram ID from database.**

---

## 🔐 GET USER'S TELEGRAM ID:

### Method 1: Check Database
```bash
# In Render Shell
cd backend
python manage.py shell

# Run:
from counselling.models import User
for u in User.objects.filter(role='user'):
    print(f"{u.username}: {u.telegram_id}")
```

### Method 2: Ask User
User sends `/start` to bot, then:
```bash
# In Render Shell
cd backend
python manage.py shell

# Run:
from counselling.models import User
latest_user = User.objects.filter(role='user').order_by('-id').first()
print(f"Latest user: {latest_user.username}")
print(f"Telegram ID: {latest_user.telegram_id}")
```

---

## 💡 COMMON RENDER ISSUES:

### Issue 1: Variables Not Taking Effect
**Symptom:** Changed variable but still using old value
**Cause:** Render didn't restart service
**Fix:** Manual redeploy

### Issue 2: Bot Token Invalid
**Symptom:** 401 errors in logs
**Cause:** Token copied wrong or revoked
**Fix:** Get fresh token from BotFather

### Issue 3: Multiple Bot Instances
**Symptom:** "Conflict: terminated by other getUpdates"
**Cause:** Bot running locally AND on Render
**Fix:** Stop local bot, wait 60 seconds

### Issue 4: Database Not Migrated
**Symptom:** No telegram_id field
**Cause:** Migration not run
**Fix:** Run `python backend/manage.py migrate` in Render Shell

---

## 🎯 RECOMMENDED RENDER SETTINGS:

### Build Command:
```bash
bash build.sh
```

### Start Command:
```bash
bash start.sh
```

### Environment Variables (Full List):
```
SECRET_KEY=<long-random-string-50-chars>
DEBUG=False
ALLOWED_HOSTS=telegram-bot-backend-bwu4.onrender.com,.onrender.com
DATABASE_URL=<auto-set-by-postgres>
TELEGRAM_BOT_TOKEN=8734303504:AAHKMNuQgutfBpfVGUuutb82rTfQBGAcqTc
BACKEND_URL=https://telegram-bot-backend-bwu4.onrender.com
FRONTEND_URL=https://astu-counselling-platform.vercel.app
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=astucounselplatform@gmail.com
EMAIL_HOST_PASSWORD=uuojgdrbxojqtbac
```

---

## 🔍 DIAGNOSTIC CHECKLIST:

Check each one:

- [ ] TELEGRAM_BOT_TOKEN is exactly 46 characters
- [ ] TELEGRAM_BOT_TOKEN has format: `numbers:letters`
- [ ] BACKEND_URL starts with `https://`
- [ ] BACKEND_URL has NO trailing slash
- [ ] BACKEND_URL matches your actual Render URL
- [ ] FRONTEND_URL matches your actual Vercel URL
- [ ] Service redeployed after variable changes
- [ ] No "Conflict" errors in logs
- [ ] Bot PID shows in logs
- [ ] Workers booted successfully
- [ ] User has telegram_id in database
- [ ] User sent /start to bot

---

## 🆘 IF STILL NOT WORKING:

### Last Resort: Fresh Bot Token

1. **Get new token:**
   - Message @BotFather
   - Send `/mybots`
   - Select bot
   - API Token → Revoke current token
   - Copy NEW token

2. **Update EVERYWHERE:**
   - Render environment variable
   - Local `.env` file (if testing locally)
   
3. **Redeploy:**
   - Manual deploy on Render
   - Wait 3 minutes
   - Test again

---

## ✅ VERIFICATION SCRIPT:

Run this in Render Shell to check everything:

```bash
cd backend
python manage.py shell << EOF
from counselling.models import User
from counselling.views import send_telegram_notification
import os

print("=" * 60)
print("ENVIRONMENT CHECK")
print("=" * 60)

# Check environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
backend_url = os.getenv('BACKEND_URL')

print(f"Bot Token: {bot_token[:20]}...{bot_token[-6:] if bot_token else 'MISSING'}")
print(f"Backend URL: {backend_url}")

# Check users with telegram_id
users = User.objects.filter(role='user').exclude(telegram_id__isnull=True)
print(f"\nUsers with Telegram ID: {users.count()}")

for u in users:
    print(f"  - {u.username}: {u.telegram_id}")
    # Test notification
    print(f"    Testing notification...")
    result = send_telegram_notification(u.telegram_id, "🧪 Test from Render Shell")
    print(f"    Result: {'✅ SUCCESS' if result else '❌ FAILED'}")

print("=" * 60)
EOF
```

---

**Copy this output and send it to me!** It will show exactly what's wrong.
