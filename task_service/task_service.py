from concurrent import futures

import grpc
import gen.task_service_pb2 as task_service_pb2
import gen.task_service_pb2_grpc as task_service_pb2_grpc

import database

sql_engine = database.Executor(
    "postgresql+psycopg2://postgres:password@taskdb:5432/postgres")


class TaskHolderServicer(task_service_pb2_grpc.TaskHolderServicer):
    def CreateTask(self, request, context):
        task_id = sql_engine.create_task(
            [request.user_id, request.title, request.description])
        return task_service_pb2.CreateTaskResponse(id=task_id)

    def UpdateTask(self, request, context):
        result = sql_engine.update_task(
            [request.id, request.title, request.description, request.user_id])
        return task_service_pb2.UpdateTaskResponse(success=result)

    def DeleteTask(self, request, context):
        result = sql_engine.delete_task([request.id, request.user_id])
        return task_service_pb2.DeleteTaskResponse(success=result)

    def GetTaskById(self, request, context):
        task = sql_engine.get_task_by_id(request.id, request.user_id)
        if not task:
            return task_service_pb2.Task()
        return task_service_pb2.Task(id=task.id, user_id=task.user_id, title=task.title, description=task.description)

    def GetAllTasks(self, request, context):
        result = sql_engine.get_all_tasks(
            request.page_number, request.page_size)
        return task_service_pb2.GetAllTasksResponse(tasks=result)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    task_service_pb2_grpc.add_TaskHolderServicer_to_server(
        TaskHolderServicer(), server)
    server.add_insecure_port("0.0.0.0:13000")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
