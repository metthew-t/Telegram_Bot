"""
Formal HTML email templates for the Counselling Platform.
Each renderer returns (subject: str, html_body: str, text_body: str).
"""

# ─── Shared Styles & Layout ────────────────────────────────────────────────────

_BASE_STYLES = """
  body { margin: 0; padding: 0; background-color: #0f1117; font-family: 'Segoe UI', Arial, sans-serif; }
  .wrapper { background-color: #0f1117; padding: 40px 20px; }
  .container { max-width: 600px; margin: 0 auto; background-color: #1a1d27; border-radius: 12px;
               border: 1px solid #2a2d3d; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
  .header { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            padding: 32px 40px; text-align: center; }
  .header-logo { font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; margin: 0; }
  .header-sub  { font-size: 13px; color: rgba(255,255,255,0.75); margin: 4px 0 0; letter-spacing: 0.5px;
                 text-transform: uppercase; }
  .badge { display: inline-block; background: rgba(255,255,255,0.15); border-radius: 20px;
           padding: 4px 14px; font-size: 12px; color: #fff; margin-top: 10px; font-weight: 600; }
  .body { padding: 36px 40px; }
  .greeting { font-size: 22px; font-weight: 700; color: #e2e8f0; margin: 0 0 8px; }
  .intro    { font-size: 15px; color: #94a3b8; line-height: 1.6; margin: 0 0 28px; }
  .info-card { background-color: #242736; border-radius: 10px; border-left: 4px solid #4f46e5;
               padding: 20px 24px; margin-bottom: 28px; }
  .info-row  { display: flex; margin-bottom: 10px; }
  .info-row:last-child { margin-bottom: 0; }
  .info-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px;
                font-weight: 600; min-width: 110px; padding-top: 2px; }
  .info-value { font-size: 14px; color: #e2e8f0; font-weight: 500; flex: 1; line-height: 1.5; }
  .info-value.mono { font-family: monospace; background: #1a1d27; padding: 2px 8px; border-radius: 4px;
                     font-size: 13px; }
  .status-badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 12px;
                  font-weight: 600; }
  .status-open     { background: rgba(245,158,11,0.15); color: #f59e0b; }
  .status-assigned { background: rgba(79,70,229,0.15);  color: #818cf8; }
  .status-closed   { background: rgba(16,185,129,0.15); color: #10b981; }
  .cta-block { text-align: center; margin: 28px 0; }
  .cta-btn { display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed);
             color: #ffffff; text-decoration: none; padding: 14px 36px; border-radius: 8px;
             font-size: 15px; font-weight: 700; letter-spacing: 0.3px;
             box-shadow: 0 4px 14px rgba(79,70,229,0.4); }
  .cta-btn:hover { opacity: 0.9; }
  .divider { border: none; border-top: 1px solid #2a2d3d; margin: 28px 0; }
  .note { font-size: 13px; color: #64748b; line-height: 1.6; margin-bottom: 6px; }
  .footer { background-color: #13151f; padding: 24px 40px; text-align: center; }
  .footer p { font-size: 12px; color: #475569; margin: 4px 0; line-height: 1.6; }
  .footer .brand { font-weight: 700; color: #6366f1; }
  .alert-icon { font-size: 40px; text-align: center; margin-bottom: 16px; }
"""

def _html_wrap(badge_label: str, badge_color: str, body_html: str) -> str:
    """Wraps body_html in the platform email shell."""
    badge_style = f"background:rgba(255,255,255,0.15);border-radius:20px;padding:4px 14px;font-size:12px;color:#fff;margin-top:10px;font-weight:600;display:inline-block;"
    if badge_color == "green":
        badge_style = "background:rgba(16,185,129,0.2);border-radius:20px;padding:4px 14px;font-size:12px;color:#10b981;margin-top:10px;font-weight:600;display:inline-block;"
    elif badge_color == "amber":
        badge_style = "background:rgba(245,158,11,0.2);border-radius:20px;padding:4px 14px;font-size:12px;color:#f59e0b;margin-top:10px;font-weight:600;display:inline-block;"
    elif badge_color == "red":
        badge_style = "background:rgba(239,68,68,0.2);border-radius:20px;padding:4px 14px;font-size:12px;color:#ef4444;margin-top:10px;font-weight:600;display:inline-block;"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Counselling Platform</title>
  <style>{_BASE_STYLES}</style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <!-- HEADER -->
      <div class="header">
        <p class="header-logo">⚖ Counsel</p>
        <p class="header-sub">Support &amp; Case Management System</p>
        <span style="{badge_style}">{badge_label}</span>
      </div>
      <!-- BODY -->
      <div class="body">
        {body_html}
      </div>
      <!-- FOOTER -->
      <div class="footer">
        <p>This is an automated notification from the <span class="brand">Counselling Platform</span>.</p>
        <p>Please do not reply to this email. Log in to the platform to take action.</p>
        <p style="margin-top:10px;color:#334155;">© 2025 Counselling Platform. All rights reserved.</p>
      </div>
    </div>
  </div>
