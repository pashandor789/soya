from typing import Annotated, Optional, List
from sqlalchemy import VARCHAR, create_engine, select, update, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import gen.task_service_pb2 as task_service_pb2


int_pk = Annotated[int, mapped_column(primary_key=True)]
text_not_null = Annotated[str, mapped_column(VARCHAR())]
text = Annotated[Optional[str], mapped_column(VARCHAR())]


class Base(DeclarativeBase):
    pass


class Tasks(Base):
    __tablename__ = "tasks"

    id: Mapped[int_pk]
    user_id: Mapped[int]
    title: Mapped[text]
    description: Mapped[text]


class Executor:
    def __init__(self, engine_config: str) -> None:
        self.engine = create_engine(engine_config)
        Base.metadata.create_all(self.engine)

    def create_task(self, params: list) -> int:
        provided_user_id, provided_title, provided_description = params[0], params[1], params[2]
        with Session(self.engine) as session:
            new_task = Tasks(user_id=provided_user_id,
                             title=provided_title, description=provided_description)
            session.add(new_task)
            session.commit()
            return new_task.id

    def update_task(self, params: list) -> bool:
        provided_id, provided_title, provided_description, provided_user_id = params[
            0], params[1], params[2], params[3]
        with Session(self.engine) as session:
            resulting_rows = session.scalars(
                select(Tasks).where(Tasks.id == provided_id)).one()
            session.commit()
            if resulting_rows.user_id != provided_user_id:
                return False
        with Session(self.engine) as session:
            session.execute(
                update(Tasks).where(Tasks.id == provided_id).values(title=provided_title,
                                                                    description=provided_description))
            session.commit()
        return True

    def delete_task(self, params: list) -> bool:
        provided_id, provided_user_id = params[0], params[1]
        with Session(self.engine) as session:
            resulting_rows = session.scalars(
                select(Tasks).where(Tasks.id == provided_id)).one()
            session.commit()
            if resulting_rows.user_id != provided_user_id:
                return False
        with Session(self.engine) as session:
            session.execute(delete(Tasks).where(Tasks.id == provided_id))
            session.commit()
        return True

    def get_task_by_id(self, id: int, provided_user_id: int):
        with Session(self.engine) as session:
            resulting_rows = session.scalars(
                select(Tasks).where(Tasks.id == id)).one()
            session.commit()
            if resulting_rows.user_id != provided_user_id:
                return None
            return resulting_rows

    def get_all_tasks(self, page_number: int, page_size: int):
        with Session(self.engine) as session:
            res = session.scalars(select(Tasks).limit(
                page_size).offset(page_number * page_size)).all()
            session.commit()
            final_result = []
            for elem in res:
                final_result.append(task_service_pb2.Task(id=elem.id, user_id=elem.user_id, title=elem.title,
                                                          description=elem.description))
            return final_result
