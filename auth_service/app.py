import database
from fastapi import FastAPI, HTTPException
from typing import Union
from pydantic import BaseModel
import uvicorn


class User(BaseModel):
    email: Union[str, None] = None
    phone_number: Union[str, None] = None
    login: str
    password: str
    name: Union[str, None] = None
    surname: Union[str, None] = None
    birth_date: Union[str, None] = None


app = FastAPI()
sql_engine = database.Executor("postgresql+psycopg2://postgres:password@db:5432/postgres")


@app.post("/authorize")
def authorize(user_data: User):
    if not sql_engine.user_exists([user_data.login, user_data.password]):
        raise HTTPException(status_code=404, detail="Wrong user data!")
    sql_engine.set_session_id([user_data.login, user_data.password])


@app.put("/update")
def update(user_data: User):
    user_list = [
        user_data.login,
        user_data.password,
        user_data.name, 
        user_data.surname,
        user_data.birth_date,
        user_data.email,
        user_data.phone_number
    ]

    sql_engine.update_user(user_list)


@app.post("/registry")
def create_user(user_data: User):
    sql_engine.create_user([user_data.login, user_data.password])


if __name__ == "__main__":
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
