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

class Knowledge(BaseModel):
    details: SubAgentResponse
    reference: str = Field(default="", description="Textual reference to the source chunk")

class AgentResponse(BaseModel):
    """
    Response from analyzing chunks - contains knowledge items and any errors
    """
    knowledge_list: List[Knowledge] = Field(default_factory=list, description="List of extracted knowledge items")
    errors: List[str] = Field(default_factory=list, description="List of error messages if any")
