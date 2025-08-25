from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import logging
import pprint
from email_agent_correct import EmailTriageAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Email Triage Agent", version="1.0.0")

# Initialize the email agent
email_agent = EmailTriageAgent()

# Store for pending email responses
pending_responses: Dict[str, Dict[str, Any]] = {}

class EmailRequest(BaseModel):
    author: str
    to: str
    subject: str
    email_thread: str

class EmailResponse(BaseModel):
    triage_decision: str
    needs_response: bool
    drafted_response: Optional[str] = None
    session_id: Optional[str] = None
    message: str

class EmailApprovalRequest(BaseModel):
    session_id: str
    approve_email: bool

@app.post("/triage_email", response_model=EmailResponse)
async def triage_email(email_data: EmailRequest):
    """Analyze an email and determine the triage decision."""
    logger.info(f"Processing email from {email_data.author} with subject: {email_data.subject}")
    try:
        # Generate a unique session ID for this email
        session_id = str(uuid.uuid4())
        logger.info(f"Generated session ID: {session_id}")
        
        # Process the email through the agent
        logger.info("Sending email to agent for processing...")
        result = email_agent.process_email(
            author=email_data.author,
            to=email_data.to,
            subject=email_data.subject,
            email_thread=email_data.email_thread,
            session_id=session_id
        )
        
        # Store the session for potential response approval
        if result.get("needs_response"):
            pending_responses[session_id] = {
                "email_data": email_data.dict(),
                "drafted_response": result.get("drafted_response"),
                "triage_decision": result.get("triage_decision")
            }
        
        return EmailResponse(
            triage_decision=result.get("triage_decision", "unknown"),
            needs_response=result.get("needs_response", False),
            drafted_response=result.get("drafted_response"),
            session_id=session_id if result.get("needs_response") else None,
            message=result.get("message", "Email processed successfully")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

@app.post("/triage_email_response", response_model=EmailResponse)
async def triage_email_response(approval: EmailApprovalRequest):
    """Handle user approval/rejection of drafted email response."""
    try:
        session_id = approval.session_id
        
        if session_id not in pending_responses:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = pending_responses[session_id]
        
        if approval.approve_email:
            # Approve the email - send it
            email_agent.approve_response(session_id)
            # Clean up the session
            del pending_responses[session_id]
            
            return EmailResponse(
                triage_decision="approved",
                needs_response=False,
                message="Email response has been sent successfully."
            )
        else:
            # Reject the email - generate a new draft
            logger.info(f"Rejecting email for session ID: {session_id}")
            result = email_agent.reject_response(session_id)
            
            # logger.info(f"Result:")
            # pprint.pprint(result, indent=4)

            return EmailResponse(
                triage_decision="rejected",
                needs_response=True,
                drafted_response=result,
                session_id=session_id,
                message="New email draft generated. Please review and approve."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "pending_sessions": len(pending_responses)}

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Cloud Run sets PORT)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )
