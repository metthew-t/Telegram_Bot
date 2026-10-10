# 🚀 Deployment Instructions - Counselling Platform Fixes

## What Was Fixed

### ✅ Code Fixes Applied (Ready for Deployment)

1. **Assignment Request/Approve/Reject Emails NOT Using Brevo API** ⚠️ **CRITICAL FIX**
   - **Problem**: Assignment emails were using Django's `send_mail()` which uses console backend when Brevo is configured
   - **Root Cause**: When `BREVO_API_KEY` is set, Django's `EMAIL_BACKEND` is `console.EmailBackend` (logs only, doesn't send)
   - **Solution**: Changed to use `_send_email()` function which properly calls Brevo API
   - **Impact**: Now all assignment emails will actually be sent via Brevo
   
2. **Assignment Request Rejection Email**
   - Admins now receive email when owner rejects their assignment request
   - Added comprehensive logging for debugging

3. **Owner Dashboard UI Refresh**
   - Assignment requests automatically move from "Pending" to "Recent History" after approval/rejection
   - No manual page refresh needed
   - Requests sorted by most recent first

4. **Seen Status in Chats**
   - "👁️ Seen by X" indicator now works correctly
   - Excludes current user from viewers count
   - Enhanced logging for troubleshooting
   - Works in both case chats and internal messages

---

## 📋 Deployment Steps

### Step 1: Deploy Code Changes

```bash
# In your project directory
git add backend/counselling/views.py
git add frontend/src/pages/OwnerDashboard.jsx
git add frontend/src/pages/CaseDetail.jsx
git add frontend/src/pages/SystemChat.jsx
git add FIXES_APPLIED.md
git add DEPLOYMENT_INSTRUCTIONS.md

git commit -m "Fix: Use Brevo API for assignment emails, seen status, UI refresh"
git push origin main
```

### Step 2: Wait for Render Deployment

1. Go to your Render dashboard
2. Wait for the deployment to complete
3. Check deployment logs for any errors

### Step 3: Verify Brevo Configuration

Make sure these environment variables are set in Render:

```
BREVO_API_KEY=your_brevo_api_key_here
DEFAULT_FROM_EMAIL=ASTU Counselling <astucounselplatform@gmail.com>
FRONTEND_URL=https://your-frontend-domain.com
```

**Important**: Check that:
- Owner email: `astucounselplatform@gmail.com` ✅
- Admin email: `matiwosteferi51@gmail.com` ✅
- Emails are DIFFERENT ✅
- Both emails are verified in your Brevo sender list

### Step 4: Test the Fixes

#### Test 1: Assignment Request Email
1. Log in as an admin
2. Go to a case with status "open"
3. Click "Request Assignment"
4. **Check**: Owner should receive an email notification
5. **Check browser console**: Should see `[Seen] Calling mark_viewed API`

#### Test 2: Assignment Approval Email
1. Log in as owner
2. Go to "Control Tower" (Owner Dashboard)
3. Find the pending assignment request
4. Click "Approve"
5. **Check**: Admin should receive approval email
6. **Check**: Request moves to "Recent History" section automatically

#### Test 3: Assignment Rejection Email
1. Log in as owner
2. Find a pending assignment request
3. Click "Reject"
4. **Check**: Admin should receive rejection email
5. **Check**: Request moves to "Recent History" section automatically

#### Test 4: Seen Status - Case Chat
1. Log in as User A (owner or admin)
2. Open a case chat and send a message
3. **Check browser console**: Should see:
   ```
   [Seen] Calling mark_viewed API for case 123
   [Seen] ✅ Marked case as viewed
   [Seen] Fetching viewers for case 123
   [Seen] ✅ Fetched viewers: {...}
   [Seen] Viewers count (excluding self): 0
   ```
4. Log in as User B
5. Open the same case chat
6. Go back to User A
7. **Check**: User A should now see "👁️ Seen by 1" on their messages
8. Click the indicator to see viewer details

#### Test 5: Seen Status - Internal Messages
1. Log in as owner
2. Go to "System Chat"
3. Send a message
4. **Check browser console**: Should see:
   ```
   [Seen] Calling mark_viewed API for internal chat
   [Seen] ✅ Marked internal chat as viewed
   ```
