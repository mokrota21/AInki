from .neo4j_graph import Node, driver, merge_repetition_state
from .repetition import RepeatState

def check_answer(node: Node, correct_answer: bool):
    state_node = driver.execute_query(
        """
        MATCH (n)-[c:LAST_REPEATED]->(r:RepetitionState)
        WHERE elementId(n) = $node_id
        RETURN r
        """,
        node_id = node.element_id
    )
    state_node = state_node.records[0]["r"]
    state = int(state_node.get("state"))
    if correct_answer:
        state += 1
    else:
        state = max(state - 1, 0)
    state = RepeatState(state)
    merge_repetition_state(node, state)

