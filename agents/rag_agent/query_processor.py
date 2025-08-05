import logging
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

class QueryProcessor:
    """
    Processor for mental health queries with entity extraction and specialty detection.
    """
    def __init__(self, config, embedding_model):
        self.logger = logging.getLogger(__name__)
        self.embedding_model = embedding_model
        self.config = config

        # Only mental health entity patterns
        self.medical_entity_categories = {
            "mental_health": r"(stress|anxiety|depression|suicide|coping|therapy|counseling|mindfulness|panic|self[- ]harm|hopelessness|support group|resilience|burnout|well-being|mental health)",
            "symptom": r"(insomnia|mood swings|irritability|concentration issues|memory problems|appetite changes|sleep disturbances|social withdrawal|fatigue|hopelessness)",
            "treatment": r"(medication|therapy|cognitive behavioral therapy|CBT|dialectical behavior therapy|DBT|exposure therapy|medication management|psychiatric evaluation|support group|mindfulness training)",
            "diagnosis": r"(bipolar disorder|schizophrenia|post-traumatic stress disorder|PTSD|obsessive[- ]compulsive disorder|OCD|generalized anxiety disorder|GAD|major depressive disorder|MDD|panic disorder|social anxiety disorder|SAD)",
            "risk_factor": r"(genetic predisposition|family history|trauma|substance abuse|chronic illness|stressful life events|social isolation|poor coping skills|low resilience|lack of support)",
            "intervention": r"(cognitive restructuring|exposure therapy|mindfulness meditation|relaxation techniques|stress management|problem-solving skills|assertiveness training|social skills training|self-care strategies|crisis intervention)"
        }
        
        # Only mental health specialty keywords
        self.specialty_keywords = {
            "psychiatry": [
                "mental health", "depression", "anxiety", "psychiatric", "disorder",
                "schizophrenia", "bipolar", "therapy", "behavioral", "psychological",
                "stress", "counseling", "mindfulness", "panic", "self-harm", "support group",
                "resilience", "burnout", "well-being"
            ]
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query to extract metadata and intent - NOT THE FULL RAG PIPELINE."""
        try:
            # Extract medical entities
            entities = self._extract_medical_entities(query)
            
            # Determine query intent
            intent = self._determine_query_intent(query)

            # Normalize query to handle typos and variations
            normalized_query = self._normalize_query(query)
            
            # Determine medical specialty
            specialty = self._detect_specialty(query)
            
            # Create metadata/filters for retrieval
            filters = {
                'query_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'query_intent': intent,
                'medical_entities': entities,
                'specialty': specialty
            }
            
            self.logger.info(f"Processed query with filters: {filters}")
            
            return {
                'filters': filters,
                'intent': intent,
                'entities': entities,
                'expanded_query': self._expand_query(query)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return self._get_default_metadata()
        

        
    def _normalize_query(self, query: str) -> str:
        """Normalize query to handle common typos and variations."""
        import re
        
        # Convert to lowercase
        normalized = query.lower()
        
        # Fix common typos or abbreviations
        typo_corrections = {
            r'\brad\b': 'road',  # rad -> road
            r'\bdepressed\b': 'depression',
            r'\bim\b': "i'm",
            r'\bu\b': 'you',
            r'\bur\b': 'your',
        }
        
        for pattern, replacement in typo_corrections.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized

    def _expand_query(self, query: str) -> str:
        """Expand query with related terms."""
        expansions = {
            "depression": "depression mood sadness hopelessness",
            "anxiety": "anxiety worry nervousness panic",
            "stress": "stress pressure tension burnout",
            "therapy": "therapy counseling psychotherapy CBT DBT",
            "suicide": "suicide self-harm hopelessness crisis",
            "support": "support group counseling help"
        }
        expanded = query
        for term, expansion in expansions.items():
            if re.search(r"\b" + re.escape(term) + r"\b", query.lower()):
                expanded = f"{expanded} {expansion}"
        return expanded

    def _extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract categorized medical entities from text."""
        categorized_entities = {}
        for category, pattern in self.medical_entity_categories.items():
            category_pattern = re.compile(pattern, re.IGNORECASE)
            matches = set(m.group(0).lower() for m in category_pattern.finditer(text))
            if matches:
                categorized_entities[category] = list(matches)
        return categorized_entities

    def _detect_specialty(self, text: str) -> Optional[str]:
        """Detect medical specialty from text."""
        text_lower = text.lower()
        for specialty, keywords in self.specialty_keywords.items():
            for keyword in keywords:
                if re.search(r"\b" + re.escape(keyword.lower()) + r"\b", text_lower):
                    return specialty
        return None

    def _determine_query_intent(self, text: str) -> str:
        """Determine the intent of the query."""
        text_lower = text.lower()
        if re.search(r"\b(what is|define|explain|describe|meaning of)\b", text_lower):
            return "definition"
        elif re.search(r"\b(treat|therapy|medication|cure|manage|drug|prescription)\b", text_lower):
            return "treatment"
        elif re.search(r"\b(diagnose|diagnostic|symptom|sign|identify|determine)\b", text_lower):
            return "diagnosis"
        elif re.search(r"\b(prevent|preventive|avoid|risk factor|reduction)\b", text_lower):
            return "prevention"
        return "general_information"