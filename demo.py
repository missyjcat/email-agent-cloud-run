#!/usr/bin/env python3
"""
Demo script for the Email Triage Agent
Shows different types of emails and their triage results
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def print_separator(title):
    """Print a formatted separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def demo_fyi_email():
    """Demonstrate an email that should be marked as FYI."""
    print_separator("FYI Email Demo")
    
    email_data = {
        "author": "hr@company.com",
        "to": "all@company.com",
        "subject": "Company Holiday Schedule Update",
        "email_thread": """
        Dear Team,
        
        Please note that the company will be closed on the following dates:
        - December 25th (Christmas)
        - December 26th (Boxing Day)
        - January 1st (New Year's Day)
        
        All employees are encouraged to take these days off.
        
        Best regards,
        HR Department
        """
    }
    
    print("Sending FYI email...")
    print(f"Subject: {email_data['subject']}")
    print(f"From: {email_data['author']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Triage Decision: {result['triage_decision'].upper()}")
            print(f"📧 Needs Response: {result['needs_response']}")
            print(f"💬 Message: {result['message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def demo_action_email():
    """Demonstrate an email that requires a response."""
    print_separator("Action Required Email Demo")
    
    email_data = {
        "author": "client@clientcompany.com",
        "to": "sales@company.com",
        "subject": "Project Proposal Request",
        "email_thread": """
        Hi Sales Team,
        
        We're interested in your services for a new project we're planning.
        Could you please provide a detailed proposal including:
        
        1. Project timeline
        2. Cost breakdown
        3. Team composition
        4. Previous similar projects
        
        We'd like to schedule a call to discuss this further.
        
        Best regards,
        Project Manager
        """
    }
    
    print("Sending action-required email...")
    print(f"Subject: {email_data['subject']}")
    print(f"From: {email_data['author']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Full result", result)
            print(f"\n✅ Triage Decision: {result['triage_decision'].upper()}")
            print(f"📧 Needs Response: {result['needs_response']}")
            print(f"💬 Message: {result['message']}")
            
            if result.get('drafted_response'):
                print(f"\n📝 Drafted Response:")
                print(f"{'─'*50}")
                print(result['drafted_response'])
                print(f"{'─'*50}")
                
            return result.get('session_id')
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def demo_spam_email():
    """Demonstrate an email that should be discarded."""
    print_separator("Spam Email Demo")
    
    email_data = {
        "author": "noreply@spamcompany.com",
        "to": "user@company.com",
        "subject": "URGENT: Your computer has viruses!",
        "email_thread": """
        Dear User,
        
        Your computer has been infected with multiple viruses!
        Click here immediately to download our antivirus software.
        
        Limited time offer: 50% off!
        
        Don't wait, act now!
        """
    }
    
    print("Sending spam email...")
    print(f"Subject: {email_data['subject']}")
    print(f"From: {email_data['author']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Triage Decision: {result['triage_decision'].upper()}")
            print(f"📧 Needs Response: {result['needs_response']}")
            print(f"💬 Message: {result['message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def demo_response_approval(session_id):
    """Demonstrate response approval workflow."""
    if not session_id:
        print("No session ID available for approval demo")
        return
    
    print_separator("Response Approval Demo")
    print(f"Session ID: {session_id}")
    
    # Show the approval process
    print("1. User reviews the drafted response")
    print("2. User decides to approve the response")
    
    approval_data = {
        "session_id": session_id,
        "approve_email": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email_response",
            json=approval_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Approval Result: {result['triage_decision'].upper()}")
            print(f"💬 Message: {result['message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def demo_response_rejection(session_id):
    """Demonstrate response rejection workflow."""
    if not session_id:
        print("No session ID available for rejection demo")
        return
    
    print_separator("Response Rejection Demo")
    print(f"Session ID: {session_id}")
    
    # Show the rejection process
    print("1. User reviews the drafted response")
    print("2. User decides to reject and request a new draft")
    
    rejection_data = {
        "session_id": session_id,
        "approve_email": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email_response",
            json=rejection_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Rejection Result: {result['triage_decision'].upper()}")
            print(f"💬 Message: {result['message']}")
            
            if result.get('drafted_response'):
                print(f"\n📝 New Drafted Response:")
                print(f"{'─'*50}")
                print(result['drafted_response'])
                print(f"{'─'*50}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    """Run the complete demo."""
    print("🚀 Email Triage Agent Demo")
    print("This demo shows how the agent handles different types of emails")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            return
    except:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        return
    
    print("✅ Server is running and ready")
    
    # Demo different email types
    demo_fyi_email()
    demo_spam_email()
    
    # Demo action email and response workflow
    session_id = demo_action_email()
    
    if session_id:
        # Show both approval and rejection workflows
        demo_response_approval(session_id)
        
        # Note: In a real scenario, you'd need a new session for rejection
        # This is just for demonstration
        print("\nNote: For rejection demo, you would typically:")
        print("1. Send a new email to get a new session")
        print("2. Or the system would create a new session after rejection")
    
    print_separator("Demo Complete")
    print("🎉 The demo has shown:")
    print("• FYI emails (no response needed)")
    print("• Spam emails (discarded)")
    print("• Action emails (response required)")
    print("• Response approval workflow")
    print("• Response rejection workflow")

if __name__ == "__main__":
    main()
