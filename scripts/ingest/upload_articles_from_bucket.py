import os
import io
import uuid
import requests
import tempfile

from dotenv import load_dotenv
import boto3
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.deps import get_config_value, get_embedding_model
from backend.rag.pdf_parser import extract_text
from backend.rag.embeddings import generate_embeddings
from backend.rag.chunker import smart_chunk_text, create_chunk_objects
from backend.scripts.db.session import SessionLocal
from backend.scripts.migration_schemas.resources_models import Article, ArticleChunk

load_dotenv()

# === Load ENV ===
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_REGION")
ENDPOINT_URL = os.getenv("SUPABASE_STORAGE_ENDPOINT")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET")
SUPABASE_STORAGE_URL = os.getenv("SUPABASE_STORAGE_URL")

class SyncUpload:
    def __init__(self):
        self.model = get_embedding_model()
        self.embedding_dim = get_config_value("model.embedding_dim", 384)
        self.file_list = self.get_articles_supabase()
        self.current_articles = self.get_current_articles_psql()

    def get_articles_supabase(self):
        s3 = boto3.client(
            's3',
            region_name=REGION,
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]

    def get_current_articles_psql(self):
        session = SessionLocal()
        try:
            return [a.title for a in session.query(Article.title).all()]
        finally:
            session.close()

    def extract_text_from_bytes(self, pdf_bytesio):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(pdf_bytesio.read())
            tmp.flush()
            return extract_text(tmp.name)

    def create_article_object(self, id, title):
        return Article(id=id, title=title)

    def file_to_chunks(self, article_filename, doc_id):
        article_url = f"{SUPABASE_STORAGE_URL}/v1/object/public/pdfs//{article_filename}"
        print(f"[INFO] Downloading: {article_url}")
        response = requests.get(article_url)
        if response.status_code != 200:
            print(f"[ERROR] Failed to download {article_url}")
            return None

        try:
            text = self.extract_text_from_bytes(io.BytesIO(response.content))
            print(f"[SUCCESS] Extracted {len(text)} characters from '{article_filename}'")
            raw_chunks = smart_chunk_text(text)
            chunk_objs = create_chunk_objects(doc_id=doc_id, chunks=raw_chunks)
            embedded_chunks = generate_embeddings(chunk_objs)
            return embedded_chunks
        except Exception as e:
            print(f"[ERROR] Processing failed for {article_filename}: {e}")
            return None

    def articles_to_rag(self):
        session = SessionLocal()
        for article_file in self.file_list:
            article_title = article_file.replace(".pdf", "")
            if article_title in self.current_articles:
                print(f"[SKIP] Already processed: {article_title}")
                continue

            doc_id = str(uuid.uuid4())
            article = self.create_article_object(id=doc_id, title=article_title)
            chunk_data = self.file_to_chunks(article_file, doc_id)

            if not chunk_data:
                continue

            try:
                chunks = [
                    ArticleChunk(
                        chunk_id=c["chunk_id"],
                        doc_id=c["doc_id"],
                        chunk_text=c["chunk_text"],
                        embedding=c["embedding"],
                        keywords=c["keywords"]
                    ) for c in chunk_data
                ]

                session.add(article)
                session.add_all(chunks)
                session.commit()
                print(f"[SUCCESS] Uploaded: {article_title} ({len(chunks)} chunks)")
            except SQLAlchemyError as e:
                session.rollback()
                print(f"[ERROR] DB insert failed for {article_title}: {e}")
            finally:
                session.close()

if __name__ == "__main__":
    SyncUpload().articles_to_rag()