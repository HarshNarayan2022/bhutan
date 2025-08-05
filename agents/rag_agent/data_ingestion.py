import os
import json
import logging
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from PyPDF2 import PdfReader

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredMarkdownLoader
)
from langchain_core.documents import Document

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MedicalDataIngestion:
    """
    Handles loading of various medical document formats.
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the data ingestion pipeline.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize loaders mapping
        self.loaders = {
            '.txt': self._load_text,
            '.pdf': self._load_pdf,
            '.csv': self._load_csv,
            '.json': self._load_json,
            '.md': self._load_markdown
        }
        
        # Initialize stats
        self.stats = {
            "files_processed": 0,
            "documents_ingested": 0,
            "errors": 0
        }
        
        logger.info("MedicalDataIngestion initialized")
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        Load a document based on its file type.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File not found: {file_path}")
            return []
        
        suffix = path.suffix.lower()
        if suffix not in self.loaders:
            self.logger.warning(f"Unsupported file type: {suffix}")
            return []
        
        try:
            return self.loaders[suffix](file_path)
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {str(e)}")
            return []
    
    def _load_text(self, file_path: str) -> List[Document]:
        """Load text files."""
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            return loader.load()
        except Exception as e:
            # Fallback to manual loading
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                doc = Document(
                    page_content=content,
                    metadata={"source": file_path, "type": "text"}
                )
                return [doc]
            except Exception as e2:
                self.logger.error(f"Error loading text file: {e2}")
                return []
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF files."""
        try:
            loader = PyPDFLoader(file_path)
            return loader.load()
        except Exception as e:
            # Fallback to PyPDF2
            try:
                reader = PdfReader(file_path)
                documents = []
                
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        doc = Document(
                            page_content=page_text,
                            metadata={
                                "source": file_path,
                                "type": "pdf",
                                "page": page_num + 1
                            }
                        )
                        documents.append(doc)
                
                return documents
            except Exception as e2:
                self.logger.error(f"Error loading PDF file: {e2}")
                return []
    
    def _load_csv(self, file_path: str) -> List[Document]:
        """Load CSV files."""
        try:
            loader = CSVLoader(file_path)
            return loader.load()
        except Exception as e:
            # Fallback to pandas
            try:
                df = pd.read_csv(file_path)
                documents = []
                
                # Find the column with the most text content
                text_column = self._identify_content_column(df)
                
                for _, row in df.iterrows():
                    content = str(row[text_column])
                    metadata = {
                        "source": file_path,
                        "type": "csv"
                    }
                    
                    # Add other columns as metadata
                    for col in df.columns:
                        if col != text_column and not pd.isna(row[col]):
                            metadata[col] = str(row[col])
                    
                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    documents.append(doc)
                
                return documents
            except Exception as e2:
                self.logger.error(f"Error loading CSV file: {e2}")
                return []
    
    def _load_json(self, file_path: str) -> List[Document]:
        """Load JSON files."""
        try:
            # For JSON files, we'll create documents from each entry
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    content = json.dumps(item, indent=2)
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": file_path,
                            "type": "json",
                            "index": idx
                        }
                    )
                    documents.append(doc)
            else:
                content = json.dumps(data, indent=2)
                doc = Document(
                    page_content=content,
                    metadata={"source": file_path, "type": "json"}
                )
                documents.append(doc)
            
            return documents
        except Exception as e:
            self.logger.error(f"Error loading JSON file: {e}")
            return []
    
    def _load_markdown(self, file_path: str) -> List[Document]:
        """Load Markdown files."""
        try:
            loader = UnstructuredMarkdownLoader(file_path)
            return loader.load()
        except Exception as e:
            # Fallback to simple text loading
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                doc = Document(
                    page_content=content,
                    metadata={"source": file_path, "type": "markdown"}
                )
                return [doc]
            except Exception as e2:
                self.logger.error(f"Error loading Markdown file: {e2}")
                return []
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            List of all loaded documents
        """
        dir_path = Path(directory_path)
        if not dir_path.exists():
            self.logger.error(f"Directory not found: {directory_path}")
            return []
        
        all_documents = []
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.loaders:
                self.logger.info(f"Loading {file_path.name}")
                documents = self.load_document(str(file_path))
                all_documents.extend(documents)
        
        return all_documents
    
    def _identify_content_column(self, df: pd.DataFrame) -> str:
        """
        Identify which column in a DataFrame contains the main content.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Name of the content column
        """
        # Look for columns with these names
        content_column_names = ["content", "text", "description", "abstract", "body"]
        
        for name in content_column_names:
            if name in df.columns:
                return name
        
        # If no standard content column found, look for the column with longest strings
        avg_lengths = {}
        for col in df.columns:
            if df[col].dtype == 'object':  # Only check string columns
                # Calculate average string length
                avg_length = df[col].astype(str).apply(len).mean()
                avg_lengths[col] = avg_length
        
        if avg_lengths:
            # Return column with longest average string length
            return max(avg_lengths.items(), key=lambda x: x[1])[0]
        
        # Fallback to first column
        return df.columns[0]
    
    def _identify_json_content_field(self, item: Dict) -> Optional[str]:
        """
        Identify which field in a JSON object contains the main content.
        
        Args:
            item: Dictionary representing a JSON object
            
        Returns:
            Name of the content field or None if not found
        """
        # Look for fields with these names
        content_field_names = ["content", "text", "description", "abstract", "body"]
        
        for name in content_field_names:
            if name in item and isinstance(item[name], str):
                return name
        
        # If no standard content field found, look for the field with longest string
        text_fields = {}
        for key, value in item.items():
            if isinstance(value, str) and len(value) > 50:
                text_fields[key] = len(value)
        
        if text_fields:
            # Return field with longest text
            return max(text_fields.items(), key=lambda x: x[1])[0]
        
        return None