"""
Email notification system for the Counselling Platform.
Sends email notifications to admins/owners for case messages and internal messages.
"""

import os
from django.conf import settings
from .email_templates import render_new_message_email


def send_case_message_notification(case, message, sender):
    """
    Send email notification when a message is posted to a case.
    
    Rules:
    - When user sends message → notify ONLY the assigned admin (if email verified and notifications enabled)
    - When admin/owner sends message → already handled by Telegram bot (no email needed)
    
    Args:
        case: Case instance
        message: Message instance
        sender: User instance who sent the message
    """
    from .models import User
    from .views import send_email  # Use centralized email function
    
    frontend_url = os.getenv('FRONTEND_URL', 'https://astucounselbot.vercel.app')
    
    # If sender is user, notify the assigned admin
    if sender.role == 'user' and case.assigned_admin:
        admin = case.assigned_admin
        
        # Check if admin has email verified and notifications enabled
        if (admin.email and 
            admin.email_verified and 
            admin.email_notifications_enabled):
            
            try:
                subject, html_content, text_body = render_new_message_email(
                    case, 
                    message, 
                    sender.username,
                    frontend_url
                )
                
                send_email(subject, html_content, text_body, [admin.email])
                
                print(f"✅ Email notification sent to {admin.username} ({admin.email}) for case #{case.id}")
            except Exception as e:
                print(f"❌ Failed to send email to {admin.username}: {e}")
                import traceback
                traceback.print_exc()


def send_internal_message_notification(internal_message, sender):
    """
    Send email notification when a message is posted in System Chat or System Reports.
    
    Rules:
    - Notify all admins and owner (except the sender)
    - Only send to users with email verified and notifications enabled
    
    Args:
        internal_message: InternalMessage instance
        sender: User instance who sent the message
    """
    from .models import User
    from .views import send_email  # Use centralized email function
    
    frontend_url = os.getenv('FRONTEND_URL', 'https://astucounselbot.vercel.app')
    
    # Get all admins and owners except the sender
    recipients = User.objects.filter(
        role__in=['admin', 'owner']
    ).exclude(
        id=sender.id
    ).filter(
        email__isnull=False,
        email_verified=True,
        email_notifications_enabled=True
    )
    
    if not recipients.exists():
        print(f"ℹ️ No eligible recipients for internal message notification")
        return
    
    # Create email content
    message_type_label = "System Chat" if internal_message.message_type == 'chat' else "System Report"
    subject = f"💬 New {message_type_label} from {sender.username}"
    
    # Build message preview
    if internal_message.message_format == 'voice':
        content_preview = f"🎤 Voice message ({internal_message.voice_duration}s)"
    elif internal_message.message_format == 'file':
        content_preview = f"📎 File: {internal_message.file_name}\n{internal_message.content[:300]}"
    else:
        content_preview = internal_message.content[:500] + ('...' if len(internal_message.content) > 500 else '')
    
    # HTML email body
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{message_type_label} Notification</title>
  <style>
    body {{ margin: 0; padding: 0; background-color: #0f1117; font-family: 'Segoe UI', Arial, sans-serif; }}
    .container {{ max-width: 600px; margin: 40px auto; background-color: #1a1d27; border-radius: 12px;
                 border: 1px solid #2a2d3d; padding: 40px; }}
    .header {{ text-align: center; margin-bottom: 30px; }}
    .icon {{ font-size: 48px; margin-bottom: 16px; }}
    h1 {{ color: #e2e8f0; font-size: 24px; margin: 0; }}
    .badge {{ display: inline-block; background: rgba(99, 102, 241, 0.2); color: #818cf8;
              padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-top: 8px; }}
    .info-card {{ background-color: #242736; border-radius: 10px; border-left: 4px solid #6366f1;
                  padding: 20px; margin: 20px 0; }}
    .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
    .value {{ font-size: 14px; color: #e2e8f0; margin-top: 4px; line-height: 1.6; }}
    .button {{ display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed);
               color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px;
               font-weight: 700; margin: 20px 0; }}
    .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #475569; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="icon">💬</div>
      <h1>New {message_type_label}</h1>
      <span class="badge">Internal Communication</span>
    </div>
    
    <div class="info-card">
      <div class="label">From</div>
      <div class="value"><strong>{sender.username}</strong> ({sender.role.capitalize()})</div>
    </div>
    
    <div class="info-card">
      <div class="label">Message</div>
      <div class="value" style="font-style: italic; color: #94a3b8;">{content_preview}</div>
    </div>
    
    <div style="text-align: center;">
      <a href="{frontend_url}/system-chat" class="button">View {message_type_label}</a>
    </div>
    
    <div class="footer">
      <p>This notification was sent to all verified administrators and owners.</p>
      <p>You can disable notifications in your profile settings.</p>
    </div>
  </div>
</body>
</html>"""
    
    text_body = f"""New {message_type_label} from {sender.username} ({sender.role.capitalize()})

{content_preview}

View at: {frontend_url}/system-chat

---
This notification was sent to all verified administrators and owners.
You can disable notifications in your profile settings.
"""
    
    # Send to all eligible recipients
    recipient_emails = [r.email for r in recipients]
    try:
        send_email(subject, html_content, text_body, recipient_emails)
        print(f"✅ Internal message notification sent to {len(recipient_emails)} recipients")
    except Exception as e:
        print(f"❌ Failed to send internal message notifications: {e}")
        import traceback
        traceback.print_exc()
