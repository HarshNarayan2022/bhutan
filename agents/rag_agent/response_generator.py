# File: agents/rag_agent/response_generator.py

import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

class ResponseGenerator:
    """
    Generates structured responses with empathy, solution, and recommendations using RAG pipeline.
    """
    def __init__(self, config=None, llm=None):
        """Initialize ResponseGenerator with optional config and LLM"""
        self.logger = logging.getLogger(__name__)
        self.config = config 
        self.llm = llm
        
        # Set default values if config is provided
        if config and hasattr(config, 'rag'):
            self.max_context_length = getattr(config.rag, "max_context_length", 2048)
            self.include_sources = getattr(config.rag, "include_sources", True)
        else:
            self.max_context_length = 2048
            self.include_sources = True

    def generate_response(self, query: str, retrieved_docs: List[Any], 
                        chat_history: Optional[str] = None, 
                        user_emotion: Optional[str] = None,
                        mental_health_status: Optional[str] = None,
                        user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate structured response using RAG pipeline with guaranteed structure."""
        
        try:
            print(f"[ResponseGenerator] Processing: {query[:50]}...")
            print(f"[ResponseGenerator] Emotion: {user_emotion}, Status: {mental_health_status}")
            
            # Extract sources from documents
            sources = self._extract_sources(retrieved_docs)
            
            # Build context from retrieved documents
            context = self._build_context_from_docs(retrieved_docs)
            
            # Get user info
            emotion = user_emotion or "neutral"
            status = mental_health_status or "Unknown"
            message_count = user_context.get('message_count', 1) if user_context else 1
            
            # Try RAG-enhanced structured response first
            try:
                print("[ResponseGenerator] Generating RAG-enhanced structured response...")
                response_text = self._generate_rag_structured_response(
                    query, context, emotion, status, message_count
                )
                
                # Verify structure is present
                if self._verify_response_structure(response_text):
                    print("[ResponseGenerator] RAG response has complete structure")
                else:
                    print("[ResponseGenerator] RAG response missing structure, enhancing...")
                    response_text = self._enhance_with_guaranteed_structure(
                        response_text, query, emotion, status
                    )
                    
            except Exception as llm_error:
                print(f"[ResponseGenerator] LLM generation failed: {llm_error}")
                print("[ResponseGenerator] Using guaranteed structured fallback...")
                response_text = self._build_structured_response(query, emotion, status)
            
            confidence = self._calculate_confidence(sources)
            
            print(f"[ResponseGenerator] Final response: {response_text[:100]}...")
            
            return {
                "response": response_text,
                "sources": sources,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return self._generate_guaranteed_structure(query, user_emotion, mental_health_status, user_context)

    def _build_context_from_docs(self, retrieved_docs: List[Any]) -> str:
        """Build context from RAG pipeline retrieved documents."""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs[:3]):
            content = ""
            if hasattr(doc, 'page_content'):
                content = doc.page_content
            elif isinstance(doc, dict):
                content = doc.get('content', doc.get('page_content', ''))
            else:
                content = str(doc)
            
            if content:
                # Truncate for context window
                truncated_content = content[:400] + "..." if len(content) > 400 else content
                context_parts.append(f"[Document {i+1}]\n{truncated_content}")
        
        return "\n\n".join(context_parts) if context_parts else "No specific context available."

    def _generate_rag_structured_response(self, query: str, context: str, emotion: str, status: str, message_count: int) -> str:
        """Generate response using RAG context with structured prompt."""
        
        if not self.llm:
            # Fallback if no LLM is provided
            return self._build_structured_response(query, emotion, status)
        
        structured_prompt = f"""You are a compassionate mental health support assistant. Using the provided context, create a response with EXACTLY 3 sections:

USER QUERY: "{query}"
USER EMOTION: {emotion}
MENTAL HEALTH STATUS: {status}
MESSAGE COUNT: {message_count}

CONTEXT FROM RAG PIPELINE:
{context}

CRITICAL: Your response MUST have ALL THREE sections in this order:

1. EMPATHY/ACKNOWLEDGEMENT (Start with "I understand..." or "I hear..." or "I can see..."):
   - Acknowledge their specific feelings from the query
   - Validate their experience
   - Show understanding and support

2. SOLUTION/INFORMATION (Include words like "can help", "try", "practice", "research shows"):
   - Use the context to provide relevant information about their concern
   - Explain what might be happening or why they feel this way
   - Offer evidence-based insights or coping strategies

3. RECOMMENDATIONS (Include words like "recommend", "consider", "suggest"):
   - Give concrete next steps based on their status ({status})
   - Suggest professional help if needed
   - Provide specific actions they can take

Use the RAG context to make your response more informative and specific. Keep it 6-9 sentences total. Be warm and conversational, not clinical.

Response:"""

        try:
            response = self.llm.invoke(structured_prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"Error invoking LLM: {e}")
            return self._build_structured_response(query, emotion, status)

    def _verify_response_structure(self, response_text: str) -> bool:
        """Verify the response has all three required sections."""
        
        # Check for empathy keywords
        has_empathy = any(word in response_text.lower() for word in [
            'understand', 'hear', 'see', 'sorry', 'valid', 'difficult', 'acknowledge'
        ])
        
        # Check for solution keywords
        has_solution = any(word in response_text.lower() for word in [
            'try', 'practice', 'can help', 'technique', 'strategy', 'approach', 
            'research shows', 'studies', 'evidence'
        ])
        
        # Check for recommendation keywords
        has_recommendations = any(word in response_text.lower() for word in [
            'recommend', 'consider', 'suggest', 'professional', 'counselor', 
            'therapist', 'healthcare'
        ])
        
        print(f"[Structure Check] Empathy: {has_empathy}, Solution: {has_solution}, Recommendations: {has_recommendations}")
        
        return has_empathy and has_solution and has_recommendations

    def _enhance_with_guaranteed_structure(self, partial_response: str, query: str, emotion: str, status: str) -> str:
        """Enhance partial response to ensure complete structure."""
        
        # Analyze what's missing and add it
        has_empathy = any(word in partial_response.lower() for word in ['understand', 'hear', 'sorry', 'valid'])
        has_solution = any(word in partial_response.lower() for word in ['try', 'practice', 'can help', 'strategy'])
        has_recommendations = any(word in partial_response.lower() for word in ['recommend', 'consider', 'suggest'])
        
        enhanced_parts = []
        
        # Add empathy if missing
        if not has_empathy:
            empathy = self._generate_empathy_section(query, emotion)
            enhanced_parts.append(empathy)
        
        # Add the existing response
        enhanced_parts.append(partial_response)
        
        # Add solution if missing
        if not has_solution:
            solution = self._generate_solution_section(query, emotion)
            enhanced_parts.append(solution)
        
        # Add recommendations if missing
        if not has_recommendations:
            recommendations = self._generate_recommendations_section(query, status)
            enhanced_parts.append(recommendations)
        
        return " ".join(enhanced_parts)

    def _generate_empathy_section(self, query: str, emotion: str) -> str:
        """Generate empathy section based on query."""
        query_lower = query.lower()
        
        if "stress" in query_lower and ("school" in query_lower or "work" in query_lower):
            return "I understand that you're feeling overwhelmed by academic/work pressure, and these feelings are completely valid."
        elif "anxiety" in query_lower:
            return "I hear that anxiety is making things really challenging for you right now."
        elif "sad" in query_lower or "depressed" in query_lower:
            return "I can see that you're going through a difficult time with these heavy feelings."
        else:
            return f"I understand that you're dealing with {emotion} feelings, and I want you to know your experience is valid."

    def _generate_solution_section(self, query: str, emotion: str) -> str:
        """Generate solution section based on query."""
        query_lower = query.lower()
        
        if "stress" in query_lower and "school" in query_lower:
            return "Academic stress can be managed through time management techniques and breaking large tasks into smaller, manageable steps."
        elif "anxiety" in query_lower:
            return "Anxiety can be helped through breathing techniques and grounding exercises that activate your body's relaxation response."
        else:
            return "There are proven strategies that can help you manage these feelings and improve your well-being over time."

    # def _generate_recommendations_section(self, query: str, status: str) -> str:
    #     """Generate recommendations based on status and query."""
        
    #     if status == "Severe":
    #         return "I strongly recommend reaching out to a mental health professional immediately, and consider calling 988 if you need crisis support."
    #     elif "school" in query.lower():
    #         return "Consider speaking with a school counselor and practicing stress-reduction techniques like regular breaks and exercise."
    #     else:
    #         return "I recommend considering professional support and incorporating daily stress-reduction activities into your routine."

    def _extract_sources(self, retrieved_docs: List[Any]) -> List[Dict]:
        """Extract sources from retrieved documents."""
        sources = []
        
        for i, doc in enumerate(retrieved_docs[:3]):
            if hasattr(doc, 'page_content'):
                content = doc.page_content
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                source = metadata.get('source', f'Document {i+1}')
                score = metadata.get('score', 0.5)
            elif isinstance(doc, dict):
                content = doc.get('content', doc.get('page_content', ''))
                metadata = doc.get('metadata', {})
                source = metadata.get('source', doc.get('source', f'Document {i+1}'))
                score = doc.get('score', metadata.get('score', 0.5))
            else:
                content = str(doc)
                source = f'Document {i+1}'
                score = 0.5
            
            if content:
                sources.append({
                    "source": source,
                    "score": float(score),
                    "snippet": content[:100] + "..." if len(content) > 100 else content
                })
        
        return sources

    def _build_structured_response(self, query: str, emotion: str, status: str) -> str:
        """Build guaranteed structured response (fallback method)."""
        
        query_lower = query.lower()
        
        print(f"[StructureBuilder] Building guaranteed structure for: {query_lower[:30]}...")
        
        # 1. EMPATHY/ACKNOWLEDGMENT
        if "sad" in query_lower and ("depressed" in query_lower or "depression" in query_lower):
            empathy = "I understand you're going through a really difficult time with sadness and depression. These feelings can be overwhelming and exhausting, and I want you to know that reaching out shows real strength."
        elif "stress" in query_lower and ("school" in query_lower or "work" in query_lower):
            empathy = "I hear that you're feeling really stressed about your school/work responsibilities. Academic and work pressure can be overwhelming, and it's completely valid to feel this way."
        elif "anxiety" in query_lower or "anxious" in query_lower:
            empathy = "I understand that anxiety can feel incredibly overwhelming and scary. What you're experiencing is very real, and your struggle with this is completely valid."
        else:
            empathy = f"I hear that you're dealing with {emotion} feelings, and I want you to know that what you're experiencing is valid and understandable."
        
        # 2. SOLUTION/INFORMATION
        if "stress" in query_lower and ("school" in query_lower or "work" in query_lower):
            solution = "Academic and work stress can be managed through time management techniques, breaking large tasks into smaller steps, and practicing stress-reduction activities. Research shows that regular breaks and boundary-setting can help you regain control."
        elif "anxiety" in query_lower or "anxious" in query_lower:
            solution = "Anxiety is highly treatable through various approaches including breathing techniques, grounding exercises, and cognitive strategies. Practice deep breathing (inhale for 4, hold for 4, exhale for 6) to help activate your body's relaxation response."
        elif "sad" in query_lower and ("depressed" in query_lower or "depression" in query_lower):
            solution = "Depression involves complex brain chemistry changes that affect mood, energy, and motivation. Research shows that combining professional support with self-care practices can help improve symptoms over time."
        else:
            solution = "There are proven strategies and techniques that can help you manage these feelings and improve your overall mental well-being through consistent practice and the right support."
        
        # 3. RECOMMENDATIONS
        if status == "Severe":
            recommendations = "I strongly recommend reaching out to a mental health professional immediately for proper assessment and support. You can also call the crisis helpline at 988 if you need immediate assistance."
        elif "school" in query_lower or "work" in query_lower:
            recommendations = "Consider speaking with a counselor about stress management, practice setting boundaries with your workload, and explore stress-reduction activities like regular exercise or meditation that fit your schedule."
        else:
            recommendations = "Consider speaking with a mental health professional for personalized guidance and support. You might also try incorporating stress-reduction activities like deep breathing exercises, regular physical activity, or journaling into your routine."
        
        final_response = f"{empathy} {solution} {recommendations}"
        print(f"[StructureBuilder] Built guaranteed response with {len(final_response)} characters")
        
        return final_response

    def _calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on sources."""
        if not sources:
            return 0.4
        
        scores = [s.get('score', 0) for s in sources[:3]]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        if len(sources) >= 3 and avg_score > 0.5:
            return min(avg_score * 1.2, 1.0)
        
        return max(avg_score, 0.4)

    def _generate_guaranteed_structure(self, query: str, emotion: str, status: str, user_context: Dict) -> Dict[str, Any]:
        """Generate fallback response with guaranteed structure."""
        
        structured_response = self._build_structured_response(query, emotion or "concerned", status or "Unknown")
        
        return {
            "response": structured_response,
            "sources": [],
            "confidence": 0.4
        }