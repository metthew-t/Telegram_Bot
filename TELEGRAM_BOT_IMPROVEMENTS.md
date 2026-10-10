# Telegram Bot Improvements - Case Switching & Reassignment Notifications

## Changes Summary

### 1. ✅ Reassignment Telegram Notifications (Backend)

**Problem**: When owner reassigns a case from one admin to another, the user receives a Telegram notification saying "Your case has been assigned to support" even though it was already assigned.

**Solution**: Modified the `assign` endpoint to detect reassignments and skip Telegram notifications.

**How it works**:
- Before assigning, check if `case.assigned_admin` is not None
- If previously assigned → This is a **reassignment** → Skip Telegram notification
- If NOT previously assigned → This is a **new assignment** → Send Telegram notification
- Audit log updated to show "reassigned" vs "assigned"

**Code Changes** (`backend/counselling/views.py`):
```python
# Check if this is a reassignment
was_previously_assigned = case.assigned_admin is not None
previous_admin = case.assigned_admin

# ... assign the case ...

# Only notify user via Telegram if this is a NEW assignment
if not was_previously_assigned:
    notify_case_user(case, f'Your case #{case.user_case_number} has been assigned to support.')
    print(f"[Assignment] ✅ User notified via Telegram (new assignment)")
else:
    print(f"[Assignment] ⏭️  Telegram notification skipped (reassignment from {previous_admin.username} to {actual_assigned_admin.username})")
```

**Behavior**:
- ✅ User creates case → Owner assigns to Admin1 → User gets Telegram notification
- ⏭️  Owner reassigns from Admin1 to Admin2 → User does NOT get notification
- ✅ Approval workflow (admin requests, owner approves) → User gets notification (always new assignment)

---

### 2. ✅ New /switchcase Command (Telegram Bot)

**Problem**: Users typing numbers (like "5" or "123") in their messages would accidentally trigger case switching, when they just wanted to include numbers in their text.

**Solution**: 
- Added explicit `/switchcase` command for case selection
- Removed automatic number-based case switching
- Numbers in messages are now treated as normal text

**How /switchcase works**:

1. User types `/switchcase`
2. Bot shows list of active cases with current selection marked:
   ```
   🔄 Switch Case
   
   You have 3 active cases:
   
   • ✓ 1: Spiritual Growth
   • 2: Academic Stress
   • 3: Family Issues
   
   Reply with the case number to switch to it.
   ```
3. User types the case number (e.g., "2")
4. Bot confirms:
   ```
   ✅ Switched to Case #2
   
   📝 Academic Stress
   📊 Status: assigned
   
   All your messages will now go to this case.
   ```

**Features**:
- Shows current selected case with ✓ mark
- Only available when user has multiple active cases
- If user has only one case, bot explains it's not needed
- Selection persists across messages
- Can switch at any time without losing context

**Code Location**: `bot/telegram_bot.py`

---

### 3. ✅ Numbers Treated as Normal Text

**Old Behavior**:
```
User: "I need help with question 5"
Bot: ✅ Case #5 selected: Some Other Case
```

**New Behavior**:
```
User: "I need help with question 5"
Bot: ✅ Sent to your case #1.
```

Numbers are now just normal text content. No special handling.

---

### 4. ✅ Improved Multiple Case Handling

**Scenario**: User has multiple active cases and hasn't selected one yet.

**Old Behavior**:
- Bot would store the message
- Ask user to type a number
- Send stored message after selection

**New Behavior**:
- Bot asks user to use `/switchcase` first
- Does NOT store or send the message
- Clearer instruction: "Use /switchcase to select which case"

**Message Example**:
```
📝 You have 3 active cases:

• Case #1: Spiritual Growth
• Case #2: Academic Stress
• Case #3: Family Issues

💡 Use /switchcase to select which case you want to reply to.

_Your message has not been sent yet._
```

---

### 5. ✅ Voice Messages

Voice messages follow the same logic:
- Single case: Sent automatically
- Multiple cases with selection: Sent to selected case
- Multiple cases without selection: User must use `/switchcase` first

---

### 6. ✅ Updated Help Command

Added `/switchcase` to the help menu:

