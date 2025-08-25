#!/usr/bin/env python3
"""
Test script for the Email Triage Agent
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_email_triage():
    """Test email triage functionality."""
    print("\nTesting email triage...")
    
    # Test email data
    email_data = {
        "author": "colleague@company.com",
        "to": "user@company.com",
        "subject": "Project Update Meeting Request",
        "email_thread": """
        Hi there,
        
        I hope this email finds you well. I wanted to schedule a meeting to discuss 
        the progress on our current project. We have some important updates to share 
        and would like your input on the next steps.
        
        Would you be available for a 30-minute call sometime this week?
        
        Best regards,
        Your Colleague
        """
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Triage response status: {response.status_code}")
        result = response.json()
        print(f"Triage result: {json.dumps(result, indent=2)}")
        
        return result.get("session_id") if result.get("needs_response") else None
        
    except Exception as e:
        print(f"Email triage failed: {e}")
        return None

def test_response_approval(session_id):
    """Test response approval functionality."""
    if not session_id:
        print("No session ID available for approval test")
        return
    
    print(f"\nTesting response approval for session: {session_id}")
    
    # Test approval
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
        
        print(f"Approval response status: {response.status_code}")
        result = response.json()
        print(f"Approval result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Response approval failed: {e}")

def test_response_rejection(session_id):
    """Test response rejection functionality."""
    if not session_id:
        print("No session ID available for rejection test")
        return
    
    print(f"\nTesting response rejection for session: {session_id}")
    
    # Test rejection
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
        
        print(f"Rejection response status: {response.status_code}")
        result = response.json()
        print(f"Rejection result: {json.dumps(result, indent=2)}")
        
        # If rejection generates a new draft, we can test approval again
        if result.get("needs_response") and result.get("drafted_response"):
            print("\nNew draft generated. Testing approval of new draft...")
            time.sleep(1)  # Small delay
            test_response_approval(session_id)
        
    except Exception as e:
        print(f"Response rejection failed: {e}")

def test_fyi_email():
    """Test an email that should be marked as FYI."""
    print("\nTesting FYI email...")
    
    email_data = {
        "author": "newsletter@company.com",
        "to": "user@company.com",
        "subject": "Weekly Company Newsletter",
        "email_thread": """
        Dear Team,
        
        Here's this week's company newsletter with updates on:
        - Company events
        - Policy changes
        - Team announcements
        
        Best regards,
        HR Team
        """
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/triage_email",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"FYI email response status: {response.status_code}")
        result = response.json()
        print(f"FYI email result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"FYI email test failed: {e}")

def main():
    """Run all tests."""
    print("Starting Email Triage Agent Tests")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health():
        print("Health check failed. Make sure the server is running.")
        return
    
    # Test FYI email (should not need response)
    test_fyi_email()
    
    # Test email that needs response
    session_id = test_email_triage()
    
    if session_id:
        # Test rejection first
        test_response_rejection(session_id)
        
        # Note: After rejection, a new session would be created
        # In a real scenario, you'd get a new session ID
        
        print("\n" + "=" * 50)
        print("Tests completed!")
        print("Note: The rejection test creates a new draft, which would")
        print("typically require a new session ID in a production system.")
    else:
        print("\nNo response needed for the test email.")

if __name__ == "__main__":
    main()
