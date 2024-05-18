FROM python:3.10

WORKDIR /auth_service
COPY auth_service .
COPY gen gen

RUN pip install -r req.txt

CMD ["python3", "app.py"]
