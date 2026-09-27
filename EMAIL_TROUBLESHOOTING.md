# 🔍 Email Not Sending - Troubleshooting Guide

## ✅ What's Working
- Backend API: ✅
- Frontend: ✅
- Telegram Bot: ✅
- Login: ✅

## ❌ What's Not Working
- Brevo emails not being sent during registration

---

## 🎯 **Step-by-Step Diagnosis**

### Step 1: Wait for Deployment (3 minutes)

The latest code with detailed logging has been pushed. Wait for Render to redeploy automatically.

### Step 2: Test Registration & Check Logs

1. Go to: https://astucounsellingplatform.netlify.app/register
2. Register with a **NEW** username and email
3. Immediately go to **Render Dashboard** → **Logs**
4. **Look for these debug messages**:

#### ✅ What You SHOULD See (Everything Working):
```
[DEBUG] send_verification_email called for user: testuser, email: test@example.com
[DEBUG] Token generated and saved: xxxxxx-xxxx-xxxx
[ACTION REQUIRED] VERIFICATION LINK FOR testuser:
https://telegram-bot-tazz.onrender.com/api/verify-email/?token=xxxxx
[DEBUG] Email rendered. Subject: ✉ Please verify your email
[DEBUG] Calling _send_email to: test@example.com
[DEBUG] _send_email called with 1 recipients
[DEBUG] Recipients: ['test@example.com']
[DEBUG] BREVO_API_KEY found: xkeysib-a7b...xqVxtr
[DEBUG] DEFAULT_FROM_EMAIL: ASTU Counselling <astucounselplatform@gmail.com>
[DEBUG] Parsed sender: {'email': 'astucounselplatform@gmail.com', 'name': 'ASTU Counselling'}
[DEBUG] Sending request to Brevo API...
[DEBUG] Brevo API response status: 201
[Email] ✅ Sent '✉ Please verify your email' to 1 recipient(s) via Brevo.
```

#### ❌ Problem Scenarios:

**Scenario A: API Key Not Found**
```
[Brevo Skipped] BREVO_API_KEY not found. Email to ['test@example.com'] not sent.
```
→ **Fix**: Double-check BREVO_API_KEY in Render environment variables

**Scenario B: Brevo API Error 401 (Unauthorized)**
```
[DEBUG] Brevo API response status: 401
[Email] ❌ Brevo API Error 401: {"message":"Invalid API key"}
```
→ **Fix**: Your API key is wrong or expired. Get a new one from Brevo.

**Scenario C: Brevo API Error 400 (Bad Request)**
```
[DEBUG] Brevo API response status: 400
[Email] ❌ Brevo API Error 400: {"message":"Sender email not verified"}
```
→ **Fix**: You need to verify `astucounselplatform@gmail.com` in Brevo dashboard

**Scenario D: No Debug Logs at All**
```
(No [DEBUG] messages appear)
```
→ **Fix**: Registration didn't trigger email sending. Check if email field was filled.

---

## 🔧 **Common Fixes**

### Fix 1: Verify Sender Email in Brevo

This is the **MOST COMMON** issue!

1. Go to Brevo dashboard: https://app.brevo.com
2. Go to **Settings** → **Senders & IP**
3. Check if `astucounselplatform@gmail.com` is listed
4. If NOT listed:
   - Click **"Add a sender"**
   - Email: `astucounselplatform@gmail.com`
   - Follow verification steps
5. If listed but not verified:
   - Click **"Resend verification email"**
   - Check Gmail inbox for verification link
   - Click the link to verify

### Fix 2: Check API Key is Correct

1. Go to Brevo: https://app.brevo.com/settings/keys/api
2. Your API key should be there
3. Copy the FULL key (don't miss any characters)
4. Go to Render → Environment
5. Edit `BREVO_API_KEY`
6. Paste the full key
7. Save

### Fix 3: Check Brevo Account Status

1. Log in to Brevo
2. Check if account is active (not suspended)
3. Check email quota:
   - Free plan: 300 emails/day
   - Make sure you haven't exceeded limit

### Fix 4: Use Alternative Sender Email

If `astucounselplatform@gmail.com` can't be verified:

1. In Render, add a new environment variable:
   ```
   DEFAULT_FROM_EMAIL=YourVerifiedEmail@example.com
   ```
2. Make sure this email is verified in Brevo
3. Redeploy

---

## 🧪 **Run Test Script Manually**

If you have SSH access to your server:

```bash
cd /app/backend
python test_email.py
```

This will:
- ✅ Check if BREVO_API_KEY is set
- ✅ Test API connection
- ✅ List all verified senders
- ✅ Send a test email (if you provide your email)

---

## 📊 **Checklist**

After redeploy, verify each item:

- [ ] BREVO_API_KEY is set in Render
- [ ] BREVO_API_KEY is correct (from Brevo dashboard)
- [ ] DEFAULT_FROM_EMAIL matches a verified sender in Brevo
- [ ] astucounselplatform@gmail.com is verified in Brevo
- [ ] Brevo account is active (not suspended)
- [ ] Haven't exceeded daily email quota (300 for free plan)
- [ ] Tried registering with a FRESH email
- [ ] Checked Render logs for [DEBUG] messages
- [ ] Checked email spam folder

---

## 🎯 **Most Likely Issue**

Based on similar cases, the most common problem is:

**❌ Sender email `astucounselplatform@gmail.com` is NOT verified in Brevo**

### How to Fix:

1. Log in to Brevo: https://app.brevo.com
2. Go to Settings → Senders & IP
3. Find `astucounselplatform@gmail.com`
4. If it shows "Not verified" → Click verify
5. Check the Gmail inbox for that address
6. Click the verification link in the email
7. Return to Brevo → Should now show "Verified" ✅
8. Try registering again

---

## 📞 **Next Steps**

1. **Now**: Wait 3 minutes for Render to redeploy with debug logs
2. **Then**: Try registering with a new account
3. **Check**: Render logs for the [DEBUG] messages above
4. **Reply**: Copy the log output showing what happens
5. **I'll help**: Based on the specific error in logs

The debug logs will tell us **exactly** what's wrong! 🔍