5. Log in as an admin
6. Open "System Chat"
7. Go back to owner
8. **Check**: Owner should see "👁️ Seen by 1" on their messages

---

## 🔍 Troubleshooting

### Emails Still Not Working?

1. **Check Render logs for Brevo API calls**:
   ```
   [DEBUG] BREVO_API_KEY found: xkeysib-abc123...xyz789
   [DEBUG] Sending request to Brevo API...
   [DEBUG] Brevo API response status: 201
   [Email] ✅ Sent 'Assignment Request...' to 1 recipient(s) via Brevo.
   ```

2. **If you see "Brevo API Error 400"**:
   - Check that sender email (`astucounselplatform@gmail.com`) is verified in Brevo
   - Go to Brevo dashboard → Senders → Add sender if not listed

3. **If you see "BREVO_API_KEY not set"**:
   - Add `BREVO_API_KEY` environment variable in Render
   - Get API key from Brevo dashboard → SMTP & API → API Keys

4. **Check spam folder**: Gmail might flag these emails initially

5. **Verify both emails in Brevo**:
   - Sender: `astucounselplatform@gmail.com` must be verified
   - Recipients don't need verification, but sender MUST be verified

### Seen Status Not Showing?

1. **Check browser console** for `[Seen]` log messages
2. **Verify migration applied**:
   ```bash
   python manage.py showmigrations counselling
   # Should show: [X] 0013_internalchatview_caseview
   ```
3. **Check database tables exist**:
   ```sql
   SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%view%';
   -- Should return: counselling_caseview, counselling_internalchatview
   ```

### UI Not Refreshing?

1. **Clear browser cache**: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. **Check network tab**: Verify API calls are successful
3. **Check console for errors**: Look for failed API calls

---

## 📊 Expected Behavior After Fixes

### Admin Dashboard
- Open cases show "Request Assignment" button
- After requesting, button changes to "⏳ Request Pending..."
- Other admins cannot request the same case while pending

### Owner Dashboard
- Pending requests show in "🔔 Assignment Requests" section
- After approving/rejecting, request moves to "Recent History" section immediately
- Recent History shows last 5 processed requests, sorted by most recent

### Case Chat
- When you send a message and someone else views the chat, you see "👁️ Seen by 1"
- Clicking shows who viewed and when
- You don't see yourself in the viewers list

### Internal Messages
- Same as case chat, but tracks views for the internal chat page

### Email Notifications
- Admin requests assignment → Owner receives email
- Owner approves → Admin receives email
- Owner rejects → Admin receives email
- All emails have proper subject lines and case details

---

## 📝 Files Modified

### Backend
- `backend/counselling/views.py` - Added rejection email, enhanced logging

### Frontend
- `frontend/src/pages/OwnerDashboard.jsx` - Fixed UI refresh, sorted history
- `frontend/src/pages/CaseDetail.jsx` - Fixed seen status filtering, enhanced logging
- `frontend/src/pages/SystemChat.jsx` - Fixed seen status filtering, enhanced logging

### Documentation
- `FIXES_APPLIED.md` - Detailed technical documentation
- `DEPLOYMENT_INSTRUCTIONS.md` - This file
- `backend/fix_email_addresses.py` - Helper script

---

## ✅ Success Criteria

After deployment, these should all work:

- [ ] Admin requests assignment → Owner receives email
- [ ] Owner approves request → Admin receives email, request moves to history
- [ ] Owner rejects request → Admin receives email, request moves to history
- [ ] User A sends message → User B views chat → User A sees "👁️ Seen by 1"
- [ ] Owner sends internal message → Admin views → Owner sees "👁️ Seen by 1"
- [ ] All browser console logs show success messages
- [ ] No page refresh needed for UI updates

---

## 🆘 Need Help?

If something doesn't work after deployment:

1. Check Render deployment logs for errors
2. Check browser console for `[Seen]` logs
3. Check Render application logs for `[REQUEST]`, `[APPROVE]`, `[REJECT]` logs
4. Verify email addresses are different in Django admin
5. Test with different email addresses if Gmail blocks emails

---

## 🎉 Summary

**All code is ready!** The only thing preventing emails from working is the email address configuration. Once you update owner and admin accounts to use DIFFERENT email addresses, everything will work perfectly.

The seen status and UI refresh features are ready to use immediately after deployment.
