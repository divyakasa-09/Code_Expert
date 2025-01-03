import snowflake.connector
from app.core.config import get_settings
from typing import List, Dict
import numpy as np
import json
import logging
import base64

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
settings = get_settings()

class SnowflakeSearchService:
    def __init__(self):
        """Initialize connection to Snowflake and set up the vector search infrastructure."""
        self.conn = snowflake.connector.connect(
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            account=settings.snowflake_account,
            database='CODE_EXPERT'
        )
        self._initialize_vector_search()

    def _initialize_vector_search(self):
        """Initialize the database and create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS CODE_EXPERT;")
            cursor.execute("USE DATABASE CODE_EXPERT;")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_embeddings (
                id INTEGER AUTOINCREMENT,
                repo_name STRING,
                file_path STRING,
                content STRING,
                is_base64 BOOLEAN,
                embedding VARIANT,
                summary STRING,
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (id)
            );
            """)
            logger.info("Database and table initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector search: {e}")
            raise
        finally:
            cursor.close()

    def _is_base64(self, content: str) -> bool:
        """Check if content is base64 encoded."""
        try:
            return bool(base64.b64decode(content))
        except Exception:
            return False

    def _decode_if_base64(self, content: str) -> tuple[str, bool]:
        """Decode content if it's base64 encoded."""
        if self._is_base64(content):
            try:
                decoded = base64.b64decode(content).decode('utf-8')
                return decoded, True
            except Exception:
                return content, False
        return content, False

    async def store_embedding(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        embedding: List[float],
        summary: str = None
    ):
        """Store embedding and other metadata in the Snowflake database."""
        cursor = self.conn.cursor()
        try:
            # Process content - decode if base64
            decoded_content, is_base64 = self._decode_if_base64(content)
            content_to_store = decoded_content if is_base64 else content

            # Debug logging
            logger.info(f"Storing embedding for file: {file_path}")
            logger.info(f"Content snippet: {content_to_store[:100]}...")
            logger.info(f"Is base64: {is_base64}")
            logger.info(f"Embedding length: {len(embedding)}")
            logger.info(f"First few embedding values: {embedding[:5]}")

            # Convert embedding to JSON format
            embedding_json = json.dumps({"vector": embedding})
            
            query = """
            INSERT INTO code_embeddings 
                (repo_name, file_path, content, is_base64, embedding, summary)
            SELECT 
                %(repo_name)s, 
                %(file_path)s, 
                %(content)s,
                %(is_base64)s,
                TO_VARIANT(%(embedding)s), 
                %(summary)s
            """
            
            params = {
                "repo_name": repo_name,
                "file_path": file_path,
                "content": content_to_store,
                "is_base64": is_base64,
                "embedding": embedding_json,
                "summary": summary
            }
            
            # Log the parameters being sent
            logger.info("Query parameters:")
            for key, value in params.items():
                if key != 'embedding':
                    logger.info(f"{key}: {value}")
                else:
                    logger.info(f"{key}: {value[:100]}...")

            cursor.execute(query, params)
            self.conn.commit()
            logger.info("Successfully stored embedding")
            
        except Exception as e:
            logger.error(f"Error storing embedding in Snowflake: {e}")
            logger.error(f"Full error details: {str(e)}")
            raise
        finally:
            cursor.close()

    async def search_similar(
        self,
        query_embedding: List[float],
        repo_name: str,
        limit: int = 5
    ) -> List[Dict]:
        """Search for similar content based on vector similarity."""
        cursor = self.conn.cursor()
        try:
            # Convert query embedding to string representation
            query_embedding_str = ','.join(str(x) for x in query_embedding)
            
            query = """
            SELECT 
                file_path, 
                content, 
                summary,
                VECTOR_COSINE_DISTANCE(embedding, ARRAY_CONSTRUCT({0})) as similarity
            FROM code_embeddings
            WHERE repo_name = ?
            ORDER BY similarity DESC
            LIMIT ?
            """.format(query_embedding_str)
            
            cursor.execute(query, (repo_name, limit))

            results = [{
                'file_path': row[0],
                'content': row[1],
                'summary': row[2],
                'similarity': float(row[3])
            } for row in cursor.fetchall()]
            
            return results
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {e}")
            raise
        finally:
            cursor.close()

    async def delete_repository_data(self, repo_name: str):
        """Delete all data for a specific repository."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM code_embeddings WHERE repo_name = ?",
                (repo_name,)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error deleting repository data: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        """Close the Snowflake connection."""
        if self.conn:
            self.conn.close()

    async def get_repository_statistics(self, repo_name: str) -> Dict:
        """Get statistics about stored embeddings for a repository."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT file_path) as total_files,
                MIN(created_at) as first_indexed,
                MAX(created_at) as last_indexed
            FROM code_embeddings
            WHERE repo_name = ?
            """, (repo_name,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'total_chunks': row[0],
                    'total_files': row[1],
                    'first_indexed': row[2],
                    'last_indexed': row[3]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting repository statistics: {e}")
            raise
        finally:
            cursor.close()