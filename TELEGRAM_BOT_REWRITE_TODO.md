# Telegram Bot Rewrite - Remaining Tasks

## Completed ✅
1. ✅ Added `seen_by_admin_at` field to Message model
2. ✅ Created migration 0015 for the new field
3. ✅ Persistent menu keyboard with new buttons
4. ✅ Prevent multiple active cases (check before creation)
5. ✅ Removed /mycases and /switchcase commands
6. ✅ Removed "Sent to your case #ID" confirmations

## Remaining Tasks 🔄

### Task 5: Implement Read Receipts in Telegram Bot
**Location:** `bot/telegram_bot.py` - `show_case_messages()` function

**Current:** Messages are displayed without status indicators

**Need to change:**
```python
# For each message, add status indicator:
# - User's messages: Show ✓ (sent) or ✓✓ (seen by admin)
# - Admin's messages: Just display normally

for msg in messages:
    if msg['sender']['role'] == 'user':
        # Check if admin has seen it
        if msg.get('seen_by_admin_at'):
            status = '✓✓'  # Seen
        else:
            status = '✓'   # Sent
        # Display: "You: message text ✓✓"
    else:
        # Display: "Support: message text"
```

### Task 6: Mark Messages as Seen in Backend
**Location:** `backend/counselling/views.py` - CaseViewSet

**Add endpoint:**
```python
@action(detail=True, methods=['post'])
def mark_messages_seen(self, request, pk=None):
    """Mark all unseen user messages in this case as seen by admin"""
    case = self.get_object()
    
    # Only admins/owners can mark as seen
    if request.user.role not in ['admin', 'owner']:
        return Response({'error': 'Permission denied'}, status=403)
    
    # Update unseen messages
    from django.utils import timezone
    unseen_messages = Message.objects.filter(
        case=case,
        sender__role='user',
        seen_by_admin_at__isnull=True
    )
    
    count = unseen_messages.update(seen_by_admin_at=timezone.now())
    
    return Response({'marked_seen': count})
```

**Frontend:** Call this when admin opens CaseDetail page

### Task 8: Update user_case_number Usage Everywhere
**Locations to update:**

1. **bot/telegram_bot.py** - All places showing case numbers:
   - ✅ newcase_confirm (already uses user_case_number)
   - list_cases function (if still exists)
   - reply_case_id function
   - viewcase_id function  
   - reopen_case_id function
   - switchcase functions (removed)
   - show_case_messages function
   - handle_message function (already updated)
   - handle_voice function

2. **Search and replace pattern:**
   - Find: `case.get('id')` or `case['id']` when displaying to user
   - Replace with: `case.get('user_case_number', case.get('id'))`

### Task 10: Update /viewcase Command
**Location:** `bot/telegram_bot.py` - `viewcase_start()` and related functions

**Current:** Shows list of all cases

**Need to change:**
- Show user's case history with user_case_number
- List format: "Case #1: Title (Status)"
- Allow viewing any of their cases

### Task 11: Update Frontend to Display user_case_number
**Locations:**

1. **frontend/src/pages/Dashboard.jsx** - User's case list
2. **frontend/src/pages/AdminDashboard.jsx** - Admin's case list
3. **frontend/src/pages/CaseDetail.jsx** - Case detail header
4. **frontend/src/pages/AllCases.jsx** - All cases view (owner)
5. **backend/counselling/serializers.py** - Add user_case_number to serializer

**Pattern:**
- Primary display: "Case #X" (user_case_number)
- Admin/Owner view can also show: "Case #X (ID: 157)" for reference

### Task 6 (Frontend): Read Receipts in Web Interface
**Location:** `frontend/src/pages/CaseDetail.jsx`

**Need to add:**
1. Call `/api/cases/{id}/mark_messages_seen/` when page opens
2. Display message status:
   - User messages: Show ✓ or ✓✓ based on `seen_by_admin_at`
   - Admin messages: Show ✓✓ (always seen by user)

## Implementation Order
1. Task 6 (Backend) - Add mark_messages_seen endpoint
2. Task 8 - Update user_case_number everywhere in bot
3. Task 5 - Add read receipts to bot message display
4. Task 10 - Update /viewcase command
5. Task 11 - Update frontend serializers and components
6. Task 6 (Frontend) - Add read receipt display and API call

## Testing Checklist
- [ ] User can only create one active case at a time
- [ ] User cannot see database IDs, only their case numbers (1, 2, 3...)
- [ ] Messages sent without "Sent to case" confirmation
- [ ] Read receipts show ✓ for sent, ✓✓ for seen
- [ ] Persistent menu always visible
- [ ] /mycases and /switchcase removed
- [ ] /viewcase shows case history
- [ ] /reopen works with user case numbers
- [ ] Frontend shows user_case_number throughout
- [ ] Admin sees read status when they open case detail
