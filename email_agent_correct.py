from typing import Dict, Any, Optional, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import json
import os
import logging
import pprint
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state structure
class EmailState(TypedDict):
    author: str
    to: str
    subject: str
    email_thread: str
    session_id: str
    triage_decision: Optional[str]
    drafted_response: Optional[str]
    needs_human_input: bool
    messages: List[BaseMessage]
    human_approval: Optional[bool]

class EmailTriageAgent:
    def __init__(self):
        """Initialize the email triage agent with LangGraph."""
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize the memory saver for state persistence
        self.memory_saver = MemorySaver()
        
        # Build the LangGraph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph for email triage with proper interrupt handling."""
        print("HELO", flush=True)
        logger.info("Building LangGraph for email triage")
        
        # Define the nodes
        def analyze_email(state: EmailState) -> EmailState:
            """Analyze the email content and make initial triage decision."""
            prompt = f"""
            Analyze the following email and determine the appropriate action:
            
            Author: {state['author']}
            To: {state['to']}
            Subject: {state['subject']}
            Email Thread: {state['email_thread']}
            
            Determine if this email should be classified in one of the following categories:
            1. FYI (no response needed)
            2. Discard (spam/unimportant)
            3. Respond (requires action)
            
            If a response is needed, insert a line that says "professional response:" and then draft a professional response starting on the next line.
            """
            logger.info("Analyzing email content")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            state['messages'].append(AIMessage(content=response.content))
            logger.info(f"Full LLM response: {response}")
            logger.info(f"LLM content received: {response.content}...")
            
            # Parse the response to determine action
            if "Respond" in response.content.lower() or "professional response:" in response.content.lower():
                logger.info("IN THE RESPONSE BLOCK")
                state['triage_decision'] = "respond"
                state['needs_human_input'] = True
                # Extract or generate draft response
                state['drafted_response'] = self._extract_draft_response(response.content)
                self._save_draft_to_state(state['session_id'], state['drafted_response'])
            elif "fyi" in response.content.lower() or "no response" in response.content.lower():
                state['triage_decision'] = "fyi"
                state['needs_human_input'] = False
            else:
                state['triage_decision'] = "discard"
                state['needs_human_input'] = False
            
            return state
        
        def check_human_input(state: EmailState) -> EmailState:
            """Check if human input is needed and interrupt if necessary."""
            if state['needs_human_input']:
                # Interrupt the graph execution
                raise InterruptedError("Human input required for email response approval")
            return state
        
        def finalize_decision(state: EmailState) -> EmailState:
            """Finalize the triage decision."""
            if state['triage_decision'] == "respond":
                state['messages'].append(AIMessage(content="Email requires response. Draft prepared for human approval."))
            elif state['triage_decision'] == "fyi":
                state['messages'].append(AIMessage(content="Email marked as FYI. No response needed."))
            else:
                state['messages'].append(AIMessage(content="Email marked for discard."))
            
            return state
        
        def handle_human_approval(state: EmailState) -> EmailState:
            """Handle human approval/rejection of the email response."""
            if state.get('human_approval') is True:
                # Approve the response
                state['messages'].append(AIMessage(content="Email response approved and sent."))
                state['triage_decision'] = "sent"
            elif state.get('human_approval') is False:
                # Reject the response, generate new draft
                new_draft = self._generate_new_draft(state['session_id'])
                state['drafted_response'] = new_draft
                state['messages'].append(AIMessage(content="New email draft generated."))
                # Continue to need human input
                state['needs_human_input'] = True
            
            return state
        
        # Build the graph
        workflow = StateGraph(EmailState)
        
        # Add nodes
        workflow.add_node("analyze_email", analyze_email)
        workflow.add_node("check_human_input", check_human_input)
        workflow.add_node("finalize_decision", finalize_decision)
        workflow.add_node("handle_human_approval", handle_human_approval)
        
        # Set entry point
        # workflow.set_entry_point("analyze_email")
        
        # Add edges
        # workflow.add_edge(START, "analyze_email")
        workflow.add_edge("analyze_email", "check_human_input")
        workflow.add_edge("check_human_input", "finalize_decision")
        workflow.add_edge("finalize_decision", END)
        workflow.add_edge("handle_human_approval", "finalize_decision")

        def handle_human_approval_edges(state: EmailState) -> str:
            logger.info(f"Human approval: {state.get('human_approval')}")
            if state.get('human_approval') is not None:
                logger.info("Human approval is not None")
                return "handle_human_approval"
            else:
                logger.info("Human approval is None")
                return "analyze_email"
        
        # Add conditional edge for human approval
        workflow.add_conditional_edges(
            START,
            handle_human_approval_edges
        )
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    def _extract_draft_response(self, llm_response: str) -> str:
        """Extract the drafted email response from the LLM response."""
        # Simple extraction - look for response content
        lines = llm_response.split('\n')
        response_lines = []
        in_response = False
        
        for line in lines:
            logger.info(f"Processing line: {line}")
            if "response:" in line.lower() or "draft:" in line.lower():
                logger.info("FOUND RESPONSE HEADER")
                in_response = True
                continue

            if in_response:
                response_lines.append(line.strip())
                
        
        if response_lines:
            response_final = '\n'.join(response_lines)
            logger.info(f"Final response: {response_final}")
            return response_final
        else:
            # Fallback: return a generic response
            return "Thank you for your email. I will review this and get back to you shortly."
    
    def process_email(self, author: str, to: str, subject: str, email_thread: str, session_id: str) -> Dict[str, Any]:
        """Process an email through the triage agent."""
        try:
            # Create initial state
            initial_state = EmailState(
                author=author,
                to=to,
                subject=subject,
                email_thread=email_thread,
                session_id=session_id,
                triage_decision=None,
                drafted_response=None,
                needs_human_input=False,
                messages=[],
                human_approval=None
            )
            
            # Run the graph
            result = self.graph.invoke(initial_state, config={"configurable": {"thread_id": session_id}})
            logger.info(f"Graph execution completed: {result.get('triage_decision', 'unknown')}")
            
            return {
                "triage_decision": result.get("triage_decision"),
                "needs_response": result.get("triage_decision") == "respond",
                "drafted_response": result.get("drafted_response"),
                "message": "Email processed successfully"
            }
            
        except InterruptedError:
            # Graph was interrupted, need human input
            # The state is already saved by the memory saver
            return {
                "triage_decision": "respond",
                "needs_response": True,
                "drafted_response": self._get_draft_from_state(session_id),
                "message": "Email requires human approval for response"
            }
        except Exception as e:
            return {
                "triage_decision": "error",
                "needs_response": False,
                "message": f"Error processing email: {str(e)}"
            }
    
    def _save_draft_to_state(self, session_id: str, draft: str) -> Optional[str]:
        """Retrieve the draft response from the saved state."""
        logger.info(f"Saving draft to state for session ID: {session_id}")
        try:
            # Save the saved state to memory saver
            state = self.memory_saver.set({"configurable": {"thread_id": session_id}}, {"drafted_response": draft})
            logger.info(f"State saved to memory saver: {state}")
            return state
        except Exception as e:
            return {
                "triage_decision": "error",
                "needs_response": False,
                "message": f"Error saving draft to state: {str(e)}"
            }
        return None
    
    def _get_draft_from_state(self, session_id: str) -> Optional[str]:
        """Retrieve the draft response from the saved state."""

        logger.info(f"Getting draft from state for session ID: {session_id}")
        try:
            # Get the saved state from memory saver
            state = self.memory_saver.get({"configurable": {"thread_id": session_id}})
            logger.info(f"State IN MEMORY SAVER:")
            pprint.pprint(state, indent=4)
            if state and 'channel_values' in state:
                if 'drafted_response' in state['channel_values']:
                    return state['channel_values']['drafted_response']
        except:
            pass
        return None
    
    def approve_response(self, session_id: str) -> Dict[str, Any]:
        """Approve and send the email response."""
        try:
            # # Resume the graph execution with approval
            # config = {"configurable": {"thread_id": session_id}}
            
            # # Resume with the approval command
            # result = self.graph.invoke(
            #     {"human_approval": True},
            #     config=config
            # )
            
            # Logic to actually send the email
            logger.info(f"Sending faux email response for session ID: {session_id}")

            return
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error sending email: {str(e)}"
            }
    
    def reject_response(self, session_id: str) -> Dict[str, Any]:
        """Reject the current draft and generate a new one."""
        try:
            # Resume the graph execution with rejection
            config = {"configurable": {"thread_id": session_id}}
            
            # Resume with the rejection command
            result = self.graph.invoke(
                {"human_approval": False},
                config=config
            )

            logger.info(f"Result of reject response graph:")
            pprint.pprint(result, indent=4)

            new_draft = None
            
            if 'drafted_response' in result:
                new_draft = result['drafted_response']

            # # Generate a new draft
            # new_draft = self._generate_new_draft(session_id)
            
            return new_draft

            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating new draft: {str(e)}"
            }
    
    def _generate_new_draft(self, session_id: str) -> str:
        """Generate a new email draft."""
        logger.info(f"Generating new email draft for session ID: {session_id}")
        try:
            # Get the original email context from the saved state
            state = self.memory_saver.get({"configurable": {"thread_id": session_id}})
            logger.info(f"State:")
            pprint.pprint(state, indent=4)
            if state and 'channel_values' in state:
                values = state['channel_values']
                logger.info(f"Values:")
                pprint.pprint(values, indent=4)
                prompt = f"""
                Generate a new email response for:
                
                Author: {values.get('author', 'Unknown')}
                Subject: {values.get('subject', 'Unknown')}
                Email Thread: {values.get('email_thread', 'Unknown')}
                
                Make sure it is professional and appropriate.
                """
                
                response = self.llm.invoke([HumanMessage(content=prompt)])
                logger.info(f"New email draft generated: {response.content}")
                self._save_draft_to_state(session_id, response.content)
                return response.content
            else:
                return "Thank you for your email. I will review this and get back to you shortly."
            
        except:
            pass
        
        return "Thank you for your email. I will review this and get back to you shortly."
