from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, obj_id):
        return (
            self.db.query(self.model)
            .filter(self.model.id == obj_id)
            .first()
        )

    def get_all(self):
        return self.db.query(self.model).all()

    def create(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self):
        self.db.commit()

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()