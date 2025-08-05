import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
from datetime import datetime
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
from langchain.schema import Document  # Add this import for Document

class MedicalDocumentProcessor:
    """
    Processes ingested medical/mental health documents: chunking, embedding, and metadata enrichment.
    """
    def __init__(self, config, embedding_model):
        self.logger = logging.getLogger(__name__)
        required_attrs = ["chunk_size", "chunk_overlap", "processed_docs_dir"]
        for attr in required_attrs:
            if not hasattr(config.rag, attr):
                raise ValueError(f"Missing '{attr}' in config.rag. Please add it to config/rag.yaml.")
        
        self.embedding_model = embedding_model
        self.chunk_size = config.rag.chunk_size
        self.chunk_overlap = config.rag.chunk_overlap
        self.processed_docs_dir = Path(config.rag.processed_docs_dir)
        self.processed_docs_dir.mkdir(parents=True, exist_ok=True)
        self.chunking_strategy = getattr(config.rag, "chunking_strategy", "hybrid")
        self.logger.info(f"Using chunking strategy: {self.chunking_strategy}")

        # Add mental health-specific patterns
        self.document_type_patterns = {
            "mental_health_tip": re.compile(r"(?i)(stress|anxiety|depression|coping|therapy|mindfulness|prevention|tip|advice|support)"),
            "clinical_note": re.compile(r"(?i)(chief complaint|history of present illness|hpi|past medical history|pmh|medications|assessment|plan|review of systems|ros|physical examination|lab results|imaging|impression|followup)"),
            "patient_record": re.compile(r"(?i)(patient information|demographics|vital signs|allergies|immunizations|family history|social history|surgical history|problem list)"),
            "treatment_guidelines": re.compile(r"(?i)(recommendations|guidelines|protocols|indications|contraindications|dosage|administration|monitoring|special populations)"),
            "pharmacology": re.compile(r"(?i)(mechanism of action|pharmacokinetics|pharmacodynamics|dosing|adverse effects|warnings|interactions|storage|pregnancy considerations)"),
            "general_medical": re.compile(r"(?i)(medical|health|wellness|nutrition|exercise|lifestyle|prevention|diagnosis|treatment|symptom|condition)")}

        self.section_headers = [
            r"^(stress|anxiety|depression|coping|therapy|mindfulness|tip|advice|support)",
            r"^(chief complaint|history of present illness|hpi|past medical history|pmh|medications|assessment|plan|review of systems|ros|physical examination|lab results|imaging|impression|followup)",
            r"^(patient information|demographics|vital signs|allergies|immunizations|family history|social history|surgical history|problem list)",
            r"^(recommendations|guidelines|protocols|indications|contraindications|dosage|administration|monitoring|special populations)",
            r"^(mechanism of action|pharmacokinetics|pharmacodynamics|dosing|adverse effects|warnings|interactions|storage|pregnancy considerations)",
            r"^(medical|health|wellness|nutrition|exercise|lifestyle|prevention|diagnosis|treatment|symptom|condition)"]
        filtered_headers = [header for header in self.section_headers if header.strip()]
        self.section_pattern = re.compile(f"({'|'.join(filtered_headers)})", re.IGNORECASE)

        # Mental health entity patterns
        self.medical_entity_categories = {
            "mental_health": r"(stress|anxiety|depression|suicide|coping|therapy|counseling|mindfulness|panic|self[- ]harm|hopelessness|support group|resilience|burnout|well-being|mental health)",
            "symptom": r"(headache|fatigue|insomnia|mood swings|irritability|concentration issues|memory problems|appetite changes|sleep disturbances|social withdrawal)",
            "treatment": r"(medication|therapy|cognitive behavioral therapy|CBT|dialectical behavior therapy|DBT|exposure therapy|medication management|psychiatric evaluation|support group|mindfulness training)",
            "diagnosis": r"(bipolar disorder|schizophrenia|post-traumatic stress disorder|PTSD|obsessive[- ]compulsive disorder|OCD|generalized anxiety disorder|GAD|major depressive disorder|MDD|panic disorder|social anxiety disorder|SAD)",
            "risk_factor": r"(genetic predisposition|family history|trauma|substance abuse|chronic illness|stressful life events|social isolation|poor coping skills|low resilience|lack of support)",
            "intervention": r"(cognitive restructuring|exposure therapy|mindfulness meditation|relaxation techniques|stress management|problem-solving skills|assertiveness training|social skills training|self-care strategies|crisis intervention)"}
        all_patterns = [f"(?P<{cat}>{pat})" for cat, pat in self.medical_entity_categories.items()]
        self.medical_entity_pattern = re.compile("|".join(all_patterns), re.IGNORECASE)

    

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process and chunk documents."""
        all_chunks = []
        
        for doc in documents:
            # Get content and metadata
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # Create chunks based on strategy
            if self.chunking_strategy == "hybrid":
                chunks = self._hybrid_chunking(content, metadata)
            elif self.chunking_strategy == "semantic":
                chunks = self._semantic_chunking(content, metadata)
            else:
                chunks = self._fixed_chunking(content, metadata)
            
            # Add embeddings to chunks
            for chunk in chunks:
                if not chunk.metadata.get('embedding'):
                    embedding = self.embedding_model.encode(chunk.page_content)
                    chunk.metadata['embedding'] = embedding.tolist()
            
            all_chunks.extend(chunks)
        
        self.logger.info(f"Processed {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks

    def _detect_document_type(self, text: str) -> str:
        """
        Detect the type of medical document based on content patterns.
        
        Args:
            text: Document text
            
        Returns:
            Document type string
        """
        type_scores = {}
        
        # Check each document type pattern
        for doc_type, pattern in self.document_type_patterns.items():
            matches = pattern.findall(text)
            type_scores[doc_type] = len(matches)
        
        # Find the document type with the highest number of matches
        if max(type_scores.values(), default=0) > 0:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        # Default to general if no clear type
        return "general_medical"
    
    
    def _split_into_paragraphs(self, text: str, section_name: str) -> List[Tuple[str, str, str]]:
        """
        Split text into paragraph-level chunks.
        
        Args:
            text: Text to split
            section_name: Name of the section
            
        Returns:
            List of (chunk_text, section_name, level) tuples
        """
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        
        for i, para in enumerate(paragraphs):
            if not para.strip():
                continue
                
            # Check if paragraph is too large
            if len(para.split()) > self.chunk_size:
                # Further split into sentences
                sentences = sent_tokenize(para)
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    sentence_length = len(sentence.split())
                    
                    if current_length + sentence_length > self.chunk_size and current_chunk:
                        # Add current chunk
                        chunk_text = " ".join(current_chunk)
                        chunks.append((chunk_text, section_name, "paragraph"))
                        current_chunk = []
                        current_length = 0
                    
                    current_chunk.append(sentence)
                    current_length += sentence_length
                
                # Add final chunk if not empty
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append((chunk_text, section_name, "paragraph"))
            else:
                chunks.append((para.strip(), section_name, "paragraph"))
        
        return chunks
    
    def _create_sliding_window_chunks(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Create overlapping chunks using a sliding window approach.
        
        Args:
            text: Document text
            
        Returns:
            List of (chunk_text, section_name, level) tuples
        """
        sentences = sent_tokenize(text)
        chunks = []
        
        # If very few sentences, return as one chunk
        if len(sentences) <= 3:
            return [(text, "full_document", "document")]
        
        # Calculate stride (number of sentences to slide window)
        stride = max(1, (self.chunk_size - self.chunk_overlap) // 20)  # Approximate words per sentence
        
        # Create chunks with sliding window
        for i in range(0, len(sentences), stride):
            # Determine end index for current window
            window_size = min(i + max(3, self.chunk_size // 20), len(sentences))
            
            # Get text for current window
            window_text = " ".join(sentences[i:window_size])
            
            # Detect current section if possible
            section_match = self.section_pattern.search(window_text)
            section_name = section_match.group(0) if section_match else "sliding_window"
            
            chunks.append((window_text, section_name, "sliding"))
        
        return chunks
    
    def _create_recursive_chunks(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Create hierarchical chunks at different levels of granularity.
        
        Args:
            text: Document text
            
        Returns:
            List of (chunk_text, section_name, level) tuples
        """
        chunks = []
        
        # Level 1: Document-level chunk (if not too large)
        if len(text.split()) <= self.chunk_size * 2:
            chunks.append((text, "full_document", "document"))
        
        # Level 2: Section-level chunks
        section_matches = list(self.section_pattern.finditer(text))
        
        if section_matches:
            for i in range(len(section_matches)):
                start_pos = section_matches[i].start()
                section_name = text[section_matches[i].start():section_matches[i].end()].strip()
                
                # Determine section end
                if i < len(section_matches) - 1:
                    end_pos = section_matches[i+1].start()
                else:
                    end_pos = len(text)
                
                section_text = text[start_pos:end_pos].strip()
                
                # Add section as a chunk
                if section_text and len(section_text.split()) <= self.chunk_size:
                    chunks.append((section_text, section_name, "section"))
                
                # Level 3: Paragraph-level chunks
                paragraphs = re.split(r'\n\s*\n', section_text)
                
                for j, para in enumerate(paragraphs):
                    if para.strip() and len(para.split()) <= self.chunk_size:
                        chunks.append((para.strip(), section_name, "paragraph"))
                    
                    # Level 4: Sentence-level chunks for important sentences
                    if self._contains_important_entities(para):
                        sentences = sent_tokenize(para)
                        for sentence in sentences:
                            if self._contains_important_entities(sentence):
                                chunks.append((sentence.strip(), section_name, "sentence"))
        else:
            # No clear sections, fall back to paragraphs and sentences
            paragraphs = re.split(r'\n\s*\n', text)
            
            for para in paragraphs:
                if para.strip() and len(para.split()) <= self.chunk_size:
                    chunks.append((para.strip(), "paragraph", "paragraph"))
        
        return chunks
    def _embed_chunks(self, chunks: List[Document]) -> List[Document]:
        """Add embeddings to chunks."""
        for chunk in chunks:
            if chunk.page_content:
                embedding = self.embedding_model.encode(chunk.page_content)
                chunk.metadata['embedding'] = embedding.tolist()
        return chunks
    
    def _hybrid_chunking(self, content: str, metadata: Dict) -> List[Document]:
        """Hybrid chunking combining semantic and fixed-size approaches."""
        # First apply semantic chunking
        semantic_chunks = self._semantic_chunking(content, metadata)
        
        # Then apply fixed-size chunking to large semantic chunks
        final_chunks = []
        for chunk in semantic_chunks:
            if len(chunk.page_content) > self.chunk_size * 2:
                # Break down large chunks
                sub_chunks = self._fixed_chunking(chunk.page_content, chunk.metadata)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        # Add embeddings to all chunks
        final_chunks = self._embed_chunks(final_chunks)
        
        return final_chunks

    def _semantic_chunking(self, content: str, metadata: Dict) -> List[Document]:
        """Chunk based on semantic boundaries (paragraphs, sections)."""
        # Split by double newlines for paragraphs
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(Document(
                        page_content=current_chunk.strip(),
                        metadata=metadata.copy()
                    ))
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata=metadata.copy()
            ))
        
        return chunks

    def _fixed_chunking(self, content: str, metadata: Dict) -> List[Document]:
        """Fixed-size chunking with overlap."""
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            chunk_text = content[start:end]
            
            # Ensure we don't cut in the middle of a word
            if end < len(content) and not content[end].isspace():
                # Find the last space before the end
                last_space = chunk_text.rfind(' ')
                if last_space > 0:
                    end = start + last_space
                    chunk_text = content[start:end]
            
            chunks.append(Document(
                page_content=chunk_text.strip(),
                metadata=metadata.copy()
            ))
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, section_name: str, chunk_size: int) -> List[Tuple[str, str, str]]:
        """
        Create chunks by grouping sentences while respecting chunk size.
        
        Args:
            text: Text to chunk
            section_name: Name of the section
            chunk_size: Maximum chunk size in words
            
        Returns:
            List of (chunk_text, section_name, level) tuples
        """
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_length = len(sentence_words)
            
            # If adding this sentence exceeds chunk size and we already have content
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append((chunk_text, section_name, "sentences"))
                
                # Start new chunk with overlap
                # Find a good overlap point that doesn't split mid-thought
                overlap_sentences = min(2, len(current_chunk))
                current_chunk = current_chunk[-overlap_sentences:]
                current_length = len(" ".join(current_chunk).split())
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk if not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append((chunk_text, section_name, "sentences"))
        
        return chunks
    
    def _contains_important_entities(self, text: str) -> bool:
        """
        Check if text contains important medical entities.
        
        Args:
            text: Text to check
            
        Returns:
            Boolean indicating presence of important entities
        """
        entities = self._extract_medical_entities(text)
        return len(entities) > 0
    
    def _calculate_chunk_importance(self, text: str, position: int, total_chunks: int) -> float:
        """
        Calculate importance score for a chunk based on various factors.
        
        Args:
            text: Chunk text
            position: Position in document
            total_chunks: Total number of chunks
            
        Returns:
            Importance score between 0 and 1
        """
        # Extract entities and count them
        entities = self._extract_medical_entities(text)
        entity_count = len(entities)
        
        # Calculate entity density
        word_count = len(text.split())
        entity_density = entity_count / max(1, word_count / 100)
        
        # Position importance - first and last chunks often contain key information
        position_score = 0.0
        if position == 0 or position == total_chunks - 1:
            position_score = 0.2
        elif position < total_chunks * 0.2 or position > total_chunks * 0.8:
            position_score = 0.1
        
        # Check for important keywords
        keyword_score = 0.0
        important_keywords = ["significant", "important", "critical", "essential", "key", 
                             "finding", "diagnosis", "recommend", "conclude", "summary"]
        for keyword in important_keywords:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE):
                keyword_score += 0.05
        keyword_score = min(0.2, keyword_score)
        
        # Combine scores
        importance_score = min(1.0, 0.3 * entity_density + position_score + keyword_score)
        
        return importance_score
    
    def _extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical entities from text by category.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of categorized medical entities
        """
        categorized_entities = {}
        
        for category, pattern in self.medical_entity_categories.items():
            category_pattern = re.compile(pattern)
            matches = set(m.group(0).lower() for m in category_pattern.finditer(text))
            if matches:
                categorized_entities[category] = list(matches)
        
        return categorized_entities
    
    def _save_processed_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]):
        """
        Save processed chunks to disk for potential reuse.
        
        Args:
            doc_id: Document identifier
            chunks: List of processed chunks
        """
        try:
            import json
            
            # Create filename
            filename = f"{doc_id}_processed.json"
            filepath = self.processed_docs_dir / filename
            
            # Save chunks without embeddings (to save space)
            chunks_without_embeddings = []
            for chunk in chunks:
                chunk_copy = chunk.copy()
                # Remove embedding as it's large and can be regenerated
                del chunk_copy["embedding"]
                chunks_without_embeddings.append(chunk_copy)
            
            with open(filepath, 'w') as f:
                json.dump(chunks_without_embeddings, f)
            
            self.logger.info(f"Saved processed chunks to {filepath}")
        except Exception as e:
            self.logger.warning(f"Failed to save processed chunks: {e}")
    
    def batch_process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of documents.
        
        Args:
            documents: List of dictionaries with 'content' and 'metadata' keys
            
        Returns:
            List of processed document chunks with embeddings
        """
        all_processed_chunks = []
        
        for doc in documents:
            try:
                processed_chunks = self.process_document(doc["content"], doc["metadata"])
                all_processed_chunks.extend(processed_chunks)
            except Exception as e:
                self.logger.error(f"Error processing document: {e}")
                # Continue with the next document
                continue
        
        return all_processed_chunks