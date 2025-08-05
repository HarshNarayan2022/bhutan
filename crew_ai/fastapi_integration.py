"""
FastAPI-compatible crew_ai processing function
"""
import json
from typing import Dict, Any
from crew_ai.chatbot import run_user_profile_retrieval, run_recommendations, run_crisis_check, run_condition_classification
from crew_ai.config import get_config

def process_user_input(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user input using crew_ai agents for FastAPI integration
    
    Args:
        context: Dictionary containing user message and context
        
    Returns:
        Dictionary with response, confidence, and additional data
    """
    try:
        user_message = context.get("user_message", "")
        user_name = context.get("user_name", "Guest")
        session_id = context.get("session_id", "default")
        
        # Build contextual query from available information
        contextual_parts = []
        if context.get("mental_health_status") and context.get("mental_health_status") != "Unknown":
            contextual_parts.append(f"Mental health status: {context['mental_health_status']}")
        
        if context.get("user_emotion") and context.get("user_emotion") != "neutral":
            contextual_parts.append(f"Current emotion: {context['user_emotion']}")
        
        if context.get("detailed_scores"):
            scores_summary = []
            for scale, details in context["detailed_scores"].items():
                scores_summary.append(f"{scale}: {details.get('interpretation', 'N/A')}")
            contextual_parts.append(f"Assessment results: {', '.join(scores_summary)}")
        
        if context.get("recommendations"):
            contextual_parts.append(f"Previous recommendations: {', '.join(context['recommendations'][:2])}")
        
        contextual_query = f"User says: '{user_message}'. " + " ".join(contextual_parts)
        
        # Check for crisis first
        crisis_result = run_crisis_check(contextual_query)
        is_crisis = crisis_result.get("is_crisis", False)
        
        if is_crisis:
            # Handle crisis situation
            crisis_rec = run_recommendations(
                contextual_query, 
                json.dumps({"name": user_name, "session_id": session_id}), 
                condition="Crisis", 
                answers="{}", 
                interpretation="N/A", 
                is_crisis="true"
            )
            
            return {
                "message": crisis_rec.get("recommendation", "If you're in immediate danger, please contact emergency services: 112 in Bhutan."),
                "confidence": 0.95,
                "is_crisis": True,
                "condition": "crisis",
                "recommendations": ["Seek immediate professional help", "Contact emergency services if in danger"],
                "resources": ["Emergency: 112", "Mental Health Helpline: 1717"]
            }
        
        # Normal processing - get user profile
        user_profile = {"name": user_name, "session_id": session_id}
        
        # Classify condition
        condition_result = run_condition_classification(contextual_query, json.dumps(user_profile))
        condition = condition_result.get("condition", "general").split(" ")[0].lower()
        
        # Get recommendations
        final_rec = run_recommendations(
            contextual_query,
            json.dumps(user_profile),
            condition,
            json.dumps(context.get("detailed_scores", {})),
            context.get("mental_health_status", "Unknown"),
            is_crisis="false"
        )
        
        return {
            "message": final_rec.get("recommendation", "I'm here to support your mental health journey. How can I help you today?"),
            "confidence": 0.8,
            "is_crisis": False,
            "condition": condition,
            "recommendations": context.get("recommendations", []),
            "resources": ["Mental Health Helpline: 1717", "Emergency: 112"]
        }
        
    except Exception as e:
        print(f"Error in crew_ai processing: {e}")
        return {
            "message": "I'm here to support you. While I process your request, please know that help is always available.",
            "confidence": 0.5,
            "is_crisis": False,
            "condition": "general",
            "recommendations": ["Practice self-care", "Consider speaking with a mental health professional"],
            "resources": ["Mental Health Helpline: 1717", "Emergency: 112"]
        }
