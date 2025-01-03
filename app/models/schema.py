# app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FileContent(BaseModel):
    repo_name: str
    file_path: str
    content: str
    file_type: str
    embedding: Optional[List[float]] = None
    last_updated: datetime = datetime.now()

class Repository(BaseModel):
    owner: str
    name: str
    default_branch: str
    
class Question(BaseModel):
    repository: str
    query: str
    
class Answer(BaseModel):
    answer: str
    references: List[str]
    confidence: float