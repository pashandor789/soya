gen_proto:
		mkdir -p gen
		cp ./task_service/proto/task_service.proto gen
		python3 -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. gen/task_service.proto

build_launch_services: gen_proto
		docker-compose build
		docker-compose up
