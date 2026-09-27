# 🔧 Email Verification Fix Guide

## ❌ Current Problem

When you register on your site, you see:
> "Please verify your email address before logging in. Check your inbox for the verification link."

But **NO EMAIL arrives** in your inbox.

---

## 🔍 Root Cause

Looking at your deployment logs, there is **NO evidence** of email sending attempts. This is because:

**`BREVO_API_KEY` environment variable is NOT configured on Render.**

When the key is missing, the code skips email sending:
```python
api_key = os.getenv('BREVO_API_KEY')
if not api_key:
    print(f"\n[Brevo Skipped] BREVO_API_KEY not found. Email not sent.")
    return
```

---

## ✅ SOLUTION: Add Environment Variables to Render

### Step 1: Get Your Brevo API Key

1. **Go to Brevo**: https://app.brevo.com (login)
2. **Navigate to**: Settings → SMTP & API → API Keys
3. **Create or Copy** your API key (looks like: `xkeysib-xxxxx...`)

If you don't have a Brevo account:
- Sign up at https://www.brevo.com
- Verify your email
- Add a sender email (astucounselplatform@gmail.com)
- Generate API key

### Step 2: Add Environment Variables on Render

1. **Open Render Dashboard**: https://dashboard.render.com
2. **Select Your Service**: `telegram-bot-tazz`
3. **Go to "Environment" Tab** (left sidebar)
4. **Click "Add Environment Variable"**

### Step 3: Add These Variables

Add each of these variables one by one:

#### Required for Email:
```
Name: BREVO_API_KEY
Value: xkeysib-your-actual-api-key-here
```

#### Required for Links in Email:
```
Name: FRONTEND_URL
Value: https://astucounsellingplatform.netlify.app
```

```
Name: BACKEND_URL  
Value: https://telegram-bot-tazz.onrender.com
```

#### Optional (if not already set):
```
Name: DEFAULT_FROM_EMAIL
Value: ASTU Counselling <astucounselplatform@gmail.com>
```

### Step 4: Save and Redeploy

1. Click **"Save Changes"**
2. Render will **automatically redeploy** your service
3. Wait ~2-3 minutes for deployment to complete

---

## 🧪 Testing After Fix

Once redeployment completes:

### Test 1: Check Logs for Email Confirmation

After adding `BREVO_API_KEY`, when someone registers, you should see in Render logs:

```
✅ SUCCESS LOG:
[Email] Sent '✉ Please verify your email — Counselling Platform' to 1 recipient(s) via Brevo.
```

### Test 2: Register New Account

1. Go to: https://astucounsellingplatform.netlify.app/register
2. Register with a **real email address**
3. Check your **inbox** and **spam folder**
4. You should receive email with **"✔ Verify My Email Address"** button

### Test 3: Complete Verification

1. Click the verify button in email
2. Should redirect to success page
3. Click "Log In to Your Account"
4. Should see **green success banner**
5. Login successfully!

---

## 📊 How to Verify Email Configuration

### Check if BREVO_API_KEY is Set

After adding the variables, check Render logs when you register:

**❌ Before Fix** (Current - No Email):
```
[NO LOG MESSAGES ABOUT EMAIL AT ALL]
```

**✅ After Fix** (Should See):
```
[Email] Sent '✉ Please verify your email — Counselling Platform' to 1 recipient(s) via Brevo.
```

**⚠️ If Still Not Working**:
```
[Brevo Skipped] BREVO_API_KEY not found. Email to [email] not sent.
```
→ This means the API key is still not set correctly

---

## 🐛 Troubleshooting

### Issue: Still No Email After Adding API Key

**Solution 1**: Check API Key is Correct
- Make sure you copied the **full** API key from Brevo
- API key should start with `xkeysib-`
- No extra spaces before/after the key

**Solution 2**: Check Brevo Account Status
- Log in to Brevo dashboard
- Verify your account is active
- Check you have remaining email quota (free plan: 300/day)
- Verify sender email (astucounselplatform@gmail.com) is added and verified

**Solution 3**: Check Email Goes to Spam
- Check your **spam/junk** folder
- Add `astucounselplatform@gmail.com` to contacts
- Mark as "Not Spam" if found there

**Solution 4**: Test with Different Email
- Try registering with:
  - Gmail account
  - Outlook/Hotmail account
  - Yahoo account
- Sometimes one provider might block initially

### Issue: Email Arrives But No Button

This is already fixed in the code! The new email template has a large prominent button.

If you still see a plain text email:
- Clear your email cache
- The old emails were sent before the fix
- New registrations will have the button

---

## 📋 Environment Variables Checklist

Make sure ALL these are set on Render:

- [x] `DATABASE_URL` (should already be set by Render)
- [x] `SECRET_KEY` (should already be set)
- [ ] **`BREVO_API_KEY`** ← **YOU NEED TO ADD THIS**
- [ ] **`FRONTEND_URL`** ← **YOU NEED TO ADD THIS**
- [ ] **`BACKEND_URL`** ← **YOU NEED TO ADD THIS**
- [ ] `DEFAULT_FROM_EMAIL` (optional, has default value)
- [ ] `TELEGRAM_BOT_TOKEN` (optional, only needed for Telegram bot feature)

---

## 🎯 Expected Result After Fix

### Registration Flow:

1. User registers → Sees "Check Your Email" page ✅
2. User checks inbox → Receives email with button ✅
3. User clicks "✔ Verify My Email Address" → Success page ✅
4. User clicks "Log In" → Green success banner ✅
5. User logs in → Authenticated successfully ✅

### Email Content:

```
From: ASTU Counselling <astucounselplatform@gmail.com>
Subject: ✉ Please verify your email — Counselling Platform

[Professional Dark Theme Design]
⚖ Counsel
Support & Case Management System
📧 Email Verification Required

✉️ Welcome, [username]!

Thank you for registering...

┌───────────────────────────────┐
│ ✔ Verify My Email Address    │  ← Large Button
│   [PROMINENT BUTTON]          │
└───────────────────────────────┘

Or copy this link: http://...
```

---

## 📞 Still Having Issues?

If after adding `BREVO_API_KEY` you still don't receive emails:

1. **Check Render Logs** - Look for "[Email]" messages
2. **Verify Brevo Dashboard** - Check if emails are being sent
3. **Test Email Address** - Make sure email is valid
4. **Check Spam Folder** - Emails might be filtered

---

## 🚨 About Telegram Bot Errors (Separate Issue)

The logs show Telegram bot errors:
```
telegram.error.InvalidToken: The token 8228914532:AAH... was rejected by the server
```

**This is a SEPARATE issue** and does NOT affect email verification.

To fix Telegram bot (optional):
1. Get a new bot token from @BotFather on Telegram
2. Update `TELEGRAM_BOT_TOKEN` environment variable on Render
3. Or just ignore it if you don't need the Telegram bot feature

The Django web server and email verification work independently of the Telegram bot.

---

## ✅ Summary

**Problem**: BREVO_API_KEY not configured  
**Solution**: Add BREVO_API_KEY to Render environment variables  
**Expected Time**: 5 minutes to configure + 2-3 minutes redeploy  
**Result**: Emails will be sent successfully with verify button  

**Next Steps**:
1. Get Brevo API key
2. Add to Render environment
3. Wait for redeploy
4. Test registration
5. Check email arrives with button!

🎉 **Your email verification will work perfectly after this!**
