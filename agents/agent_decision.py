"""
Agent Decision System for Multi-Agent Mental Health Chatbot
Orchestrates RAG, CrewAI, and Web Search agents using LangGraph.
"""
from dotenv import load_dotenv
import json
from typing import TypedDict, List, Any, Optional, Union, Dict
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from difflib import SequenceMatcher

from agents.web_search_processor_agent import WebSearchProcessorAgent
from config.config import Config
from .shared_rag import shared_rag_instance

# Import CrewAI components
try:
    from crew_ai.chatbot import (
        run_crisis_check,
        run_condition_classification, 
        run_user_profile_retrieval,
        run_recommendations
    )
    CREWAI_AVAILABLE = True
    print("✅ CrewAI components imported successfully")
except ImportError as e:
    print(f"⚠️ CrewAI components not available: {e}")
    CREWAI_AVAILABLE = False

load_dotenv()

# Configuration
config = Config()
memory = MemorySaver()

# Simple query cache
QUERY_CACHE = {}
CACHE_SIMILARITY_THRESHOLD = 0.85

class AgentState(TypedDict):
    """State maintained across the workflow."""
    messages: List[Any]
    agent_name: Optional[str]
    current_input: Optional[Union[str, Dict]]
    output: Optional[str]
    retrieval_confidence: float
    user_context: Optional[Dict]
    # CrewAI specific state
    crisis_detected: Optional[bool]
    condition_classified: Optional[str]
    user_profile: Optional[Dict]
    crewai_used: Optional[bool]

def get_cached_response(query: str, user_context: dict) -> Optional[dict]:
    """Check for cached similar response."""
    query_lower = query.lower()
    
    for cached_query, cached_data in QUERY_CACHE.items():
        similarity = SequenceMatcher(None, query_lower, cached_query.lower()).ratio()
        if similarity >= CACHE_SIMILARITY_THRESHOLD:
            if (cached_data['emotion'] == user_context.get('emotion') and 
                cached_data['status'] == user_context.get('mental_health_status')):
                print(f"[CACHE] Found similar response (similarity: {similarity:.2f})")
                return cached_data['response']
    return None

def cache_response(query: str, user_context: dict, response: dict):
    """Cache response for future use."""
    if len(QUERY_CACHE) > 100:
        oldest_key = next(iter(QUERY_CACHE))
        del QUERY_CACHE[oldest_key]
    
    QUERY_CACHE[query] = {
        'emotion': user_context.get('emotion'),
        'status': user_context.get('mental_health_status'),
        'response': response
    }

