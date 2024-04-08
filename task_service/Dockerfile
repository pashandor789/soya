FROM python:3.10

WORKDIR /task_service
COPY task_service .
COPY gen gen

RUN pip install -r req.txt

CMD ["python3", "task_service.py"]
