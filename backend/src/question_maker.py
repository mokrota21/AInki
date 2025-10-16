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
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This makes it show in terminal
    ]
)

logger = logging.getLogger(__name__)
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
You are an expert educational content designer.
Your task is to generate short, high-quality review questions based on the provided knowledge object.

Knowledge object:
- Name: {name}
- Type: {type}
- Reference text: {reference}

Question generation goals:
1. Focus on the core concept or reasoning described in the reference text.
2. Do NOT use undefined symbols, variables, or notation (e.g., n, m, f(x)).
   - Instead, restate them in plain language (e.g., "a number", "a function", "two quantities").
3. Ensure each question is self-contained and understandable to a learner who has not seen the reference.
4. Keep questions and answers short, clear, and educational.
5. Use precise and general mathematical or conceptual language rather than copied text.
6. Match the intent of the given question type, but simplify if it becomes overly complex.
7. Focus on understanding and reasoning, not rote recall.

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
      "answer": "<string>",
      "cognitive_focus": "<understanding|application|analysis>"
    }}
  ]
}}

Guidelines:
- Generate exactly 1 question.
- Keep both question and answer concise.
- Rephrase any symbolic or contextual references into general descriptive terms.
- Ensure learners can understand and answer without access to the original text.
- Use consistent, accessible terminology that communicates meaning clearly.
"""


completion_tokens = 10000
model_name = os.getenv("MODEL_NAME")
max_retries = 3
max_questions_per_type = 1
max_questions_per_node = 1

from .neo4j_connection import driver
from .chunk_maper import chunk_maper
import numpy as np

# TODO: Check this
def sample_question_type(node_id: str):
    query = """
    MATCH (q:ReviewQuestion)-[:QUESTION_FOR]->(n)
    WHERE elementId(n) = $node_id
    RETURN q.type AS type, COUNT(q) AS total
    """
    result = driver.execute_query(query, node_id=node_id)

    # Initialize counts for all types; drop types at per-type cap
    question_types_count = {q_type: 0 for q_type in question_types.keys()}
    total_questions = 0

    for record in result.records:
        type_key = record["type"]
        total = record["total"]
        total_questions += total
        if total >= max_questions_per_type:
            question_types_count.pop(type_key, None)
        else:
            question_types_count[type_key] = total
    # logger.info(f"Question types count: {question_types_count}")
    # logger.info(f"Total questions: {total_questions}")
    # logger.info(f"Question types: {question_types_count}")
    # Enforce per-node cap
    if total_questions >= max_questions_per_node:
        return None

    # If no types remain under the per-type cap, do not generate
    if not question_types_count:
        return None

    types_ar = np.array(list(question_types_count.keys()))
    types_counts_ar = np.array(list(question_types_count.values()), dtype=float)
    logger.info(f"Types: {types_ar}, Types counts: {types_counts_ar}")

    # If none generated yet for any remaining type -> uniform choice
    if types_counts_ar.sum() == 0:
        logger.info(f"No types generated yet for any remaining type -> uniform choice")
        res = np.random.choice(types_ar)
        return res.item() if hasattr(res, "item") else res

    # Favor underrepresented types; avoid division by zero
    type_weights = 1.0 / ((types_counts_ar + 1.0) ** 2)

    # Increase skip probability as we approach the node limit
    remaining_slots = max(0, max_questions_per_node - total_questions)
    none_prob = max(0.0, 1.0 - (remaining_slots / float(max_questions_per_node)))

    probs = np.append(type_weights, none_prob)
    choices = np.append(types_ar, None)

    if probs.sum() == 0:
        res = np.random.choice(types_ar)
        return res.item() if hasattr(res, "item") else res

    probs = probs / probs.sum()
    res = np.random.choice(choices, p=probs)
    if res is None:
        return None
    return res.item() if hasattr(res, "item") else res

def make_review_questions(node_id: str, question_type: str = None):
    if question_type is None:
        return None
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
        question_node = add_review_question(node_id, question["question_text"], question_type, question["cognitive_focus"], question["answer"])
        question_nodes.append(question_node)
    return question_nodes
