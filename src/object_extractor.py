from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
import json

load_dotenv()

model_name = os.getenv("MODEL_NAME")
client = AzureOpenAI()

def extract_objects_from_chunks(chunks: List[str], doc_id: int) -> List[Dict[str, Any]]:
    """
    Process chunks to extract definitions, theorems, and properties using OpenAI.
    
    Args:
        chunks: List of text chunks to process
        doc_id: Document ID for tracking
    
    Returns:
        List of extracted objects with their metadata
    """
    extracted_objects = []
    i = 0
    
    while i < len(chunks):
        current_chunk = chunks[i]
        
        # Ask if current chunk contains any mathematical objects
        object_detection_prompt = f"""
        Analyze the following text chunk and determine if it contains any of these mathematical objects:
        - Definition: A formal statement that explains the meaning of a term
        - Theorem: A statement that has been proven to be true
        - Lemma: A smaller result used to prove a larger theorem
        - Axiom: A fundamental assumption that is accepted without proof
        - Property: A characteristic or attribute of a mathematical object
        - Corollary: A direct consequence of a theorem
        - Conjecture: A statement that is believed to be true but not yet proven
        - Example: A specific instance illustrating a concept
        - Proof: A logical argument demonstrating the truth of a statement
        
        Text chunk:
        {current_chunk}
        
        Respond with a JSON object in this exact format:
        {{
            "contains_object": true/false,
            "object_type": "definition"/"theorem"/"lemma"/"axiom"/"property"/"corollary"/"conjecture"/"example"/"proof"/null,
            "object_name": "name of the object"/null
        }}
        
        If contains_object is false, set object_type and object_name to null.
        """
        
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
            max_completion_tokens=1000,
            model=model_name
        )
        
        try:
            detection_result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # If JSON parsing fails, skip this chunk
            i += 1
            continue
        
        if detection_result.get("contains_object", False):
            object_type = detection_result.get("object_type")
            object_name = detection_result.get("object_name")
            
            if object_type and object_name:
                # Found an object, now check for continuation in subsequent chunks
                chunk_id_s = i
                chunk_id_e = i
                
                # Check if next chunks are continuations
                j = i + 1
                while j < len(chunks):
                    continuation_prompt = f"""
                    The following text is a continuation of a {object_type} named "{object_name}":
                    
                    Previous context: {current_chunk}
                    
                    Current chunk to analyze: {chunks[j]}
                    
                    Determine if this current chunk is a continuation of the {object_type} "{object_name}".
                    
                    Respond with a JSON object in this exact format:
                    {{
                        "is_continuation": true/false
                    }}
                    """
                    
                    continuation_response = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert mathematician. Determine if text chunks are continuations of mathematical objects. Always respond with valid JSON."
                            },
                            {
                                "role": "user",
                                "content": continuation_prompt
                            }
                        ],
                        max_completion_tokens=100,
                        model=model_name
                    )
                    
                    try:
                        continuation_result = json.loads(continuation_response.choices[0].message.content)
                        if continuation_result.get("is_continuation", False):
                            chunk_id_e = j
                            j += 1
                        else:
                            break
                    except json.JSONDecodeError:
                        break
                
                # Create the extracted object
                extracted_object = {
                    "name": object_name,
                    "type": object_type,
                    "doc_id": doc_id,
                    "chunk_id_s": chunk_id_s,
                    "chunk_id_e": chunk_id_e
                }
                extracted_objects.append(extracted_object)
                
                # Move to the next unprocessed chunk
                i = chunk_id_e + 1
            else:
                i += 1
        else:
            i += 1
    
    return extracted_objects

def process_chunks_and_store(chunks: List[str], doc_id: int):
    """
    Process chunks to extract objects and store them in Neo4j.
    
    Args:
        chunks: List of text chunks to process
        doc_id: Document ID for tracking
    """
    from neo4j_graph import (
        add_definition, add_property, add_theorem, add_lemma, add_axiom,
        add_corollary, add_conjecture, add_example, add_proof
    )
    
    extracted_objects = extract_objects_from_chunks(chunks, doc_id)
    
    # Mapping of object types to their corresponding Neo4j functions
    type_to_function = {
        "definition": add_definition,
        "property": add_property,
        "theorem": add_theorem,
        "lemma": add_lemma,
        "axiom": add_axiom,
        "corollary": add_corollary,
        "conjecture": add_conjecture,
        "example": add_example,
        "proof": add_proof
    }
    
    for obj in extracted_objects:
        obj_type = obj["type"]
        if obj_type in type_to_function:
            type_to_function[obj_type](
                obj["name"], 
                obj["doc_id"], 
                obj["chunk_id_s"], 
                obj["chunk_id_e"]
            )
    
    return extracted_objects

