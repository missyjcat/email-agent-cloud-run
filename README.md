# Note from the author

This is my first attempt at vibe coding from scratch. I had just come back from a Langchain Academy Live workshop to learn about how to use LangGraph to code general purpose agents, and decided to have Cursor help me bootstrap the application but in a way that is easy to deploy to Cloud Run.

The part that is a bit tricky about it is I wanted it to be able to be almost fully stateless in Cloud Run, and use the Memory Saver LangGraph paradigm to be able to store and retrieve the state so that when triaging emails, the human-in-the-loop threads can be stored offline in your data storage of choice. I wanted to test the ergonomics of this.

I was pretty impressed with how Cursor was able to almost get a Cloud Run configuration generated for me off the bat. I was less impressed with Cursor's ability to write up the whole logic of the application in one shot. It was pretty tedious to have to troubleshoot the command flow of this graph. However! It taught me the ins and outs of LangGraph really quickly! I feel like I understand the usefulness of LangGraph Studio a lot more now too. But a lot of this was old fashioned debugging and logger statements (which I left in but should clean up)

Right now, it's pretty basic and doesn't use interrupt() or Command() features, mainly relying on the state management. But it works in Cloud Run, though I'm not sure how long because right now the state is in-memory and there is a little bit of stickiness allowing me to retrieve the state minutes after storing. 

Some TODOs:
* Store the state in an actual persistent storage
* Replace the InterruptExceptions with actual interrupt / Command() flow
* Clean up logging statements
* Make everything more programmatic when setting up (from storage to CLoud Run compute setup)


# Email Triage Agent with LangGraph and Cloud Run

This project implements an intelligent email triage system using LangGraph agents with human-in-the-loop functionality. The system analyzes incoming emails and determines whether they should be marked as FYI, discarded, or responded to, with the ability to interrupt execution for human approval when responses are needed.

## Features

- **Intelligent Email Analysis**: Uses GPT-4 to analyze email content and determine appropriate actions
- **Human-in-the-Loop**: Interrupts execution when human approval is needed for email responses
- **State Persistence**: Uses InMemorySaver to maintain conversation state across interruptions
- **FastAPI Integration**: RESTful API endpoints for email processing and approval
- **Command Pattern**: Implements resume functionality to continue interrupted workflows

## Architecture

The system consists of:

1. **LangGraph Agent**: Core email triage logic with interrupt handling
2. **FastAPI Server**: REST endpoints for email processing and human approval
3. **State Management**: InMemorySaver for persisting conversation state
4. **LLM Integration**: OpenAI GPT-4 for email analysis and response generation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd email-agent-cloud-run
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### 1. Triage Email

**POST** `/triage_email`

Analyzes an email and determines the appropriate action.

**Request Body:**
```json
{
    "author": "sender@example.com",
    "to": "recipient@example.com",
    "subject": "Meeting Request",
    "email_thread": "Hi, I'd like to schedule a meeting to discuss the project..."
}
```

**Response:**
```json
{
    "triage_decision": "respond",
    "needs_response": true,
    "drafted_response": "Thank you for your email. I'd be happy to meet...",
    "session_id": "uuid-here",
    "message": "Email requires human approval for response"
}
```

#### 2. Approve/Reject Response

**POST** `/triage_email_response`

Handles human approval or rejection of drafted email responses.

**Request Body:**
```json
{
    "session_id": "uuid-from-previous-response",
    "approve_email": true
}
```

**Response (Approval):**
```json
{
    "triage_decision": "approved",
    "needs_response": false,
    "message": "Email response has been sent successfully."
}
```

**Response (Rejection):**
```json
{
    "triage_decision": "rejected",
    "needs_response": true,
    "drafted_response": "New draft content...",
    "session_id": "same-uuid",
    "message": "New email draft generated. Please review and approve."
}
```

#### 3. Health Check

**GET** `/health`

Returns system status and number of pending sessions.

## How It Works

1. **Email Analysis**: The agent receives an email and analyzes it using GPT-4
2. **Decision Making**: Determines if the email needs a response, is FYI, or should be discarded
3. **Interruption**: If a response is needed, the graph execution is interrupted
4. **State Persistence**: The current state is saved using InMemorySaver
5. **Human Approval**: User reviews the drafted response via API
6. **Resume**: Graph execution resumes with the human decision
7. **Completion**: Final action is taken (send email, generate new draft, etc.)

## LangGraph Implementation

The system does not uses LangGraph's interrupt functionality or the Command pattern - maybe coming soon.

But it does a similar control flow thanks to the InMemorySaver and the ability to resume from threads.

I use a poor-man's version of interrupt with Exception handling, but hope to actually dig into
the interrupt semantics soon.

- **Interrupts**: When human input is needed, the graph execution is interrupted
- **State Persistence**: InMemorySaver maintains the conversation state
- **Resume**: The graph can be resumed with new input using the same thread ID
- **Conditional Edges**: Dynamic routing based on human decisions

## Example Workflow

1. Send email to `/triage_email`
2. System analyzes email and determines response is needed
3. Graph execution is interrupted, state is saved
4. User receives drafted response with session ID
5. User approves/rejects via `/triage_email_response`
6. If approved: email is sent, workflow completes
7. If rejected: new draft is generated, workflow continues

## Configuration

- **Model**: GPT-4 (configurable in `email_agent_correct.py`)
- **Temperature**: 0 (deterministic responses)
- **Memory**: InMemorySaver for state persistence
- **Port**: 8000 (configurable in `main.py`)

## Error Handling

The system handles various error scenarios:
- Invalid session IDs
- LLM API failures
- Graph execution errors
- State retrieval failures

## Development

To modify the email analysis logic:
1. Edit the `analyze_email` function in `email_agent_correct.py`
2. Modify the prompt template
3. Adjust the decision logic based on LLM response

To add new workflow steps:
1. Define new node functions
2. Add nodes to the graph
3. Configure edges and conditional routing

## Testing

Test the endpoints using curl or any HTTP client:

```bash
# Test email triage
curl -X POST "http://localhost:8000/triage_email" \
     -H "Content-Type: application/json" \
     -d '{"author":"test@example.com","to":"user@example.com","subject":"Test","email_thread":"Hello"}'

# Test response approval (use session_id from previous response)
curl -X POST "http://localhost:8000/triage_email_response" \
     -H "Content-Type: application/json" \
     -d '{"session_id":"your-session-id","approve_email":true}'
```

## Dependencies

- `langgraph`: Graph-based workflow orchestration
- `langchain`: LLM integration framework
- `langchain-openai`: OpenAI integration
- `fastapi`: Web framework for API endpoints
- `uvicorn`: ASGI server
- `pydantic`: Data validation

## License

This project is open source and available under the MIT License.
