from datetime import timedelta
from neo4j.graph import Node
from datetime import datetime, timezone
tz = timezone.utc
BASE = timedelta(minutes=10)
l_boxes_ratios = [1, 2, 3, 1000, 10000]

class RepeatState:
    def __init__(self, userid: str, state: int = 0) -> None:
        self.state = min(state, len(l_boxes_ratios) - 1)
        self.userid = userid

    def get_state_val(self):
        return l_boxes_ratios[self.state] * BASE

    def get_next_repeat(self):
        return datetime.now(tz) + self.get_state_val()

    def get_all_states(self):
        return range(len(l_boxes_ratios))

    def set_state(self, state):
        self.state = min(state, len(l_boxes_ratios) - 1)
