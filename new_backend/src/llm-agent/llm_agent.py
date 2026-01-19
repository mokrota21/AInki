from ..config.settings import settings
from .state import AgentResponse, Knowledge, SubAgentResponse, ChunkAnalysisResponse
import logging
import asyncio
from pathlib import Path
from typing import List

logger = logging.getLogger("llm_agent")

# Get the directory where this file is located
_current_dir = Path(__file__).parent
_prompt_path = _current_dir / "prompts" / "general-textbook.txt"
with open(_prompt_path, encoding='utf-8') as f:
    PROMPT = f.read()


async def analyze_chunk(chunk: str, chunk_reference: str = "") -> AgentResponse:
    """
    Analyzes single chunk on presence of any review interesting information
    
    Args:
        chunk: Text chunk to analyze
        chunk_reference: Reference identifier for the chunk (e.g., chunk index or page number)
    
    Returns:
        AgentResponse with knowledge_list and errors
    """
    try:
        model = settings.llm_client
        # Model returns ChunkAnalysisResponse with list of SubAgentResponse objects
        model_with_structure = model.with_structured_output(ChunkAnalysisResponse)

        # Format prompt with chunk content
        user_content = PROMPT.format(current_chunk=chunk)
        
        messages = [
            {"role": "system", "content": "You are an expert at analyzing educational content and extracting important knowledge that students should remember."},
            {"role": "user", "content": user_content}
        ]

        parsed_response = await model_with_structure.ainvoke(
            messages,
            config={
                "callbacks": [settings.langfuse_handler],
            }
        )
        
        # Manually construct Knowledge objects from SubAgentResponse objects
        knowledge_list = []
        for sub_response in parsed_response.questions:
            knowledge = Knowledge(
                details=sub_response,
                reference=chunk_reference
            )
            knowledge_list.append(knowledge)
        
        return AgentResponse(knowledge_list=knowledge_list, errors=[])
    except Exception as e:
        logger.error(f"Error analyzing chunk: {e}", exc_info=True)
        return AgentResponse(knowledge_list=[], errors=[str(e)])


async def analyze_chunks_parallel(
    chunks: List[str], 
    chunk_references: List[str] = None,
    batch_size: int = 10,
    max_concurrent: int = 5
) -> AgentResponse:
    """
    Analyzes a list of chunks in parallel batches and returns aggregated results.
    
    Args:
        chunks: List of text chunks to analyze
        chunk_references: Optional list of reference identifiers for each chunk
        batch_size: Number of chunks to process in each batch
        max_concurrent: Maximum number of concurrent requests per batch
    
    Returns:
        AgentResponse with aggregated knowledge_list and errors from all chunks
    """
    if chunk_references is None:
        chunk_references = [f"chunk_{i}" for i in range(len(chunks))]
    
    if len(chunks) != len(chunk_references):
        raise ValueError("chunks and chunk_references must have the same length")
    
    all_knowledge = []
    all_errors = []
    
    # Process chunks in batches
    for batch_start in range(0, len(chunks), batch_size):
        batch_end = min(batch_start + batch_size, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]
        batch_references = chunk_references[batch_start:batch_end]
        
        logger.info(f"Processing batch {batch_start // batch_size + 1}: chunks {batch_start} to {batch_end - 1}")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(chunk: str, ref: str):
            async with semaphore:
                return await analyze_chunk(chunk, ref)
        
        # Process batch in parallel
        tasks = [
            analyze_with_semaphore(chunk, ref) 
            for chunk, ref in zip(batch_chunks, batch_references)
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results from batch
        for result in batch_results:
            if isinstance(result, Exception):
                all_errors.append(str(result))
                logger.error(f"Exception in batch processing: {result}")
            else:
                all_knowledge.extend(result.knowledge_list)
                all_errors.extend(result.errors)
    
    logger.info(f"Completed processing {len(chunks)} chunks. Found {len(all_knowledge)} knowledge items, {len(all_errors)} errors")
    
    return AgentResponse(knowledge_list=all_knowledge, errors=all_errors)
