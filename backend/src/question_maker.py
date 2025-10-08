from langfuse.openai import AzureOpenAI
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from .neo4j_graph import add_review_question
from .repetition import RepeatState
from .neo4j_graph import merge_repetition_state
from tqdm import tqdm

load_dotenv()

client = AzureOpenAI()

question_types = {
    "Free Recall": "Ask the learner to recall everything they can about a topic without cues. "
                   "Forces active retrieval and strengthens long-term memory.",
    "Cued Recall": "Provide a partial cue or keyword (e.g., 'Explain how photosynthesis uses light energy'). "
                   "Retrieval is guided but still effortful.",
    "Elaborative Why/How": "Ask for explanations, causes, or mechanisms. Example: 'Why does increasing temperature speed up reactions?' "
                           "Promotes deep understanding and connection between ideas.",
    "Application/Transfer": "Pose a new scenario requiring application of learned material. "
                           "Example: 'How would Newton's laws apply on the Moon?' "
                           "Enhances flexible use of knowledge.",
    "Compare & Contrast": "Ask learners to identify similarities and differences. "
                          "Example: 'Compare classical conditioning and operant conditioning.' "
                          "Builds conceptual discrimination.",
    "Example/Non-Example": "Ask for examples and counterexamples of a concept. "
                           "Example: 'Give one example and one non-example of a democracy.' "
                           "Clarifies category boundaries.",
    "Prediction/Prequestion": "Ask a question before presenting new material. "
                              "Example: 'What do you think will happen if we double the dose?' "
                              "Primes attention and boosts later recall.",
    "Error Correction": "Provide a statement or solution that may be wrong and ask the learner to evaluate or correct it. "
                        "Encourages metacognition and consolidation through feedback.",
    "Metacognitive Reflection": "Ask learners to assess their own understanding or generate a question they still have. "
                                "Improves self-regulation and guides future study."
}

question_prompt = """
You are an expert mathematician and educational content designer.
Your goal is to generate several high-quality review questions based on the provided knowledge object.

Knowledge object:
- Name: {name}
- Type: {type}
- Reference text: {reference}

Question generation goals:
1. Reflect the key meaning, proof idea, or implications of the knowledge object.
2. Match the requested question type.
3. Encourage recall, reasoning, or application rather than rote repetition.
4. Use clear, formal mathematical language appropriate for advanced learners.

Question type: {question_type}
Question type description: {description}

Output format:
Return a single JSON-like dictionary with this structure:

{{
  "knowledge_name": "<string>",
  "knowledge_type": "<string>",
  "question_type": "<string>",
  "questions": [
    {{
      "id": 1,
      "question_text": "<string>",
      "difficulty": "<easy|medium|hard>",
      "cognitive_focus": "<recall|understanding|application|analysis>"
    }},
    ...
  ]
}}

Guidelines:
- Generate 3–5 questions.
- Vary the difficulty and cognitive focus across items.
- Do NOT include explanations or answers.
- Ensure the text of each question is self-contained and precise.
"""
completion_tokens = 10000
model_name = os.getenv("MODEL_NAME")
max_retries = 3
max_questions_per_type = 50

from .neo4j_connection import driver
from .chunk_maper import chunk_maper
import numpy as np

def sample_question_type(node_id: str):
    query = """
    MATCH (n:BookKnowledge)-[:QUESTION_FOR]->(q:ReviewQuestion)
    WHERE elementId(n) = $node_id
    RETURN q.type AS type, COUNT(q) AS total
    ORDER BY total DESC
    """
    result = driver.execute_query(query, node_id=node_id)
    question_types_count = {}
    for q_type in question_types.keys():
        question_types_count[q_type] = 0
    for type_key, total in result.records:
        if total >= max_questions_per_type:
            question_types_count.pop(type_key)
        else:
            question_types_count[type_key] = total

    # Make probabilities independent of each other
    types_ar = np.array(list(question_types_count.keys()))
    types_counts_ar = np.array(list(question_types_count.values()))
    if types_counts_ar.sum() == 0: # No questions generated yet
        return np.random.choice(types_ar)
    type_probability = 1 / (types_counts_ar * types_counts_ar)

    s = type_probability.sum()
    none_prob = 1 - s if s < 1 else 0

    type_probability = np.append(type_probability, none_prob)
    types_ar = np.append(types_ar, None)
    type_probability = type_probability / type_probability.sum()
    res =  np.random.choice(types_ar, p=type_probability)
    if res is None:
        return None
    res = res.item()
    return res

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_review_questions(node_id: str, question_type: str = None):
    if question_type is None:
        return None
    print(node_id, question_type)
    query = """
    MATCH (m)
    WHERE elementId(m) = $node_id
    RETURN m.name, m.type, m.chunk_id_s, m.chunk_id_e, m.doc_id
    """
    result = driver.execute_query(query, node_id=node_id)
    
    # Check if any records were returned
    if not result.records:
        logger.error(f"No node found with ID: {node_id}")
        return None
    
    name = result.records[0]["m.name"]
    type_knowledge = result.records[0]["m.type"]
    chunk_id_s = result.records[0]["m.chunk_id_s"]
    chunk_id_e = result.records[0]["m.chunk_id_e"]
    doc_id = result.records[0]["m.doc_id"]
    reference = chunk_maper(doc_id, chunk_id_s, chunk_id_e)

    # Get description from the dictionary
    if question_type not in question_types:
        logger.error(f"Question type '{question_type}' not found in question_types")
        return None
    
    description = question_types[question_type]
    question_result = None
    
    for _ in range(max_retries):
    
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert teacher. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": question_prompt.format(name=name, type=type_knowledge, reference=reference, question_type=question_type, description=description)
                }
            ],
            max_completion_tokens=completion_tokens,
            model=model_name
        )

        try:
            question_result = json.loads(response.choices[0].message.content)
            assert ["knowledge_name", "knowledge_type", "question_type", "questions"] == list(question_result.keys())
        except json.JSONDecodeError:
            pass
    if question_result is None:
        return None
    question_nodes = []
    for question in question_result["questions"]:
        question_node = add_review_question(node_id, question["question_text"], question_type, question["difficulty"], question["cognitive_focus"])
        question_nodes.append(question_node)
    return question_nodes
