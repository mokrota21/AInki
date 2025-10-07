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

client = AzureOpenAI()

question_types = [
    {
        "type": "Free Recall",
        "description": "Ask the learner to recall everything they can about a topic without cues. "
                       "Forces active retrieval and strengthens long-term memory."
    },
    {
        "type": "Cued Recall",
        "description": "Provide a partial cue or keyword (e.g., 'Explain how photosynthesis uses light energy'). "
                       "Retrieval is guided but still effortful."
    },
    {
        "type": "Elaborative Why/How",
        "description": "Ask for explanations, causes, or mechanisms. Example: 'Why does increasing temperature speed up reactions?' "
                       "Promotes deep understanding and connection between ideas."
    },
    {
        "type": "Application/Transfer",
        "description": "Pose a new scenario requiring application of learned material. "
                       "Example: 'How would Newton’s laws apply on the Moon?' "
                       "Enhances flexible use of knowledge."
    },
    {
        "type": "Compare & Contrast",
        "description": "Ask learners to identify similarities and differences. "
                       "Example: 'Compare classical conditioning and operant conditioning.' "
                       "Builds conceptual discrimination."
    },
    {
        "type": "Example/Non-Example",
        "description": "Ask for examples and counterexamples of a concept. "
                       "Example: 'Give one example and one non-example of a democracy.' "
                       "Clarifies category boundaries."
    },
    {
        "type": "Prediction/Prequestion",
        "description": "Ask a question before presenting new material. "
                       "Example: 'What do you think will happen if we double the dose?' "
                       "Primes attention and boosts later recall."
    },
    {
        "type": "Error Correction",
        "description": "Provide a statement or solution that may be wrong and ask the learner to evaluate or correct it. "
                       "Encourages metacognition and consolidation through feedback."
    },
    {
        "type": "Metacognitive Reflection",
        "description": "Ask learners to assess their own understanding or generate a question they still have. "
                       "Improves self-regulation and guides future study."
    }
]

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

{
  "knowledge_name": "<string>",
  "knowledge_type": "<string>",
  "question_type": "<string>",
  "questions": [
    {
      "id": 1,
      "question_text": "<string>",
      "difficulty": "<easy|medium|hard>",
      "cognitive_focus": "<recall|understanding|application|analysis>"
    },
    ...
  ]
}

Guidelines:
- Generate 3–5 questions.
- Vary the difficulty and cognitive focus across items.
- Do NOT include explanations or answers.
- Ensure the text of each question is self-contained and precise.
"""
completion_tokens = 10000
model_name = os.getenv("MODEL_NAME")
max_retries = 3

from .neo4j_connection import driver
from .chunk_maper import chunk_maper

def make_review_question(node_id: str, question_type: str):
    query = """
    MATCH (m:BookKnowledge {id: $node_id})
    RETURN m.name, m.type, m.chunk_id_s, m.chunk_id_e, m.doc_id
    """
    result = driver.execute_query(query, node_id=node_id)
    name = result.records[0]["m.name"]
    type = result.records[0]["m.type"]
    chunk_id_s = result.records[0]["m.chunk_id_s"]
    chunk_id_e = result.records[0]["m.chunk_id_e"]
    doc_id = result.records[0]["m.doc_id"]
    reference = chunk_maper(doc_id, chunk_id_s, chunk_id_e)

    description = question_types[question_type]["description"]
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
                    "content": question_prompt.format(name=name, type=type, reference=reference, question_type=question_type, description=description)
                }
            ],
            max_completion_tokens=completion_tokens,
            model=model_name
        )

        try:
            question_result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            pass
    return question_result