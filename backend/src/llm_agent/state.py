from typing import List

from pydantic import BaseModel, Field

class SubAgentResponse(BaseModel):
    question: str = Field(..., description="Question to ask user to measure their understanding")
    knowledge_object: str = Field(..., description="Name of the topic/knowledge that we are asking about")

class ChunkAnalysisResponse(BaseModel):
    """
    Response from LLM analyzing a single chunk - contains list of SubAgentResponse objects
    """
    questions: List[SubAgentResponse] = Field(default_factory=list, description="List of questions extracted from the chunk")

class ChunkKnowledge(BaseModel):
    knowledge_objects: ChunkAnalysisResponse = Field(..., description="Knowledge objects extracted from the chunk")
    reference: int = Field(default=0, description="Index of the chunk in the document")