</body>
</html>"""


def _case_info_card(case) -> str:
    status_class = {
        'open': 'status-open',
        'assigned': 'status-assigned',
        'closed': 'status-closed',
    }.get(case.status, 'status-open')

    assigned = case.assigned_admin.username if case.assigned_admin else '—  <em style="color:#475569">Unassigned</em>'

    return f"""
    <div class="info-card">
      <div class="info-row">
        <span class="info-label">Case ID</span>
        <span class="info-value mono"># {case.id}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Title</span>
        <span class="info-value">{case.title}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Status</span>
        <span class="info-value"><span class="status-badge {status_class}">{case.status.capitalize()}</span></span>
      </div>
      <div class="info-row">
        <span class="info-label">Submitted by</span>
        <span class="info-value">{case.user.username}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Assigned to</span>
        <span class="info-value">{assigned}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Created</span>
        <span class="info-value">{case.created_at.strftime('%d %B %Y, %H:%M UTC')}</span>
      </div>
    </div>"""


def _cta_button(label: str, url: str) -> str:
    return f"""
    <div class="cta-block">
      <a href="{url}" class="cta-btn">{label}</a>
    </div>
    <p class="note" style="text-align:center;">
      Or copy this link: <a href="{url}" style="color:#818cf8;">{url}</a>
    </p>"""


# ─── Template: Email Verification ─────────────────────────────────────────────

def render_verification_email(user, verification_link: str):
    subject = "✉ Please verify your email — Counselling Platform"

    body_html = f"""
    <div class="alert-icon">✉️</div>
    <h2 class="greeting">Welcome, {user.username}!</h2>
    <p class="intro">
      Thank you for registering as support staff on the <strong style="color:#818cf8;">Counselling Platform</strong>.
      Before you can receive system notifications and access your account fully, we need to verify
      your email address.
    </p>
    <p class="intro" style="margin-top:-14px;">
      Click the button below to confirm your email. This link will expire after
      <strong style="color:#f59e0b;">24 hours</strong>.
    </p>
    {_cta_button("✔ Verify My Email Address", verification_link)}
    <hr class="divider"/>
    <p class="note"><strong style="color:#94a3b8;">Why am I receiving this?</strong></p>
    <p class="note">
      An account was just created using this email address on the Counselling Platform.
      If you did not register, you can safely ignore this email — no account will be activated.
    </p>
    <p class="note" style="margin-top:10px;">
      <strong style="color:#94a3b8;">Role assigned:</strong>
      <span style="color:#818cf8;font-weight:600;">{user.role.capitalize()}</span>
    </p>"""

    text_body = f"""Welcome, {user.username}!

Please verify your email address to activate your Counselling Platform account.

Verification link:
{verification_link}

This link expires after 24 hours.
Role assigned: {user.role.capitalize()}

If you did not register, please ignore this email.
"""

    return subject, _html_wrap("Email Verification Required", "amber", body_html), text_body


# ─── Template: New Case Created ───────────────────────────────────────────────

def render_new_case_email(case, frontend_url: str):
    subject = f"🆕 New Case #{case.id} Submitted — Action Required"
    case_url = f"{frontend_url}/cases/{case.id}"

    body_html = f"""
    <div class="alert-icon">🆕</div>
    <h2 class="greeting">New Support Case Submitted</h2>
    <p class="intro">
      A new case has been submitted by a user and is awaiting assignment.
      Please review the details below and assign it to a support admin at your earliest convenience.
    </p>
    {_case_info_card(case)}
    <div class="info-card" style="border-left-color:#7c3aed;margin-top:-10px;">
      <div class="info-row">
        <span class="info-label">Description</span>
        <span class="info-value" style="font-style:italic;color:#94a3b8;">{case.description[:400]}{'…' if len(case.description) > 400 else ''}</span>
      </div>
    </div>
    {_cta_button("📂 View &amp; Assign Case", case_url)}
    <hr class="divider"/>
    <p class="note">This notification was sent to all verified administrators and the platform owner.</p>"""

    text_body = f"""New Support Case Submitted — Case #{case.id}

