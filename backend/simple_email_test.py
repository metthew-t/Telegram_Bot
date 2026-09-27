#!/usr/bin/env python
"""
Simple test to send email via Brevo API directly
Run this on your Render server to test if Brevo is working at all
"""
import os
import requests

def test_simple_email():
    """Send a very simple email to test Brevo"""
    
    api_key = os.getenv('BREVO_API_KEY')
    if not api_key:
        print("❌ BREVO_API_KEY not set!")
        return False
    
    print(f"✅ Found BREVO_API_KEY: {api_key[:15]}...{api_key[-6:]}")
    
    # Very simple email
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    data = {
        "sender": {
            "email": "astucounselplatform@gmail.com",
            "name": "ASTU Counsel"
        },
        "to": [
            {"email": "YOUR_TEST_EMAIL@gmail.com"}  # CHANGE THIS!
        ],
        "subject": "Test from Counselling Platform",
        "htmlContent": "<html><body><h1>Test</h1><p>This is a test email.</p></body></html>",
        "textContent": "Test - This is a test email."
    }
    
    print("📧 Sending test email...")
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.ok:
            print("✅ Email sent successfully!")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == '__main__':
    test_simple_email()
