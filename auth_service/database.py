from typing import Annotated, Optional, List
from sqlalchemy import VARCHAR, create_engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import uuid
from hashlib import sha256

int_pk = Annotated[int, mapped_column(primary_key=True)]
text_not_null = Annotated[str, mapped_column(VARCHAR())]
text = Annotated[Optional[str], mapped_column(VARCHAR())]


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int_pk]
    session: Mapped[Optional[uuid.UUID]]
    name: Mapped[text]
    surname: Mapped[text]
    birth_date: Mapped[text]
    email: Mapped[text]
    phone_number: Mapped[text]
    login: Mapped[text_not_null]
    password: Mapped[text_not_null]


class Executor:
    def __init__(self, engine_config: str) -> None:
        self.engine = create_engine(engine_config)
        Base.metadata.create_all(self.engine)

    def create_user(self, params: list[str]) -> None:
        provided_login, provided_password = params[0], params[1]
        with Session(self.engine) as session:
            new_user = Users(login=provided_login, password=sha256(provided_password.encode('utf-8')).hexdigest())
            session.add(new_user)
            session.commit()

    def user_exists(self, params: list[str]) -> bool:
        login, password = params[0], params

        with Session(self.engine) as session:
            command = select(Users).where(
                Users.login == login and Users.password == password)
            resulting_rows = session.scalars(command).all()

            session.commit()

        return len(resulting_rows) != 0

    def set_session_id(self, params: list) -> uuid:
        provided_login, provided_password = params[0], params[1]
        token = uuid.uuid4()
        with Session(self.engine) as session:
            session.execute(
                update(Users).where(Users.login == provided_login and Users.password == provided_password).values(
                    session=token))
            session.commit()
        return token

    def user_exists_with_session(self, params: list) -> bool:
        provided_token = params[0]
        with Session(self.engine) as session:
            resulting_rows = session.scalars(
                select(Users).where(Users.session == provided_token)).all()
            session.commit()
            return len(resulting_rows) > 0

    def get_id_by_session(self, token: str) -> int:
        with Session(self.engine) as session:
            resulting_rows = session.scalars(
                select(Users).where(Users.session == token)).one()
            session.commit()
            return resulting_rows.id

    def update_user(self, params: list[str]) -> None:
        login, password = params[0], params[1]
        name, surname, birth_date, email, phone_number = params[
            2], params[3], params[4], params[5], params[6]
        predicate = Users.login == login and Users.password == password

        with Session(self.engine) as session:
            session.execute(update(Users).where(predicate).values(
                name=name,
                surname=surname,
                birth_date=birth_date,
                email=email,
                phone_number=phone_number
            ))

            session.commit()
