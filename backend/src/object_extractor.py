from langfuse.openai import AzureOpenAI
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from .neo4j_graph import add_knowledge_object
from .repetition import RepeatState
from .neo4j_graph import merge_repetition_state
from tqdm import tqdm

load_dotenv()

logger = logging.getLogger(__name__)

model_name = os.getenv("MODEL_NAME")
client = AzureOpenAI()
completion_tokens = 10000
price_mapping = {
    "gpt-5-nano": (0.05 / 1000000, 0.40 / 1000000),
}
prompts = {
    "math_textbook_prompt": """
        Analyze the following text chunk and determine information that user should remember. Such information could be explicit, i.e. algorithm, or implicit, like subtle property implied by the text, small note mentioned by author, etc.
        - Definition: A formal statement that explains the meaning of a term
        - Theorem: A statement that has been proven to be true
        - Lemma: A smaller result used to prove a larger theorem
        - Axiom: A fundamental assumption that is accepted without proof
        - Property: A characteristic or attribute of a mathematical object
        - Corollary: A direct consequence of a theorem
        - Conjecture: A statement that is believed to be true but not yet proven
        - Example: A specific instance illustrating a concept
        - Proof: A logical argument demonstrating the truth of a statement
        - Other: Any other information that user should remember
        
        Text chunk:
        {current_chunk}
        
        Respond with a JSON object in this exact format:
        {{
            "objects": [
                {{
                    "object_type": "definition"/"theorem"/"lemma"/"axiom"/"property"/"corollary"/"conjecture"/"example"/"proof"/"other",
                    "object_name": "name of the object"
                }}
            ]
        }}
        
        If no objects are found, return {{"objects": []}}.
        """,
    "general_textbook_prompt": """
        Analyze the following text chunk and determine key information that a reader should remember. 
        Such information could be explicit (e.g., a definition, rule, or example) or implicit (e.g., an important insight, implication, or subtle note mentioned by the author).

        Possible object types:
        - Definition: A formal statement that explains the meaning of a term or concept
        - Principle: A fundamental rule, law, or guiding idea
        - Fact: A specific piece of information that is presented as true
        - Example: A specific instance illustrating a concept or idea
        - Observation: A noteworthy statement, remark, or empirical finding
        - Method: A described procedure, technique, or approach
        - Note: A useful comment, warning, or side remark made by the author
        - Other: Any other information that the reader should remember

        Text chunk:
        {current_chunk}

        Respond with a JSON object in this exact format:
        {{
            "objects": [
                {{
                    "object_type": "definition"/"principle"/"fact"/"example"/"observation"/"method"/"note"/"other",
                    "object_name": "name or short title of the object"
                }}
            ]
        }}

        If no objects are found, return {{"objects": []}}.
        """
}

def extract_objects_from_chunks(chunks: List[Tuple[str, int]], doc_id: int, prompt_key: str = "general_textbook_prompt", max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    Process chunks to extract definitions, theorems, and properties using OpenAI.
    
    Args:
        chunks: List of tuples (text chunk, chunk idx)
        doc_id: Document ID for tracking
    
    Returns:
        List of extracted objects with their metadata
    """
    extracted_objects = []
    
    pbar = tqdm(total=len(chunks))
    current_retries = 0
    
    for i, (current_chunk, chunk_idx) in enumerate(chunks):
        object_detection_prompt = prompts[prompt_key].format(current_chunk=current_chunk)

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert mathematician. Analyze mathematical text and identify definitions, theorems, and properties. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": object_detection_prompt
                }
            ],
            max_completion_tokens=completion_tokens,
            model=model_name
        )

        try:
            detection_result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # If JSON parsing fails, skip this chunk
            if max_retries - current_retries > 0:
                current_retries += 1
            else:
                current_retries = 0
                pbar.update(1)
            continue
        
        current_retries = 0
        pbar.update(1)
        
        # Process all objects found in this chunk
        objects = detection_result.get("objects", [])
        for obj in objects:
            object_type = obj.get("object_type")
            object_name = obj.get("object_name")
            
            if object_type and object_name:
                # Create the extracted object
                extracted_object = {
                    "name": object_name,
                    "type": object_type,
                    "doc_id": doc_id,
                    "chunk_id_s": chunk_idx,
                    "chunk_id_e": chunk_idx
                }
                extracted_objects.append(extracted_object)

    return extracted_objects

def insert_objects(extracted_objects: List[Dict[str, Any]]):
    """
    Process chunks to extract objects and store them in Neo4j.
    
    Args:
        extracted_objects: List of objects to insert
    """
    result = []

    # Mapping of object types to their Neo4j labels
    type_to_label = {
        "definition": "Definition",
        "property": "Property", 
        "theorem": "Theorem",
        "lemma": "Lemma",
        "axiom": "Axiom",
        "corollary": "Corollary",
        "conjecture": "Conjecture",
        "example": "Example",
        "proof": "Proof",
        "other": "ImplicitKnowledge",
        "principle": "Principle",
        "fact": "Fact",
        "observation": "Observation",
        "method": "Method",
        "note": "Note"
    }
    
    for obj in extracted_objects:
        obj_type = obj["type"]
        if obj_type in type_to_label:
            result.append(add_knowledge_object(
                obj["name"], 
                type_to_label[obj_type],
                obj["doc_id"], 
                obj["chunk_id_s"], 
                obj["chunk_id_e"]
            ))
    
    return result

def make_study_object(chunks: List[Tuple[str, int]], doc_id: int, prompt_key: str = "general_textbook_prompt"):
    objects = extract_objects_from_chunks(chunks, doc_id, prompt_key)
    logger.info(f"Extracted {len(objects)} objects")

    object_nodes = insert_objects(objects)
    logger.info("Objects inserted successfully")

prompts_available = list(prompts.keys())

def price_approximation(chunks: List[str], prompt_key: str = "general_textbook_prompt", model_name: str = "gpt-5-nano"):
    input_tokens = 0
    for chunk in chunks:
        input_tokens += len(chunk) / 4
    input_tokens += len(prompts[prompt_key]) * len(chunks) / 4
    predicted_output_tokens = 0.508 * input_tokens + 251.692 # monte carlo prediction based on week worth of data
    input_price, completion_price = price_mapping[model_name]
    return input_tokens * input_price + predicted_output_tokens * completion_price