def create_agent_graph():
    """Create and configure the LangGraph for agent orchestration."""

    def rag_agent_processor(state):
        """Process query using RAG pipeline"""
        try:
            user_query = state["current_input"]
            user_context = state.get("user_context", {})
            
            print(f"[RAG_AGENT] Processing: {user_query[:50]}...")
            print(f"[RAG_AGENT] Context - Emotion: {user_context.get('emotion', 'neutral')}, Status: {user_context.get('mental_health_status', 'Unknown')}")
            
            # Check cache first
            cached_response = get_cached_response(user_query, user_context)
            if cached_response:
                print("[RAG_AGENT] Using cached response")
                return {
                    **state,
                    "output": cached_response.get('response', ''),
                    "agent_name": "RAG_AGENT_CACHED",
                    "retrieval_confidence": cached_response.get('confidence', 0.8),
                    "crewai_used": False
                }
            
            # Get RAG instance and process query
            rag = shared_rag_instance.get_rag()
            result = rag.process_query(
                query=user_query,
                user_emotion=user_context.get('emotion', 'neutral'),
                mental_health_status=user_context.get('mental_health_status', 'Unknown'),
                user_context=user_context
            )
            
            confidence = result.get("confidence", 0.0)
            response_text = result.get("response", "I'm here to help you with your mental health concerns.")
            
            print(f"[RAG_AGENT] Confidence: {confidence}")
            print(f"[RAG_AGENT] Response: {response_text[:100]}...")
            
            # Cache the response
            cache_response(user_query, user_context, result)
            
            return {
                **state,
                "output": response_text,
                "agent_name": "RAG_AGENT",
                "retrieval_confidence": confidence,
                "crewai_used": False
            }
            
        except Exception as e:
            print(f"[RAG_AGENT] Error: {e}")
            return {
                **state,
                "output": "I understand you're reaching out for support. While I'm having some technical difficulties, I want you to know that your feelings are valid and there are people who can help.",
                "agent_name": "RAG_AGENT_FALLBACK",
                "retrieval_confidence": 0.0,
                "crewai_used": False
            }

    def crewai_pipeline_processor(state: AgentState) -> AgentState:
        """Process query using CrewAI pipeline when RAG confidence is low"""
        print("[CREWAI_PIPELINE] Processing with CrewAI agents...")
        
        try:
            if not CREWAI_AVAILABLE:
                print("[CREWAI_PIPELINE] Not available, falling back to web search")
                return fallback_to_web_search(state)
            
            user_query = str(state["current_input"])
            user_context = state.get("user_context", {})
            
            print(f"[CREWAI_PIPELINE] Query: {user_query[:50]}...")
            
            # Use RAG's CrewAI integration if available
            rag = shared_rag_instance.get_rag()
            if hasattr(rag, 'process_query_with_crewai') and rag.crewai_enabled:
                print("[CREWAI_PIPELINE] Using RAG's CrewAI integration")
                
                result = rag.process_query_with_crewai(user_query, user_context)
                
                return {
                    **state,
                    "output": result.get("response", "I'm here to support you."),
                    "agent_name": result.get("agent", "CREWAI_ENHANCED_SYSTEM"),
                    "crisis_detected": result.get("is_crisis", False),
                    "condition_classified": result.get("condition", "general"),
                    "crewai_used": True,
                    "retrieval_confidence": result.get("confidence", 0.85)
                }
            else:
                print("[CREWAI_PIPELINE] Using direct CrewAI functions")
                
                # Direct CrewAI processing
                user_id = user_context.get('user_id', 'anon_user')
                
                # Crisis check
                crisis_result = run_crisis_check(user_query)
                is_crisis = crisis_result.get("is_crisis", False)
                
                if is_crisis:
                    crisis_rec = run_recommendations(
                        user_query, 
                        user_profile=json.dumps(user_context), 
                        condition="Crisis", 
                        answers="{}", 
                        interpretation="N/A", 
                        is_crisis="true"
                    )
                    
                    return {
                        **state,
                        "output": crisis_rec.get("recommendation", 
                            "🆘 Please reach out for immediate help. In Bhutan: Emergency Services (112), National Mental Health Program (1717)"),
                        "agent_name": "CREWAI_CRISIS_AGENT",
                        "crisis_detected": True,
                        "crewai_used": True,
                        "retrieval_confidence": 0.95
                    }
                
                # Normal processing
                try:
                    user_profile = run_user_profile_retrieval(user_query, user_id)
                except:
                    user_profile = {"id": user_id, "name": user_context.get('name', 'User')}
                
                try:
                    condition_result = run_condition_classification(user_query, json.dumps(user_profile))
                    condition = condition_result.get("condition", "general").lower()
                except:
                    condition = "general"
                
                final_rec = run_recommendations(
                    user_query,
                    json.dumps(user_profile),
                    condition,
                    json.dumps(user_context.get('assessment_answers', {})),
                    user_context.get('mental_health_status', 'Unknown'),
                    is_crisis="false"
                )
                
                return {
                    **state,
                    "output": final_rec.get("recommendation", 
                        f"Thank you for sharing your concerns. I'm here to support you with {condition} related issues."),
                    "agent_name": "CREWAI_ENHANCED_SYSTEM",
                    "condition_classified": condition,
                    "user_profile": user_profile,
                    "crewai_used": True,
                    "retrieval_confidence": 0.85
                }
                
        except Exception as e:
            print(f"[CREWAI_PIPELINE] Error: {e}")
            return fallback_to_web_search(state)

    def fallback_to_web_search(state: AgentState) -> AgentState:
        """Fallback to web search processor"""
        print("[WEB_SEARCH] Processing with web search agent...")
        
        try:
            query = str(state["current_input"])
            user_context = state.get("user_context", {})
            
            # Use WebSearchProcessorAgent
            web_agent = WebSearchProcessorAgent()
            response = web_agent.process_web_search_results(
                query=query,
                user_context=user_context
            )
            
            return {
                **state,
                "output": response,
                "agent_name": "WEB_SEARCH_PROCESSOR_AGENT",
                "crewai_used": False
            }
            
        except Exception as e:
            print(f"[WEB_SEARCH] Error: {e}")
            return {
                **state,
                "output": "I'm here to support you, though I'm having some technical difficulties. Please know that help is available. For immediate support in Bhutan, contact the National Mental Health Program at 1717.",
                "agent_name": "WEB_SEARCH_FALLBACK",
                "crewai_used": False
            }

    def confidence_based_routing(state: AgentState) -> str:
        """Route based on RAG confidence score."""
        min_confidence = getattr(config.rag, 'min_retrieval_confidence', 0.7)
        confidence = state.get("retrieval_confidence", 0.0)
        
        print(f"[ROUTING] Confidence: {confidence:.2f}, Threshold: {min_confidence}")
        
        if confidence < min_confidence:
            if CREWAI_AVAILABLE:
                print(f"[ROUTING] Low confidence, routing to CrewAI...")
                return "CREWAI_PIPELINE"
            else:
                print(f"[ROUTING] Low confidence, routing to Web Search...")
                return "WEB_SEARCH_PROCESSOR_AGENT"
        
        print(f"[ROUTING] High confidence, finalizing...")
        return "finalize_response"

    def finalize_response(state: AgentState) -> AgentState:
        """Finalize the response."""
        output = state.get("output", "")
        
        if output:
            messages = state.get("messages", [])
            messages.append(AIMessage(content=str(output)))
            
            agent_name = state.get("agent_name", "Unknown")
            crewai_used = state.get("crewai_used", False)
            
            print(f"[FINALIZE] Response from {agent_name}, CrewAI: {crewai_used}")
            
            return {
                **state,
                "messages": messages
            }
        
        return state

    # Create workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("RAG_AGENT", rag_agent_processor)
    workflow.add_node("CREWAI_PIPELINE", crewai_pipeline_processor)
    workflow.add_node("WEB_SEARCH_PROCESSOR_AGENT", fallback_to_web_search)
    workflow.add_node("finalize_response", finalize_response)
    
    # Define edges
    workflow.set_entry_point("RAG_AGENT")
    workflow.add_conditional_edges("RAG_AGENT", confidence_based_routing)
    workflow.add_edge("CREWAI_PIPELINE", "finalize_response")
    workflow.add_edge("WEB_SEARCH_PROCESSOR_AGENT", "finalize_response")
    workflow.add_edge("finalize_response", END)
    
    return workflow.compile(checkpointer=memory)

def init_agent_state() -> AgentState:
    """Initialize agent state with default values."""
    return {
        "messages": [],
        "agent_name": None,
        "current_input": None,
        "output": None,
        "retrieval_confidence": 0.0,
        "user_context": None,
        "crisis_detected": None,
        "condition_classified": None,
        "user_profile": None,
        "crewai_used": None
    }