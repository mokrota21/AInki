from .neo4j_graph import Node, driver, merge_repetition_state
from .repetition import RepeatState

def check_answer(node: Node, state_node: Node, correct_answer: bool):
    state = int(state_node['state'])
    if correct_answer:
        state += 1
    else:
        state = max(state - 1, 0)
    state = RepeatState(state)
    merge_repetition_state(node, state)