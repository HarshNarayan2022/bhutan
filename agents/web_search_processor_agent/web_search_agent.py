from typing import Dict, List
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import both Gemini and PubMed agents
try:
    from .geminai_search import GeminiSearchAgent, PubmedSearchAgent
except ImportError:
    from agents.web_search_processor_agent.geminai_search import GeminiSearchAgent, PubmedSearchAgent

class WebSearchAgent:
    """
    Agent responsible for retrieving real-time medical information from web sources.
    Uses Gemini AI for general queries and maintains PubMed compatibility.
    """
    
    def __init__(self, config=None):
        """Initialize the web search agent."""
        # Initialize both search agents
        self.gemini_agent = GeminiSearchAgent()
        self.pubmed_search_agent = PubmedSearchAgent()  # This is actually GeminiSearchAgent too
        self.config = config
    
    def search(self, query: str) -> str:
        """
        Perform searches using Gemini AI.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results
        """
        print(f"[WebSearchAgent] Searching with Gemini for: {query}")
        
        try:
            # Use Gemini search for better results
            results = self.gemini_agent.search_mental_health(query)
            
            # Format the results
            formatted_results = self._format_gemini_results(results)
            
            return formatted_results
            
        except Exception as e:
            print(f"[WebSearchAgent] Error during search: {str(e)}")
            # Fallback to basic response
            return self._get_fallback_response(query)
    
    def _format_gemini_results(self, results: List[Dict[str, str]]) -> str:
        """Format Gemini results for display."""
        if not results:
            return "No relevant information found."
        
        # Check for error results
        if results[0].get("type") == "error":
            return results[0].get("content", "Error occurred during search")
        
        formatted_output = []
        
        for result in results:
            if result.get("type") == "ai_summary":
                # Format AI-generated content
                content = result.get("content", "")
                formatted_output.append(content)
            else:
                # Format other types of results
                title = result.get("title", "Information")
                content = result.get("content", "")
                source = result.get("source", "Unknown")
                
                formatted_output.append(f"**{title}**\n*Source: {source}*\n\n{content}")
        
        return "\n\n".join(formatted_output)
    
    def _get_fallback_response(self, query: str) -> str:
        """Provide a fallback response when search fails."""
        return f"""I apologize, but I couldn't retrieve specific information about "{query}" at this moment. 
        
Here are some general suggestions:
1. Consider consulting with a mental health professional
2. Visit reputable mental health websites like NIMH or WHO
3. Speak with your healthcare provider for personalized advice

Would you like to rephrase your question or ask about something else?"""
    
    def search_mental_health_specific(self, query: str) -> str:
        """
        Search specifically for mental health related content.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results with mental health focus
        """
        # The GeminiSearchAgent already adds mental health context
        return self.search(query)
    
    def search_with_topics(self, query: str, topics: List[str]) -> str:
        """
        Search for specific topics using Gemini.
        
        Args:
            query: Base query
            topics: List of specific topics
            
        Returns:
            Formatted results by topic
        """
        try:
            results = self.gemini_agent.search_specific_topics(query, topics)
            
            formatted = [f"**Information about {query}:**\n"]
            for topic, content in results.items():
                formatted.append(f"\n### {topic.title()}\n{content}")
            
            return "\n".join(formatted)
            
        except Exception as e:
            print(f"[WebSearchAgent] Error in topic search: {str(e)}")
            return self._get_fallback_response(query)