Title:       {case.title}
Status:      {case.status.capitalize()}
Submitted:   {case.user.username}
Created:     {case.created_at.strftime('%d %B %Y, %H:%M UTC')}

Description:
{case.description}

View the case: {case_url}
"""

    return subject, _html_wrap("🆕 New Case", "amber", body_html), text_body


# ─── Template: New Message on a Case ─────────────────────────────────────────

def render_new_message_email(case, message, actor_username: str, frontend_url: str):
    subject = f"💬 New Message on Case #{case.id} — {case.title}"
    case_url = f"{frontend_url}/cases/{case.id}"

    body_html = f"""
    <div class="alert-icon">💬</div>
    <h2 class="greeting">New Message on Case #{case.id}</h2>
    <p class="intro">
      <strong style="color:#818cf8;">{actor_username}</strong> has posted a new message on the support case below.
      Please log in to review and respond.
    </p>
    {_case_info_card(case)}
    <div class="info-card" style="border-left-color:#0ea5e9;">
      <div class="info-row">
        <span class="info-label">From</span>
        <span class="info-value"><strong>{actor_username}</strong></span>
      </div>
      <div class="info-row">
        <span class="info-label">Message</span>
        <span class="info-value" style="font-style:italic;color:#94a3b8;">{message.content[:500]}{'…' if len(message.content) > 500 else ''}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Sent at</span>
        <span class="info-value">{message.timestamp.strftime('%d %B %Y, %H:%M UTC')}</span>
      </div>
    </div>
    {_cta_button("💬 Open Conversation", case_url)}
    <hr class="divider"/>
    <p class="note">This notification was sent to all verified administrators and the platform owner.</p>"""

    text_body = f"""New Message on Case #{case.id} — {case.title}

From:    {actor_username}
At:      {message.timestamp.strftime('%d %B %Y, %H:%M UTC')}

Message:
{message.content}

View the case: {case_url}
"""

    return subject, _html_wrap("💬 New Message", "purple", body_html), text_body


# ─── Template: Case Assigned ─────────────────────────────────────────────────

def render_case_assigned_email(case, assigned_admin_username: str, performer_username: str, frontend_url: str):
    subject = f"📋 Case #{case.id} Assigned to {assigned_admin_username}"
    case_url = f"{frontend_url}/cases/{case.id}"

    body_html = f"""
    <div class="alert-icon">📋</div>
    <h2 class="greeting">Case #{case.id} Has Been Assigned</h2>
    <p class="intro">
      <strong style="color:#818cf8;">{performer_username}</strong> has assigned Case #{case.id} to
      <strong style="color:#10b981;">{assigned_admin_username}</strong>.
      The assigned admin should now take ownership and follow up with the client.
    </p>
    {_case_info_card(case)}
    {_cta_button("📋 View Assigned Case", case_url)}
    <hr class="divider"/>
    <p class="note">This notification was sent to the assigned administrator and the platform owner.</p>"""

    text_body = f"""Case Assignment Notification — Case #{case.id}

Case:      {case.title}
Assigned:  {assigned_admin_username}
By:        {performer_username}
Status:    {case.status.capitalize()}

View the case: {case_url}
"""

    return subject, _html_wrap("📋 Case Assigned", "green", body_html), text_body


# ─── Template: Case Closed ────────────────────────────────────────────────────

def render_case_closed_email(case, performer_username: str, frontend_url: str):
    subject = f"✅ Case #{case.id} Closed — {case.title}"
    case_url = f"{frontend_url}/cases/{case.id}"

    body_html = f"""
    <div class="alert-icon">✅</div>
    <h2 class="greeting">Case #{case.id} Has Been Closed</h2>
    <p class="intro">
      <strong style="color:#818cf8;">{performer_username}</strong> has marked Case #{case.id} as
      <strong style="color:#10b981;">Closed</strong>. No further action is required unless the client
      re-opens the case.
    </p>
    {_case_info_card(case)}
    {_cta_button("✅ View Closed Case", case_url)}
    <hr class="divider"/>
    <p class="note">This notification was sent to all verified administrators and the platform owner.</p>"""

    text_body = f"""Case Closed — Case #{case.id}

Title:    {case.title}
Closed by: {performer_username}
Status:   Closed

View the case: {case_url}
"""

    return subject, _html_wrap("✅ Case Closed", "green", body_html), text_body
