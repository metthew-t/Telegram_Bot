# 🔧 CRITICAL FIX: Assignment Emails Using Brevo API

## The Problem

You reported that assignment request emails are not working, even though you have:
- ✅ Different email addresses (owner: `astucounselplatform@gmail.com`, admin: `matiwosteferi51@gmail.com`)
- ✅ Brevo API configured for sending emails
- ✅ Other emails working (new case, case closed, internal messages)

## Root Cause Found

The assignment request/approve/reject email functions were using **Django's `send_mail()`** instead of the custom **`_send_email()`** function.

### Why This Matters

Your `settings.py` has this configuration:

```python
if os.getenv('BREVO_API_KEY'):
    # Brevo API is used directly in views.py — Django's backend only needs console.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # No Brevo key → fall back to SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

**When Brevo API key is set**:
- `EMAIL_BACKEND = 'console.EmailBackend'` → Django's `send_mail()` only prints to console (doesn't actually send!)
- `_send_email()` function → Properly uses Brevo API to send real emails

**What was happening**:
1. Admin requests assignment
2. Code called `send_mail()` 
3. Email printed to console but NOT sent via Brevo
4. Owner never received the email ❌

**What was working**:
- New case emails → Uses `_send_email()` → Sent via Brevo ✅
- Case closed emails → Uses `_send_email()` → Sent via Brevo ✅
- Internal messages → Uses `_send_email()` → Sent via Brevo ✅

## The Fix

Changed all three assignment email functions to use `_send_email()`:

### 1. Assignment Request (Admin → Owner)

**BEFORE**:
```python
send_mail(
    subject,
    text_body,
    settings.DEFAULT_FROM_EMAIL,
    [owner.email],
    html_message=html_body,
    fail_silently=True
)
```

**AFTER**:
```python
_send_email(subject, html_body, text_body, [owner.email])
```

### 2. Assignment Approval (Owner → Admin)

**BEFORE**:
```python
send_mail(
    subject,
    text_body,
    settings.DEFAULT_FROM_EMAIL,
    [admin.email],
    html_message=html_body,
    fail_silently=True
)
```

**AFTER**:
```python
_send_email(subject, html_body, text_body, [admin.email])
```

### 3. Assignment Rejection (Owner → Admin)

**BEFORE**:
```python
send_mail(
    subject,
    message,
    settings.DEFAULT_FROM_EMAIL,
    [admin.email],
    fail_silently=True
)
```

**AFTER**:
```python
_send_email(subject, html_body, text_body, [admin.email])
```

## What `_send_email()` Does

```python
def _send_email(subject, html_body, text_body, recipients):
    api_key = os.getenv('BREVO_API_KEY')
    
    if api_key:
        # ── Brevo API path ──
        print(f"[DEBUG] BREVO_API_KEY found: {api_key[:15]}...{api_key[-6:]}")
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': api_key,
                'Content-Type': 'application/json'
            },
            json={
                'sender': {'email': 'astucounselplatform@gmail.com', 'name': 'ASTU Counselling'},
                'to': [{'email': recipient} for recipient in recipients],
                'subject': subject,
                'htmlContent': html_body,
                'textContent': text_body
            },
            timeout=10
        )
        
        if response.ok:
            print(f"[Email] ✅ Sent '{subject}' to {len(recipients)} recipient(s) via Brevo.")
        else:
            print(f"[Email] ❌ Brevo API Error {response.status_code}: {response.text}")
            # Falls back to SMTP if Brevo fails
    else:
        # Falls back to SMTP if no Brevo key
        _send_email_smtp(subject, html_body, text_body, recipients)
