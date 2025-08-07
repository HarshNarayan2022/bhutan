"""
Open Source Lightweight RAG System for 512MB Deployment
Uses only scikit-learn and basic NLP without external APIs
"""

import os
import json
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

# Basic imports that are always available
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class OpenSourceRAG:
    def __init__(self, documents_path: str = "knowledge", cache_path: str = "rag_cache"):
        self.documents_path = Path(documents_path)
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(exist_ok=True)
        
        # Memory-efficient storage
        self.documents = []
        self.vectorizer = None
        self.doc_vectors = None
        
        # Cache files
        self.documents_cache = self.cache_path / "documents.pkl"
        self.vectorizer_cache = self.cache_path / "vectorizer.pkl"
        self.vectors_cache = self.cache_path / "vectors.pkl"
        
        # Mental health knowledge base
        self.mental_health_responses = {
            'depression': {
                'keywords': ['sad', 'depressed', 'depression', 'down', 'hopeless', 'empty', 'worthless'],
                'response': "I understand you're going through a difficult time with feelings of sadness or depression. These feelings are valid and you're not alone. Depression is a common mental health condition that affects millions of people. It's important to know that depression is treatable. Consider reaching out to a mental health professional, such as a therapist or counselor, who can provide personalized support and treatment options. In the meantime, try to maintain a routine, get adequate sleep, eat well, and engage in activities you used to enjoy, even if they don't feel as rewarding right now."
            },
            'anxiety': {
                'keywords': ['anxious', 'anxiety', 'worried', 'panic', 'nervous', 'stress', 'fear'],
                'response': "I hear that you're experiencing anxiety or stress. These feelings are very common and there are effective ways to manage them. Anxiety can manifest in many ways - racing thoughts, physical symptoms like rapid heartbeat, or overwhelming worry. Some helpful techniques include deep breathing exercises, progressive muscle relaxation, mindfulness meditation, and regular physical activity. Grounding techniques like the 5-4-3-2-1 method (name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste) can help during anxious moments. If anxiety is significantly impacting your daily life, consider speaking with a mental health professional."
            },
            'crisis': {
                'keywords': ['suicide', 'kill myself', 'end it all', 'not worth living', 'hurt myself', 'self harm'],
                'response': "I'm very concerned about you right now. These feelings are serious, and I want you to know that help is available immediately. Please reach out to a crisis helpline: National Suicide Prevention Lifeline at 988 (US), or Crisis Text Line by texting HOME to 741741. You can also go to your nearest emergency room or call emergency services. Your life has value, and these intense feelings can change with proper support. Please don't face this alone - there are people who want to help you through this difficult time."
            },
            'therapy': {
                'keywords': ['therapy', 'therapist', 'counselor', 'counseling', 'psychologist', 'psychiatrist'],
                'response': "Seeking therapy is a positive and brave step toward better mental health. Therapy provides a safe, confidential space to explore your thoughts and feelings with a trained professional. There are many types of therapy (cognitive behavioral therapy, dialectical behavior therapy, psychodynamic therapy, etc.) and finding the right fit is important. You can find therapists through your insurance provider, community mental health centers, or online directories like Psychology Today. Many therapists also offer sliding scale fees based on income. Remember, it's okay to 'shop around' to find a therapist you feel comfortable with."
            },
            'general': {
                'keywords': ['help', 'support', 'mental health', 'feel better', 'cope'],
                'response': "I'm here to provide support and information about mental health. Taking care of your mental health is just as important as your physical health. Some general strategies for maintaining good mental health include: maintaining social connections, getting regular exercise, eating a balanced diet, getting adequate sleep, practicing stress management techniques, and engaging in activities you enjoy. If you're struggling, remember that seeking help is a sign of strength, not weakness. Mental health professionals are trained to provide the support and tools you need."
            }
        }
        
        # Load or create document index
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load cached index or create new one"""
        try:
            if (self.documents_cache.exists() and 
                self.vectorizer_cache.exists() and 
                self.vectors_cache.exists()):
                
                # Load cached data
                with open(self.documents_cache, 'rb') as f:
                    self.documents = pickle.load(f)
                with open(self.vectorizer_cache, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(self.vectors_cache, 'rb') as f:
                    self.doc_vectors = pickle.load(f)
                    
                print(f"📚 Loaded {len(self.documents)} documents from cache")
            else:
                self.create_document_index()
        except Exception as e:
            print(f"⚠️ Cache loading failed: {e}")
            self.create_document_index()
    
    def create_document_index(self):
        """Create document index from knowledge folder and mental health responses"""
        self.documents = []
        
        # Add built-in mental health knowledge
        for category, data in self.mental_health_responses.items():
            self.documents.append({
                "text": data['response'],
                "source": "Built-in Mental Health Knowledge",
                "category": category,
                "keywords": data['keywords']
            })
        
        # Load additional documents from knowledge folder if exists
        if self.documents_path.exists():
            for file_path in self.documents_path.glob("*.txt"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            # Split into manageable chunks
                            chunks = self.split_text(content, max_length=400)
                            for i, chunk in enumerate(chunks):
                                self.documents.append({
                                    "text": chunk,
                                    "source": file_path.name,
                                    "category": "general",
                                    "chunk_id": i
                                })
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        # Create TF-IDF vectors
        self.create_tfidf_vectors()
        
        # Cache the results
        self.save_cache()
        
        print(f"✅ Created RAG index with {len(self.documents)} documents")
    
    def split_text(self, text: str, max_length: int = 400) -> List[str]:
        """Split text into smaller chunks"""
        # Simple sentence-based splitting
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def create_tfidf_vectors(self):
        """Create TF-IDF vectors for documents"""
        if not self.documents:
            return
        
        # Extract text from documents
        texts = [doc["text"] for doc in self.documents]
        
        # Create TF-IDF vectorizer with memory optimization
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit features for memory
            stop_words='english',
            lowercase=True,
            token_pattern=r'\b[a-zA-Z]{2,}\b',  # Only alphabetic tokens
            max_df=0.8,  # Ignore very common terms
            min_df=1,    # Include even rare terms for mental health
            ngram_range=(1, 2)  # Include bigrams for better context
        )
        
        # Fit and transform documents
        self.doc_vectors = self.vectorizer.fit_transform(texts)
        
        print(f"🔍 Created TF-IDF vectors: {self.doc_vectors.shape}")
    
    def save_cache(self):
        """Save index to cache"""
        try:
            with open(self.documents_cache, 'wb') as f:
                pickle.dump(self.documents, f)
            with open(self.vectorizer_cache, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            with open(self.vectors_cache, 'wb') as f:
                pickle.dump(self.doc_vectors, f)
            print("💾 Cached RAG index")
        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")
    
    def preprocess_query(self, query: str) -> str:
        """Basic query preprocessing"""
        # Convert to lowercase and remove extra whitespace
        query = query.lower().strip()
        
        # Simple keyword expansion for mental health terms
        expansions = {
            'sad': 'sad depressed depression',
            'worried': 'worried anxious anxiety stress',
            'scared': 'scared fear anxiety panic',
            'angry': 'angry frustrated irritated',
            'lonely': 'lonely isolated alone',
        }
        
        for word, expansion in expansions.items():
            if word in query:
                query += f" {expansion}"
        
        return query
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if not self.documents or self.vectorizer is None or self.doc_vectors is None:
            return []
        
        try:
            # Preprocess query
            processed_query = self.preprocess_query(query)
            
            # Convert query to TF-IDF vector
            query_vector = self.vectorizer.transform([processed_query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.doc_vectors)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.05:  # Minimum similarity threshold
                    doc = self.documents[idx]
                    results.append({
                        "text": doc["text"],
                        "source": doc.get("source", "Unknown"),
                        "category": doc.get("category", "general"),
                        "similarity": float(similarities[idx]),
                        "keywords": doc.get("keywords", [])
                    })
            
            # If no good matches, try keyword matching
            if not results:
                results = self.keyword_fallback_search(query.lower())
            
            return results
        
        except Exception as e:
            print(f"⚠️ Search failed: {e}")
            return self.keyword_fallback_search(query.lower())
    
    def keyword_fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search using simple keyword matching"""
        query_lower = query.lower()
        results = []
        
        for category, data in self.mental_health_responses.items():
            for keyword in data['keywords']:
                if keyword in query_lower:
                    results.append({
                        "text": data['response'],
                        "source": "Built-in Mental Health Knowledge",
                        "category": category,
                        "similarity": 0.8,  # High confidence for keyword matches
                        "keywords": data['keywords']
                    })
                    break  # Only add once per category
        
        return results[:3]  # Return top 3
    
    def process_query(self, query: str, emotion: str = "neutral", mental_health_status: str = "Unknown", user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query using the RAG system - compatible with FastAPI interface
        
        Args:
            query: User's question/message
            emotion: User's current emotional state
            mental_health_status: User's mental health status
            user_context: Additional user context
            
        Returns:
            Dictionary with response, confidence, sources, etc.
        """
        try:
            if user_context is None:
                user_context = {}
            
            print(f"🔍 Processing query: '{query}' (emotion: {emotion})")
            
            # Check for crisis keywords first
            if self.is_crisis_query(query):
                return {
                    "response": self.mental_health_responses['crisis']['response'],
                    "confidence": 0.95,
                    "sources": ["Crisis Response Protocol"],
                    "condition": "crisis",
                    "is_crisis": True,
                    "agent": "Crisis Support"
                }
            
            # Search for relevant documents
            docs = self.search(query, top_k=3)
            
            # Generate contextual response
            response = self.generate_response(query, docs, emotion, mental_health_status)
            
            # Calculate confidence based on document relevance and keyword matching
            confidence = self.calculate_confidence(query, docs)
            
            # Extract source information
            sources = []
            for doc in docs:
                if isinstance(doc, dict) and 'source' in doc:
                    sources.append(doc['source'])
                elif isinstance(doc, str):
                    sources.append("Knowledge Base")
            
            return {
                "response": response,
                "confidence": confidence,
                "sources": sources[:3],  # Limit to top 3 sources
                "condition": self.detect_condition(query),
                "is_crisis": self.is_crisis_query(query),
                "agent": "Open Source RAG Assistant"
            }
            
        except Exception as e:
            print(f"❌ Error in process_query: {e}")
            return {
                "response": self.fallback_response(query),
                "confidence": 0.3,
                "sources": ["Fallback Response"],
                "condition": "general",
                "is_crisis": False,
                "agent": "Fallback Assistant"
            }
    
    def is_crisis_query(self, query: str) -> bool:
        """Check if query indicates a mental health crisis"""
        query_lower = query.lower()
        crisis_keywords = self.mental_health_responses['crisis']['keywords']
        return any(keyword in query_lower for keyword in crisis_keywords)
    
    def detect_condition(self, query: str) -> str:
        """Detect the primary mental health condition being discussed"""
        query_lower = query.lower()
        
        for condition, data in self.mental_health_responses.items():
            if condition == 'general':
                continue
            keywords = data.get('keywords', [])
            if any(keyword in query_lower for keyword in keywords):
                return condition
        
        return 'general'
    
    def calculate_confidence(self, query: str, docs: List[Dict]) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.7
        
        # Increase confidence if we have good document matches
        if docs and len(docs) > 0:
            base_confidence += 0.1
        
        # Increase confidence if query matches mental health keywords
        query_lower = query.lower()
        for condition_data in self.mental_health_responses.values():
            keywords = condition_data.get('keywords', [])
            if any(keyword in query_lower for keyword in keywords):
                base_confidence += 0.1
                break
        
        return min(base_confidence, 0.95)  # Cap at 95%
    
    def generate_response(self, query: str, docs: List[Dict], emotion: str = "neutral", mental_health_status: str = "Unknown") -> str:
        """
        Generate response with emotional context
        """
        # Check for specific mental health topics first
        query_lower = query.lower()
        
        # Crisis response
        if self.is_crisis_query(query):
            return self.mental_health_responses['crisis']['response']
        
        # Specific condition responses
        for condition, data in self.mental_health_responses.items():
            if condition == 'general':
                continue
            keywords = data.get('keywords', [])
            if any(keyword in query_lower for keyword in keywords):
                response = data['response']
                
                # Add emotional context if available
                if emotion and emotion != "neutral":
                    response += f"\n\nI can sense you're feeling {emotion} right now, and that's completely understandable."
                
                return response
        
        # Use document-based response if available
        if docs and len(docs) > 0:
            # Combine relevant document content
            context = "\n".join([doc.get('text', str(doc))[:200] for doc in docs[:2]])
            
            # Generate response based on context
            response = f"Based on the information I have, {context[:300]}..."
            
            # Add supportive message
            response += "\n\nRemember that everyone's journey with mental health is unique. If you're struggling, consider reaching out to a mental health professional who can provide personalized support."
            
            return response
        
        # Fallback response
        return self.fallback_response(query)

    # Add property for compatibility with FastAPI
    @property
    def ingest_knowledge_folder(self):
        """Property for compatibility with existing FastAPI code"""
        return str(self.documents_path)
    
    # Global RAG instance
    rag_system = None

def get_rag_system():
    """Get or create RAG system instance"""
    global rag_system
    if rag_system is None:
        try:
            rag_system = OpenSourceRAG()
        except Exception as e:
            print(f"⚠️ RAG system initialization failed: {e}")
            rag_system = None
    return rag_system

def search_knowledge(query: str) -> str:
    """Main function to search knowledge and generate response"""
    rag = get_rag_system()
    if not rag:
        return "I'm here to support you with your mental health concerns. Please consider reaching out to a mental health professional for personalized support."
    
    try:
        # Search for relevant documents
        docs = rag.search(query, top_k=3)
        
        # Generate response
        response = rag.generate_response(query, docs)
        
        return response
    
    except Exception as e:
        print(f"⚠️ Knowledge search failed: {e}")
        return rag.fallback_response(query) if rag else "I'm experiencing some technical difficulties, but I'm here to listen. Consider reaching out to a mental health professional for personalized support."

# Test the system if run directly
if __name__ == "__main__":
    print("🧪 Testing Open Source RAG System...")
    
    test_queries = [
        "I feel really sad and hopeless",
        "I'm having anxiety attacks",
        "I need help with therapy",
        "I can't stop worrying about everything"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        response = search_knowledge(query)
        print(f"A: {response[:200]}...")
    
    print("\n✅ RAG system test complete!")
