from typing import List, Dict, Any, Optional
from .web_search_processor import WebSearchProcessor

class WebSearchProcessorAgent:
    """
    Agent responsible for processing web search results with structured responses.
    """
    
    def __init__(self, config=None):
        self.web_search_processor = WebSearchProcessor(config)
    
    def process_web_search_results(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None, 
                                 user_context: Optional[Dict] = None) -> str:
        """
        Process web search results and return structured response.
        
        Args:
            query: User query
            chat_history: Previous conversation history
            user_context: User context (emotion, mental health status, etc.)
            
        Returns:
            Structured empathy + solution + recommendations response
        """
        return self.web_search_processor.process_query(query, user_context)