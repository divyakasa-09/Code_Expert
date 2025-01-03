import asyncio
from typing import List, Dict, Optional
from app.services.github import GitHubService
from app.services.mistral import MistralService
from app.services.snowflake import SnowflakeSearchService
import psutil
import logging

# Configure Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
    """
    Splits a given text into smaller chunks with optional overlap.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        while end > start and not text[end - 1].isspace() and end < text_length:
            end -= 1
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap

    return [chunk for chunk in chunks if chunk]  # Remove empty chunks

def log_system_status():
    """
    Log current memory usage for debugging resource issues.
    """
    process = psutil.Process()
    memory = process.memory_info().rss / (1024 * 1024)  # Memory in MB
    logger.info(f"Memory usage: {memory:.2f} MB")

class RepositoryProcessor:
    def __init__(self, batch_size: int = 2):
        self.github_service = GitHubService()
        self.mistral_service = MistralService()
        self.snowflake_service = SnowflakeSearchService()
        self.progress_callback = None
        self.batch_size = batch_size

    def set_callback(self, callback):
        self.progress_callback = callback

    def set_batch_size(self, batch_size: int):
        self.batch_size = batch_size

    async def process_file(self, file_url: str, file_path: str, repo: str) -> Optional[List[Dict]]:
        """
        Process a single file, chunk its content, and send for embedding and response generation.
        """
        try:
            logger.info(f"Fetching content for file: {file_path}")
            content = await self.github_service.get_file_content(file_url)
            if not content:
                logger.warning(f"Empty content for file: {file_path}")
                return None

            chunks = chunk_text(content)
            logger.info(f"Chunked file {file_path} into {len(chunks)} chunks")

            for chunk_idx, chunk in enumerate(chunks):
                try:
                    log_system_status()  # Monitor memory usage
                    embedding = self.mistral_service.generate_embedding(chunk)
                    response = self.mistral_service.generate_response(
                        prompt="Analyze and summarize this code chunk:",
                        messages=[{"role": "user", "content": chunk}]
                    )
                    await self.snowflake_service.store_embedding(
                        repo_name=repo,
                        file_path=file_path,
                        content=chunk,
                        embedding=embedding,
                        summary=response
                    )
                    if self.progress_callback:
                        await self.progress_callback(file_path)

                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx + 1} in {file_path}: {e}")
                    continue

            return {"file_path": file_path, "chunks_processed": len(chunks)}

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None

    async def ingest_repository(self, owner: str, repo: str) -> bool:
        """
        Process all files in a repository.
        """
        semaphore = asyncio.Semaphore(self.batch_size)
        tasks = []

        async def process_with_limit(file):
            async with semaphore:
                return await self.process_file(file['url'], file['path'], repo)

        try:
            logger.info(f"Fetching repository tree for {owner}/{repo}...")
            repo_content = await self.github_service.get_repository_tree(owner, repo)

            for file in repo_content:
                if self._should_process_file(file['path']):
                    tasks.append(process_with_limit(file))

            logger.info(f"Processing {len(tasks)} files...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if r)
            logger.info(f"Successfully processed {success_count}/{len(tasks)} files.")
            return success_count > 0

        except Exception as e:
            logger.error(f"Repository ingestion failed: {e}")
            return False
        finally:
            self.mistral_service.close()

    def _should_process_file(self, file_path: str) -> bool:
        """
        Determine if a file should be processed based on its extension.
        """
        valid_extensions = {'.py', '.js', '.md', '.yml', '.json'}
        return any(file_path.endswith(ext) for ext in valid_extensions)