```

## Expected Logs After Fix

### When Admin Requests Assignment

```
[REQUEST] Attempting to send assignment request email to owners...
[REQUEST] Found 1 eligible owners
[REQUEST] Sending to owner: owner (astucounselplatform@gmail.com)
[REQUEST] Email subject: New Assignment Request - Case #123
[DEBUG] BREVO_API_KEY found: xkeysib-abc123...xyz789
[DEBUG] Recipients: ['astucounselplatform@gmail.com']
[DEBUG] Sending request to Brevo API...
[DEBUG] Brevo API response status: 201
[Email] ✅ Sent 'New Assignment Request - Case #123' to 1 recipient(s) via Brevo.
[REQUEST] ✅ Assignment request email sent to owner: astucounselplatform@gmail.com
```

### When Owner Approves

```
[APPROVE] Assignment request ID: 13
[APPROVE] Current status: pending
[APPROVE] ✅ Case assigned to admin1
[APPROVE] Attempting to send email notification...
[APPROVE] Admin: admin1, Email: matiwosteferi51@gmail.com
[APPROVE] Email verified: True, Notifications enabled: True
[APPROVE] Frontend URL: https://your-domain.com
[APPROVE] Email subject: Assignment Request Approved - Case #123
[DEBUG] BREVO_API_KEY found: xkeysib-abc123...xyz789
[DEBUG] Recipients: ['matiwosteferi51@gmail.com']
[DEBUG] Sending request to Brevo API...
[DEBUG] Brevo API response status: 201
[Email] ✅ Sent 'Assignment Request Approved - Case #123' to 1 recipient(s) via Brevo.
[APPROVE] ✅ Assignment approval email sent to admin: matiwosteferi51@gmail.com
```

### When Owner Rejects

```
[REJECT] Assignment request ID: 14
[REJECT] Current status: pending
[REJECT] ✅ Request rejected
[REJECT] Attempting to send email notification...
[REJECT] Admin: admin1, Email: matiwosteferi51@gmail.com
[REJECT] Email verified: True, Notifications enabled: True
[DEBUG] BREVO_API_KEY found: xkeysib-abc123...xyz789
[DEBUG] Recipients: ['matiwosteferi51@gmail.com']
[DEBUG] Sending request to Brevo API...
[DEBUG] Brevo API response status: 201
[Email] ✅ Sent 'Assignment Request Rejected - Case #123' to 1 recipient(s) via Brevo.
[REJECT] ✅ Assignment rejection email sent to admin: matiwosteferi51@gmail.com
```

## Verification Checklist

After deployment, verify these logs appear:

- [ ] See `[DEBUG] BREVO_API_KEY found:` in logs
- [ ] See `[DEBUG] Sending request to Brevo API...` in logs
- [ ] See `[DEBUG] Brevo API response status: 201` (201 = success)
- [ ] See `[Email] ✅ Sent '...' to X recipient(s) via Brevo.` in logs
- [ ] **Actually receive emails** at `astucounselplatform@gmail.com` and `matiwosteferi51@gmail.com`

## Brevo Dashboard Check

1. Go to https://app.brevo.com/
2. Navigate to **Statistics** → **Email**
3. Check **Sent emails** - should see assignment request/approve/reject emails
4. If emails show as "Delivered" but not received → Check spam folder
5. If emails show as "Bounced" or "Blocked" → Check sender verification

## Common Brevo Issues

### Issue 1: Sender Not Verified
**Error**: `Brevo API Error 400: Sender email not verified`

**Solution**:
1. Go to Brevo → Settings → Senders
2. Add `astucounselplatform@gmail.com` as verified sender
3. Verify via email link Brevo sends

### Issue 2: Invalid API Key
**Error**: `Brevo API Error 401: Unauthorized`

**Solution**:
1. Go to Brevo → SMTP & API → API Keys
2. Create a new API key (v3)
3. Update `BREVO_API_KEY` in Render environment variables
4. Redeploy

### Issue 3: Rate Limit Exceeded
**Error**: `Brevo API Error 429: Too many requests`

**Solution**:
- Wait a few minutes and try again
- Brevo free tier has daily sending limits
- Upgrade plan if hitting limits regularly

## Testing the Fix

### Test 1: Admin Requests Assignment
1. Log in as admin (`matiwosteferi51@gmail.com`)
2. Find an open case
3. Click "Request Assignment"
4. **Check Render logs** for Brevo API call
5. **Check owner email** (`astucounselplatform@gmail.com`) - should receive email

### Test 2: Owner Approves Request
1. Log in as owner (`astucounselplatform@gmail.com`)
2. Go to Owner Dashboard
3. Find pending request in "🔔 Assignment Requests"
4. Click "Approve"
5. **Check Render logs** for Brevo API call
6. **Check admin email** (`matiwosteferi51@gmail.com`) - should receive approval email

### Test 3: Owner Rejects Request
1. Log in as owner
2. Find pending request
3. Click "Reject"
4. **Check Render logs** for Brevo API call
5. **Check admin email** (`matiwosteferi51@gmail.com`) - should receive rejection email

## Summary

**Before Fix**: Assignment emails used `send_mail()` → Logged to console only → Never sent ❌

**After Fix**: Assignment emails use `_send_email()` → Sent via Brevo API → Actually delivered ✅

This matches the pattern used by working features (new case, case closed, internal messages).

Deploy the updated `backend/counselling/views.py` and the emails will start working immediately!
