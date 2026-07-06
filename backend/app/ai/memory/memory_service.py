class MemoryService:

    def __init__(self):
        self.memory = {}

    def get_history(self, user_id):

        return self.memory.get(str(user_id), [])

    def add_message(self, user_id, role, content):

        user_id = str(user_id)

        if user_id not in self.memory:
            self.memory[user_id] = []

        self.memory[user_id].append({
            "role": role,
            "content": content,
        })

        # Keep only last 10 messages
        self.memory[user_id] = self.memory[user_id][-10:]