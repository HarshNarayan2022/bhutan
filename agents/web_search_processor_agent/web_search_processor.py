import os
from typing import Dict, List, Optional

try:
    from .web_search_agent import WebSearchAgent
except ImportError:
    from agents.web_search_processor_agent.web_search_agent import WebSearchAgent

class WebSearchProcessor:
    """
    Processes web search results using structured empathy + solution + recommendations format.
    """
    
    def __init__(self, config=None):
        self.config = config
        try:
            self.web_search_agent = WebSearchAgent()
        except Exception as e:
            print(f"⚠️ Web search agent not available: {e}")
            self.web_search_agent = None

    def process_query(self, query: str, user_context: Optional[Dict] = None) -> str:
        """
        Process query with structured empathy + solution + recommendations format.
        
        Args:
            query: User query
            user_context: User context including emotion, mental_health_status, name
            
        Returns:
            Structured response string
        """
        try:
            query_lower = query.lower()
            user_context = user_context or {}
            
            emotion = user_context.get("emotion", "neutral")
            mental_health_status = user_context.get("mental_health_status", "Unknown")
            user_name = user_context.get("name", "there")
            
            # Generate structured response based on query content
            if any(word in query_lower for word in ["depressed", "depression", "sad"]):
                empathy = f"I can hear that you're going through a really difficult time with sadness and depression, {user_name}. Those feelings can be overwhelming and exhausting, and I want you to know that what you're experiencing is completely valid."
                solution = "Depression often involves changes in brain chemistry that affect mood, energy, and motivation. Professional treatment through therapy and/or medication has proven very effective for most people experiencing depression."
                recommendations = "I strongly recommend reaching out to a mental health professional who can provide proper assessment and treatment. In the meantime, try to maintain basic self-care routines, connect with supportive people in your life, and consider contacting the National Mental Health Program at 1717 if you need immediate support."
                
            elif any(word in query_lower for word in ["anxious", "anxiety", "worried", "panic"]):
                empathy = f"I understand that anxiety can feel incredibly overwhelming and scary, {user_name}. Those racing thoughts and physical sensations are very real and can be exhausting to deal with."
                solution = "Anxiety is one of the most treatable mental health conditions. Techniques like deep breathing, grounding exercises, and cognitive behavioral therapy have strong research support for managing anxiety symptoms."
                recommendations = "Try practicing 4-7-8 breathing (inhale 4, hold 7, exhale 8), limit caffeine intake, and consider speaking with a counselor who specializes in anxiety treatment. Regular exercise and mindfulness can also significantly help."
                
            elif any(word in query_lower for word in ["stress", "overwhelm", "pressure"]):
                empathy = f"It sounds like you're dealing with a lot of stress right now, {user_name}. That pressure can really take a toll on your mental and physical well-being."
                solution = "Stress management involves both addressing the source of stress and building your capacity to handle pressure. Identifying specific stressors and developing coping strategies can make a significant difference."
                recommendations = "Try breaking down overwhelming tasks into smaller steps, practice saying no to additional commitments, and schedule regular breaks. Consider stress-reduction techniques like meditation, exercise, or talking to a therapist."
                
            elif any(word in query_lower for word in ["lonely", "alone", "isolated"]):
                empathy = f"I hear that you're feeling lonely, {user_name}. Loneliness can be very difficult to experience, and you're showing strength by reaching out."
                solution = "Loneliness is a common human experience that can be addressed through building meaningful connections and developing a support network."
                recommendations = "Consider joining community groups, volunteering, or participating in activities you enjoy. Online support groups can also provide connection. If loneliness persists, talking to a counselor can help develop strategies for building relationships."
                
            elif any(word in query_lower for word in ["sleep", "tired", "exhausted", "insomnia"]):
                empathy = f"It sounds like you're having difficulties with sleep or feeling tired, {user_name}. Sleep issues can significantly impact mental health and daily functioning."
                solution = "Sleep problems often have both physical and mental health components. Good sleep hygiene and addressing underlying stress or anxiety can improve sleep quality."
                recommendations = "Try maintaining a consistent sleep schedule, limiting screen time before bed, and creating a relaxing bedtime routine. Avoid caffeine late in the day. If sleep problems persist, consider consulting a healthcare provider."
                
            else:
                # Generic structured response
                empathy = f"Thank you for reaching out and sharing what you're going through, {user_name}. I can sense that you're dealing with some challenges right now, and I want you to know that your experience matters."
                solution = "There are evidence-based strategies and resources available that can help you manage these feelings and improve your mental health over time."
                recommendations = "Consider speaking with a mental health professional for personalized support, practice daily self-care activities, and don't hesitate to reach out to trusted friends or family members for additional support."
            
            # Combine the structured response
            structured_response = f"{empathy}\n\n{solution}\n\n{recommendations}"
            
            # Add crisis resources for severe cases
            if (mental_health_status in ["Severe", "Crisis"] or 
                any(word in query_lower for word in ["suicide", "kill myself", "want to die", "hurt myself"])):
                crisis_addition = "\n\n**🆘 Immediate Support Available:** If you're having thoughts of self-harm, please contact the National Mental Health Program at 1717 (24/7) or Emergency Services at 112 immediately."
                structured_response += crisis_addition
            
            return structured_response
            
        except Exception as e:
            print(f"[WebSearchProcessor] Error: {e}")
            return f"I'm here to support you, {user_context.get('name', 'there')}, though I'm having some technical difficulties. Please know that whatever you're going through, there are people and resources available to help. For immediate support in Bhutan, contact the National Mental Health Program at 1717."

    def process_web_results(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Legacy method for compatibility.
        """
        # Build context from chat history
        user_context = {}
        if chat_history and len(chat_history) > 0:
            # Extract user context from recent messages
            recent_messages = chat_history[-3:] if len(chat_history) > 3 else chat_history
            for msg in recent_messages:
                if msg.get("role") == "user":
                    content = msg.get('content', '').lower()
                    # Simple emotion detection
                    if any(word in content for word in ['sad', 'depressed', 'down']):
                        user_context['emotion'] = 'sad'
                    elif any(word in content for word in ['anxious', 'worried', 'panic']):
                        user_context['emotion'] = 'anxious'
                    elif any(word in content for word in ['angry', 'frustrated', 'mad']):
                        user_context['emotion'] = 'angry'
        
        return self.process_query(query, user_context)

# Convenience function for direct use
def search_mental_health_info(query: str, user_context: Optional[Dict] = None) -> str:
    """
    Direct function to search for mental health information.
    """
    processor = WebSearchProcessor()
    return processor.process_query(query, user_context)