```
/start — Register & get started
/newcase — Submit a new support case
/mycases — List all your cases
/viewcase — View messages on a case
/reply — Reply to a case
/switchcase — Switch to a different active case  ← NEW!
/help — Show this help message
/cancel — Cancel current operation

💡 Tip: If you have one active case, just type your messages 
normally and they'll be sent to that case!
```

---

## Testing Scenarios

### Test 1: Reassignment (No Notification)
1. Owner assigns Case #1 to Admin1
2. ✅ User receives Telegram: "Your case #1 has been assigned to support"
3. Owner reassigns Case #1 to Admin2
4. ⏭️  User does NOT receive Telegram notification

### Test 2: New Assignment (Notification)
1. User creates new case
2. Owner assigns to Admin1
3. ✅ User receives Telegram: "Your case #2 has been assigned to support"

### Test 3: Approval Workflow (Notification)
1. User creates case (status: open)
2. Admin requests assignment
3. Owner approves
4. ✅ User receives Telegram: "Your case #3 has been assigned to support"

### Test 4: Numbers in Messages
1. User has Case #1 selected
2. User types: "Can you help with problem 5 and 7?"
3. ✅ Message sent to Case #1 with content including "5 and 7"
4. Numbers NOT interpreted as case switch

### Test 5: /switchcase Command
1. User has 3 active cases
2. User types `/switchcase`
3. ✅ Bot shows list with current selection marked
4. User types "2"
5. ✅ Bot confirms switch to Case #2
6. User types a message
7. ✅ Message sent to Case #2

### Test 6: Single Case (No Switch Needed)
1. User has only 1 active case
2. User types any message
3. ✅ Message automatically sent to that case
4. No need to select or switch

---

## Files Modified

### Backend
- `backend/counselling/views.py`
  - Modified `assign()` endpoint to detect reassignments
  - Added logging for reassignment vs new assignment
  - Skip Telegram notification on reassignments

### Telegram Bot
- `bot/telegram_bot.py`
  - Added `/switchcase` command with ConversationHandler
  - Added `switchcase_start()` function
  - Added `switchcase_select()` function
  - Removed number-based case switching from `handle_message()`
  - Updated `handle_voice()` to match text message logic
  - Updated `help_command()` to include `/switchcase`
  - Registered `switchcase_handler` in application

---

## User Benefits

1. **Clearer Communication**: No confusing notifications when cases are reassigned
2. **Safer Messaging**: Numbers in messages work normally (e.g., "help with question 5")
3. **Explicit Control**: Users explicitly choose when to switch cases
4. **Better UX**: Single case users don't need to think about switching
5. **Persistent Selection**: Once switched, stays on that case until explicitly changed

---

## Developer Notes

### Case Selection Logic

```python
# Single case
if len(cases) == 1:
    # Auto-send to that case
    
# Multiple cases
elif len(cases) > 1:
    selected_case_id = context.user_data.get('selected_case_id')
    
    if selected_case_id:
        # Send to selected case
    else:
        # Ask user to use /switchcase
```

### Reassignment Detection

```python
was_previously_assigned = case.assigned_admin is not None

if not was_previously_assigned:
    notify_case_user(...)  # Send Telegram
else:
    print("Skipping notification (reassignment)")
```

### Audit Log Enhancement

```python
AuditLog.objects.create(
    case=case,
    performer=request.user,
    action='reassigned' if was_previously_assigned else 'assigned',
    details=f'{"Reassigned" if was_previously_assigned else "Assigned"} case to {admin.username}',
)
```

---

## Deployment

These changes are ready for deployment. No database migrations needed.

After deployment:
1. Test reassignment workflow (owner reassigns case)
2. Test /switchcase command with multiple cases
3. Verify numbers in messages are treated as text
4. Check Telegram notifications (should only send on new assignments)

---

## Backward Compatibility

✅ All existing functionality preserved:
- Single case auto-routing still works
- `/reply` command still works
- `/viewcase` still works
- All other commands unchanged

🆕 New additions:
- `/switchcase` command (new)
- Reassignment detection (transparent to users)
- Better multiple-case handling (improved UX)
