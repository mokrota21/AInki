from .neo4j_graph import Node, driver, merge_repetition_state
from .repetition import RepeatState
from pydantic import BaseModel

class QuizAnswer(BaseModel):
    node_id: str
    correct: bool

def check_answer(answer: QuizAnswer):
    state_node = driver.execute_query(
        """
        MATCH (n)-[c:LAST_REPEATED]->(r:RepetitionState)
        WHERE elementId(n) = $node_id
        RETURN r
        """,
        node_id = answer.node_id
    )
    state_node = state_node.records[0]["r"]
    state = int(state_node.get("state"))
    if answer.correct:
        state += 1
    else:
        state = max(state - 1, 0)
    state = RepeatState(state_node.get("userid"), state)
    merge_repetition_state(answer.node_id, state)

