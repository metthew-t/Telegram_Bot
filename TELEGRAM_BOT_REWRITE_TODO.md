# Telegram Bot Rewrite - Remaining Tasks

## Completed ✅
1. ✅ Added `seen_by_admin_at` field to Message model
2. ✅ Created migration 0015 for the new field
3. ✅ Persistent menu keyboard with new buttons
4. ✅ Prevent multiple active cases (check before creation)
5. ✅ Removed /mycases and /switchcase commands
6. ✅ Removed "Sent to your case #ID" confirmations
7. ✅ Task 5: Read Receipts in Telegram Bot (`✓` sent, `✓✓` seen by admin)
8. ✅ Task 6: Mark Messages as Seen in Backend (`/api/cases/{id}/mark_messages_seen/`)
9. ✅ Task 6 (Frontend): Read Receipts and automatic mark-as-seen in CaseDetail
10. ✅ Task 8: Complete `user_case_number` usage in bot (`reply_case_id`, `viewcase_id`, `reopen_start`, `reopen_case_id`, `show_case_messages`, `legacy_message`) and backend auto-remapping in `MessageViewSet` and `CaseViewSet`
11. ✅ Task 10: `/viewcase` shows case history with `user_case_number`
12. ✅ Task 11: Frontend shows `user_case_number` across Dashboard, AdminDashboard, OwnerDashboard, AllCases, and CaseDetail

## Testing Checklist
- [x] User can only create one active case at a time
- [x] User cannot see database IDs, only their case numbers (1, 2, 3...)
- [x] Messages sent without "Sent to case" confirmation
- [x] Read receipts show ✓ for sent, ✓✓ for seen
- [x] Persistent menu always visible
- [x] /mycases and /switchcase removed
- [x] /viewcase shows case history
- [x] /reopen works with user case numbers and lists closed cases
- [x] Frontend shows user_case_number throughout
- [x] Admin sees read status when they open case detail
- [x] Backend automatically remaps `user_case_number` to DB ID for regular users to prevent 403 Forbidden
