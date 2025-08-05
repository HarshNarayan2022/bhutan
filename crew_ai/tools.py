import os
from crewai.tools import BaseTool
from crewai.tools import tool
from transformers import pipeline
from backend.crew_ai.data_retriever_util import get_user_profile
from backend.crew_ai.config import get_config
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import ClassVar
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import pipeline
from gradio_client import Client

class MentalHealthTools:
    """Tools for mental health chatbot"""
    @tool("Bhutanese Helplines")
    def get_bhutanese_helplines() -> str:
        """
        Retrieves Bhutanese mental health helplines from the PostgreSQL `resources` table.

        """
        try:
            db_uri = os.getenv("SUPABASE_DB_URI")
            if not db_uri:
                raise ValueError("SUPABASE_DB_URI not set in environment")

            conn = psycopg2.connect(db_uri)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT name, description, phone, website, address, operation_hours
            FROM resources
            """
            cursor.execute(query)
            helplines = cursor.fetchall()

            if not helplines:
                return "No helplines found in the database."

            response = "📞 Bhutanese Mental Health Helplines:\n"
            for h in helplines:
                response += f"\n📌 {h['name']}"
                if h['description']:
                    response += f"\n   Description: {h['description']}"
                if h['phone']:
                    response += f"\n   📱 Phone: {h['phone']}"
                if h['website']:
                    response += f"\n   🌐 Website: {h['website']}"
                if h['address']:
                    response += f"\n   🏠 Address: {h['address']}"
                if h['operation_hours']:
                    response += f"\n   ⏰ Hours: {h['operation_hours']}"
                response += "\n"

            cursor.close()
            conn.close()
            return response.strip()

        except Exception as e:
            return f"⚠️ Failed to fetch helplines from DB: {str(e)}"
        

class CrisisClassifierTool(BaseTool):
    name: str = "Crisis Classifier"
    description: str = (
        "A tool that classifies text into predefined categories. "
        "Input should be the text to classify."
    )
            
    def _run(self, text: str) -> str:
        """
        Classifies the given text using the Hugging Face model.
        Returns the classification label and score.
        """
        try:
            # Initialize the pipeline here (will happen on every tool call)
            classifier = pipeline("sentiment-analysis", model="sentinet/suicidality")
            result = classifier(text)
            if result:
                label = result[0]['label']
                score = result[0]['score']
                return f"Classification: {label} (Score: {score:.4f})"
            return "Could not classify the text."
        except Exception as e:
            return f"Error during text classification: {e}"
        
class MentalConditionClassifierTool(BaseTool):
    name: str = "Mental condition Classifier"
    description: str = (
        "A tool that classifies text into predefined categories. "
        "Input should be the text to classify."
    )

    # Class-level cache for the client
    _client = None

    def _get_client(self):
        if self._client is None:
            self.__class__._client = Client("ety89/mental_health_text_classifiaction")  # ✅ fixed typo
        return self._client
            
    def _run(self, text: str) -> str:
        """
        Classifies the given text using the Hugging Face model.
        Returns the classification label and score.
        """
        try:
            # Initialize the pipeline here (will happen on every tool call)
            
            client = Client("ety89/mental_health_text_classifiaction")
            result = client.predict(
                input_text=text,
                api_name="/predict"
            )
            if result:
                label = result.split(':')[-2].split('(')[-2].strip()
                score = result.split(':')[-1].strip(')').strip()
                return label, score
        
            return "Could not classify the text."
    
        except Exception as e:
            return f"Error during text classification: {e}"
        
class DataRetrievalTool(BaseTool):
    name: str = "Data Retrieval"
    description: str = (
        "A tool that fetched the user profile data from the database. "
        "Input should be User Profile ID."
    )

       
    def _run(self, user_profile_id: str) -> str:
        """
        Fetches the user profile data from the database using the user profile ID.
        Returns the user profile information or an error message.
        """
        try:

            config = get_config()   

            if user_profile_id.strip() == "anon_user":
                return config['default_user_profile']

            # Retrieve user profile using the utility function
            user_profile = get_user_profile(user_profile_id)
            if user_profile:
                return f"User Profile: {user_profile}"
            return "User profile not found."
        except Exception as e:
            return f"Error retrieving user profile: {e}"
        
class QueryVectorStoreTool(BaseTool):
    name: str = "Query Vector Store"
    description: str = (
        "Queries the Supabase-hosted PostgreSQL vector database with a user query and classified condition, "
        "and retrieves the top 3 most relevant documents."
    )

    # Shared across all instances
    embedding_model: ClassVar = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    def _run(self, user_query: str, classified_condition: str) -> dict:
        query_text = f"{user_query} Condition: {classified_condition}"
        embedding = self.embedding_model.embed_query(query_text)

        db_uri = os.getenv("SUPABASE_DB_URI")
        if not db_uri:
            raise ValueError("SUPABASE_DB_URI not set in environment")

        conn = psycopg2.connect(db_uri)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ac.chunk_text, a.title, a.topic, a.source, ac.embedding <-> %s::vector AS score
            FROM article_chunks ac
            JOIN articles a ON ac.doc_id = a.id
            ORDER BY score
            LIMIT 3;
        """, (embedding,))


        rows = cursor.fetchall()
        docs = [
            {
                "text": row[0],
                "title": row[1],
                "topic": row[2],
                "source": row[3],
                "score": row[4]
            }
            for row in rows
        ]
        
        cursor.close()
        conn.close()

        return {"docs": docs}

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented")
        
        