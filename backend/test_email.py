#!/usr/bin/env python
"""
Test script to verify Brevo email configuration
Run: python backend/test_email.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from django.conf import settings
import requests

def test_brevo_connection():
    """Test if Brevo API key and sender email are configured correctly"""
    
    print("=" * 60)
    print("BREVO EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Check API Key
    api_key = os.getenv('BREVO_API_KEY')
    if not api_key:
        print("❌ BREVO_API_KEY not found in environment variables")
        return False
    
    print(f"✅ BREVO_API_KEY found: {api_key[:15]}...{api_key[-6:]}")
    
    # Check sender email
    sender_email = settings.DEFAULT_FROM_EMAIL
    print(f"📧 Sender email: {sender_email}")
    
    # Parse sender email
    if '<' in sender_email:
        sender_name = sender_email.split('<')[0].strip()
        sender_email_only = sender_email.split('<')[1].strip('>')
        from_dict = {"email": sender_email_only, "name": sender_name}
    else:
        from_dict = {"email": sender_email}
    
    print(f"   Parsed sender: {from_dict}")
    
    # Test API connection
    print("\n🔍 Testing Brevo API connection...")
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        # Get account info
        response = requests.get(
            'https://api.brevo.com/v3/account',
            headers=headers,
            timeout=10
        )
        
        if response.ok:
            account = response.json()
            print(f"✅ Brevo API connection successful!")
            print(f"   Account: {account.get('email', 'N/A')}")
            print(f"   Plan: {account.get('plan', [{}])[0].get('type', 'N/A')}")
            
            # Check remaining credits
            if 'plan' in account and len(account['plan']) > 0:
                credits = account['plan'][0].get('credits', 0)
                print(f"   Email credits remaining: {credits}")
        else:
            print(f"❌ Brevo API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as exc:
        print(f"❌ Connection failed: {exc}")
        return False
    
    # Check senders
    print("\n📋 Checking verified senders...")
    try:
        response = requests.get(
            'https://api.brevo.com/v3/senders',
            headers=headers,
            timeout=10
        )
        
        if response.ok:
            senders = response.json().get('senders', [])
            print(f"   Found {len(senders)} verified sender(s):")
            
            sender_found = False
            for sender in senders:
                sender_email_addr = sender.get('email', '')
                is_active = sender.get('active', False)
                status = "✅ ACTIVE" if is_active else "❌ INACTIVE"
                print(f"   - {sender_email_addr} {status}")
                
                if sender_email_addr == from_dict['email']:
                    sender_found = True
            
            if not sender_found:
                print(f"\n⚠️  WARNING: Your configured sender email ({from_dict['email']}) is NOT in verified senders list!")
                print("   You need to verify this sender in your Brevo dashboard.")
                return False
            else:
                print(f"\n✅ Your sender email ({from_dict['email']}) is verified!")
                
        else:
            print(f"❌ Could not fetch senders: {response.status_code}")
            
    except Exception as exc:
        print(f"❌ Failed to check senders: {exc}")
    
    # Try sending a test email
    print("\n📧 Attempting to send test email...")
    test_recipient = input("Enter your email to receive test: ").strip()
    
    if not test_recipient:
        print("⏭️  Skipping test email send")
        return True
    
    data = {
        "sender": from_dict,
        "to": [{"email": test_recipient}],
        "subject": "🧪 Test Email from Counselling Platform",
        "htmlContent": "<html><body><h1>Test Successful!</h1><p>Your Brevo configuration is working correctly.</p></body></html>",
        "textContent": "Test Successful! Your Brevo configuration is working correctly."
    }
    
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            print(f"✅ Test email sent successfully!")
            print(f"   Message ID: {result.get('messageId', 'N/A')}")
            print(f"   Check your inbox at: {test_recipient}")
        else:
            print(f"❌ Failed to send test email: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as exc:
        print(f"❌ Failed to send test email: {exc}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED - Email configuration is correct!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_brevo_connection()
    sys.exit(0 if success else 1)
