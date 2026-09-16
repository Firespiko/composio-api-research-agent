from typing import List, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    claim: str
    url: str

class ResearchResult(BaseModel):
    id: int
    name: str
    category: str
    description: str

    auth_methods: List[str]
    access_type: str

    api_types: List[str]
    sdk_available: bool | None = None

    api_breadth: str
    mcp_status: str

    buildability: str
    blocker: Optional[str]

    evidence: List[Evidence]

    confidence: float = Field(ge=0.0, le=1.0)