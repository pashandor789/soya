import database
from fastapi import Cookie, FastAPI, HTTPException, Response
from typing import Union
from pydantic import BaseModel
import uvicorn

from hashlib import sha256

from typing import Annotated
from fastapi.responses import JSONResponse

from http import HTTPStatus

import json
import grpc
from google.protobuf.json_format import MessageToJson
import gen.task_service_pb2 as task_service_pb2
import gen.task_service_pb2_grpc as task_service_pb2_grpc


class User(BaseModel):
    email: Union[str, None] = None
    phone_number: Union[str, None] = None
    login: str
    password: str
    name: Union[str, None] = None
    surname: Union[str, None] = None
    birth_date: Union[str, None] = None


class Task(BaseModel):
    id: Union[int, None] = None
    title: Union[str, None] = None
    description: Union[str, None] = None
    page_number: Union[int, None] = None
    page_size: Union[int, None] = None


app = FastAPI()
sql_engine = database.Executor(
    "postgresql+psycopg2://postgres:password@userdb:5432/postgres")
channel = grpc.insecure_channel(
    "task_service:13000", options=(('grpc.enable_http_proxy', 0),))
stub = task_service_pb2_grpc.TaskHolderStub(channel)


@app.post("/authorize")
def authorize(user_data: User, response: Response):
    if not user_data.login or not user_data.password:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No login or password provided in the body.")
    encrypted_password = sha256(user_data.password.encode('utf-8')).hexdigest()
    if not sql_engine.user_exists([user_data.login, encrypted_password]):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided login and password.")
    token = sql_engine.set_session_id([user_data.login, encrypted_password])
    response.set_cookie(key="token", value=token)


@app.put("/update")
def update_user(user_data: User, token: Annotated[str, Cookie()]):
    if not sql_engine.user_exists_with_session([token]):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided token.")
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
    if not user_data.login or not user_data.password:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No login or password provided in the body.")
    if sql_engine.user_exists([user_data.login, None]):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="User with such login already exists.")
    sql_engine.create_user([user_data.login, user_data.password])


@app.post("/create_task")
def create_task(task_data: Task, token: Annotated[str, Cookie()]):
    user_id = sql_engine.get_id_by_session(token)
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided token.")
    create_task_request = task_service_pb2.CreateTaskRequest(user_id=user_id, title=task_data.title,
                                                             description=task_data.description)
    create_task_response = stub.CreateTask(create_task_request)
    return JSONResponse(content=json.loads(MessageToJson(create_task_response)))


@app.put("/update_task")
def update_task(task_data: Task, token: Annotated[str, Cookie()]):
    user_id = sql_engine.get_id_by_session(token)
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided token.")
    update_task_request = task_service_pb2.UpdateTaskRequest(id=task_data.id, title=task_data.title,
                                                             description=task_data.description, user_id=user_id)
    update_task_response = stub.UpdateTask(update_task_request)
    return JSONResponse(content=json.loads(MessageToJson(update_task_response)))


@app.delete("/delete_task")
def delete_task(task_data: Task, token: Annotated[str, Cookie()]):
    user_id = sql_engine.get_id_by_session(token)
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided token.")
    delete_task_request = task_service_pb2.DeleteTaskRequest(
        id=task_data.id, user_id=user_id)
    delete_task_response = stub.DeleteTask(delete_task_request)
    return JSONResponse(content=json.loads(MessageToJson(delete_task_response)))


@app.get("/get_task")
def get_task_by_id(task_data: Task, token: Annotated[str, Cookie()]):
    user_id = sql_engine.get_id_by_session(token)
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided token.")
    get_task_by_id_request = task_service_pb2.GetTaskByIdRequest(
        id=task_data.id, user_id=user_id)
    get_task_by_id_response = stub.GetTaskById(get_task_by_id_request)
    return JSONResponse(content=json.loads(MessageToJson(get_task_by_id_response)))


@app.get("/get_all_tasks")
def get_all_tasks(task_data: Task, token: Annotated[str, Cookie()]):
    if not sql_engine.user_exists_with_session([token]):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST.value,
                            detail="No user with provided token.")
    get_all_tasks_request = task_service_pb2.GetAllTasksRequest(
        page_number=task_data.page_number, page_size=task_data.page_size)
    get_all_tasks_response = stub.GetAllTasks(get_all_tasks_request)
    return JSONResponse(content=json.loads(MessageToJson(get_all_tasks_response)))


if __name__ == "__main__":
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
