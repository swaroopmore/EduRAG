class BM25Registry:

    def __init__(self):

        self.indexes = {}

    def get_key(
        self,
        user_id,
        subject_id,
    ):

        return (
            str(user_id),
            str(subject_id),
        )

    def has_index(
        self,
        user_id,
        subject_id,
    ):

        key = self.get_key(
            user_id,
            subject_id,
        )

        return key in self.indexes

    def get(
        self,
        user_id,
        subject_id,
    ):

        key = self.get_key(
            user_id,
            subject_id,
        )

        return self.indexes.get(key)

    def set(
        self,
        user_id,
        subject_id,
        index,
    ):

        key = self.get_key(
            user_id,
            subject_id,
        )

        self.indexes[key] = index