"""
Session & Context Memory Manager for KSP Platform.
Preserves multi-turn conversation history and active slot entity states (district, crime type, year, case ID).
"""

class Session:
    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self.history = []  # List of {"role": "user"/"assistant", "content": "..."}
        self.active_slots = {
            "active_district": None,
            "active_crime_type": None,
            "active_year": None,
            "active_search_keywords": [],
            "active_ipc_sections": [],
            "active_accused_id": None,
            "active_case_no": None,
            "last_sql_executed": None
        }

    def add_turn(self, user_query: str, bot_answer: str, meta: dict = None):
        self.history.append({"role": "user", "content": user_query})
        self.history.append({"role": "assistant", "content": bot_answer})
        if len(self.history) > 12:
            self.history = self.history[-12:]  # Keep last 6 turns (12 messages)

    def update_slots(self, new_slots: dict):
        for k, v in new_slots.items():
            if v and k in self.active_slots:
                self.active_slots[k] = v

    def reset(self):
        self.history = []
        for k in self.active_slots:
            self.active_slots[k] = None if not isinstance(self.active_slots[k], list) else []


    def get_recent_history(self, n_turns: int = 4) -> list[dict]:
        return self.history[-(n_turns * 2):]

_session_store = {}

def get_session(session_id: str) -> Session:
    if session_id not in _session_store:
        _session_store[session_id] = Session(session_id)
    return _session_store[session_id]
