# app/services/github.py
from typing import List, Dict, Optional
import httpx
from app.core.config import get_settings

settings = get_settings()

class GitHubService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {settings.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_repository_content(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
            f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
            headers=self.headers
         )
        response.raise_for_status()
        return response.json()

        

        
    
    async def get_file_content(self, file_url: str) -> Optional[str]:
       async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(file_url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("content")

    
    async def get_repository_tree(self, owner: str, repo: str) -> List[Dict]:
        """Get complete repository tree recursively"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
        # Get default branch
            repo_response = await client.get(
             f"{self.base_url}/repos/{owner}/{repo}",
              headers=self.headers
              )
            repo_response.raise_for_status()
            default_branch = repo_response.json()["default_branch"]

    # Get tree
            tree_response = await client.get(
            f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
             headers=self.headers
              )
            tree_response.raise_for_status()
        return tree_response.json()["tree"]


    @staticmethod
    def is_processable_file(path: str) -> bool:
        """Check if file should be processed based on extension"""
        processable_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.md', 
            '.rst', '.yaml', '.yml', '.json'
        }
        return any(path.endswith(ext) for ext in processable_extensions)