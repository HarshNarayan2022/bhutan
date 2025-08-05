import os
from typing import List, Dict, Optional
import google.generativeai as genai

class GeminiSearchAgent:
    """
    Searches for mental health information using Google's Gemini AI.
    """
    def __init__(self):
        """Initialize the Gemini search agent."""
        # Get API key from environment or use the one from your main.py
        api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyDzBTzKt211XwMurywdk5HFCnFeeFxcRJ0")
        genai.configure(api_key=api_key)
        
        # Use gemini-1.5-flash which is currently available
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # List available models (for debugging)
        try:
            models = genai.list_models()
            print("Available models:")
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"  - {model.name}")
        except:
            pass
    
    def search_mental_health(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search for mental health information using Gemini AI.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing search results
        """
        try:
            # Enhance query for mental health context
            enhanced_query = f"""
            As a mental health information assistant, provide reliable information about: {query}
            
            Focus on:
            1. Evidence-based mental health resources
            2. Professional medical sources and recent research
            3. Practical advice and coping strategies
            4. Treatment options and therapeutic approaches
            
            Please provide specific, actionable information that would be helpful for someone seeking mental health support.
            Format the response with clear sections if applicable.
            """
            
            # Generate content
            response = self.model.generate_content(enhanced_query)
            
            # Extract the response text
            main_response = response.text if response.text else "No response generated"
            
            # Format as a list of results
            results = [{
                "title": "Mental Health Information",
                "content": main_response,
                "source": "Google Gemini AI",
                "type": "ai_summary"
            }]
            
            return results
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            return [{
                "title": "Error",
                "content": f"Error retrieving information: {str(e)}",
                "source": "Error",
                "type": "error"
            }]
    
    def search_specific_topics(self, query: str, topics: List[str]) -> Dict[str, str]:
        """
        Search for specific mental health topics.
        
        Args:
            query: Base query
            topics: List of specific topics to include
            
        Returns:
            Dictionary with topic-specific information
        """
        results = {}
        
        for topic in topics:
            specific_query = f"""
            Provide brief, evidence-based information about: {query} specifically regarding {topic}.
            Keep the response concise but informative, focusing on practical advice and current best practices.
            """
            try:
                response = self.model.generate_content(specific_query)
                content = response.text if response.text else "No information available"
                results[topic] = content
                
            except Exception as e:
                results[topic] = f"Error: {str(e)}"
        
        return results


# For backward compatibility with existing code
class PubmedSearchAgent(GeminiSearchAgent):
    """Alias for GeminiSearchAgent to maintain compatibility."""
    
    def search_pubmed(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Wrapper method to maintain compatibility with existing code.
        Redirects to Gemini search.
        """
        # Get results from Gemini
        gemini_results = self.search_mental_health(query, max_results)
        
        # Transform to expected format
        formatted_results = []
        for i, result in enumerate(gemini_results):
            formatted_results.append({
                "title": result.get("title", "Information from Gemini AI"),
                "abstract": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", ""),
                "url": "",  # No direct URL with Gemini
                "authors": "Google Gemini AI",
                "publication_date": "Current",
                "full_content": result.get("content", ""),
            })
        
        return formatted_results


# Test function
if __name__ == "__main__":
    # Test Gemini search
    agent = GeminiSearchAgent()
    
    print("\nTesting Gemini Search Agent...")
    print("-" * 60)
    
    # Test query
    query = "cognitive behavioral therapy for depression"
    results = agent.search_mental_health(query)
    
    for result in results:
        print(f"\nTitle: {result['title']}")
        print(f"Source: {result['source']}")
        print(f"Content: {result['content'][:500]}...")
    
    # Test specific topics
    print("\n" + "=" * 60)
    print("Testing specific topics...")
    topics_results = agent.search_specific_topics(
        "anxiety management",
        ["breathing exercises", "medication options", "lifestyle changes"]
    )
    
    for topic, content in topics_results.items():
        print(f"\n{topic.upper()}:")
        print(content[:300] + "...")