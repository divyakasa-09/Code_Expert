import sys
import os
import asyncio

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports
from app.services.github import GitHubService
from app.services.snowflake import SnowflakeSearchService
from app.services.mistral import MistralService
# Test Mistral Service
from app.services.mistral import MistralService
from app.core.config import get_settings
# Test GitHub Service
import json
async def test_github_service():
    try:
        github_service = GitHubService()
        owner = "tiangolo"  # Example: Owner of the FastAPI repo
        repo = "fastapi"    # Example: Repository name
        files = await github_service.get_repository_tree(owner, repo)
        print("GitHub Repository Files:")
        for file in files[:10]:  # Display the first 10 files
            print(file)
    except Exception as e:
        print(f"Error testing GitHub service: {e}")


# Test Snowflake Service
async def test_snowflake_service():
    try:
        snowflake_service = SnowflakeSearchService()
        await snowflake_service.store_embedding(
            repo_name='test_repo',
            file_path='test/file.py',
            content='print("Hello")',
            embedding=[0.1, 0.2, 0.3]
        )
        print("Snowflake test successful")
    except Exception as e:
        print(f"Error testing Snowflake service: {e}")





def test_mistral_service():
    settings = get_settings()
    mistral_service = MistralService()
    query = "What is the capital of France?"
    context = []
    response = mistral_service.generate_response(query, context)
    print("Response:", response)
    mistral_service.close()





# Run all tests
if __name__ == "__main__":
    # Run GitHub service test
    asyncio.run(test_github_service())
    
    # Run Snowflake service test
    asyncio.run(test_snowflake_service())
    
    # Run Mistral service test (synchronous)
    test_mistral_service()