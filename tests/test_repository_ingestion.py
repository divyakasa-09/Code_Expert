# import asyncio
# from app.services.repository_ingestion import RepositoryProcessor

# async def test_ingest_repository():
#     owner = "tiangolo"  # Repository owner
#     repo = "fastapi"    # Repository name
#     batch_size = 5      # Process 5 files at a time

#     try:
#         # Initialize the RepositoryProcessor
#         processor = RepositoryProcessor(batch_size=batch_size)
#         total_files = 0
#         total_chunks = 0

#         # Define a progress callback to track files and chunks
#         async def process_callback(file_path):
#             nonlocal total_chunks
#             total_chunks += 1
#             print(f"[{total_chunks}] Processing: {file_path}")

#         # Set the callback for progress tracking
#         processor.set_callback(process_callback)

#         # Start the repository ingestion
#         print(f"Starting ingestion for repository: {owner}/{repo}")
#         success = await processor.ingest_repository(owner, repo)

#         # Final output after processing
#         print(f"\nProcessed {total_chunks} total chunks")
#         print(f"Repository processed: {'✓' if success else '✗'}")
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     asyncio.run(test_ingest_repository())


import asyncio
from app.services.repository_ingestion import RepositoryProcessor

async def test_ingest_repository():
    owner = "divyakasa-09"  # Replace with your GitHub username
    repo = "Code_Expert"    # Replace with your repository name

    try:
        processor = RepositoryProcessor(batch_size=2)
        total_chunks = 0

        async def process_callback(file_path):
            nonlocal total_chunks
            total_chunks += 1
            print(f"[{total_chunks}] Processing: {file_path}")

        processor.set_callback(process_callback)

        print(f"Starting ingestion for repository: {owner}/{repo}")
        success = await processor.ingest_repository(owner, repo)

        print(f"\nProcessed {total_chunks} total chunks")
        print(f"Repository processed: {'✓' if success else '✗'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ingest_repository())
