import os
import subprocess
import sys


def generate_grpc_code(protos):
    for proto in protos:
        if not os.path.exists(proto):
            print(f"No such file {proto}")
            sys.exit(1)

        os.makedirs("api_gateway/proto", exist_ok=True)
        os.makedirs("user_service/proto", exist_ok=True)

        try:
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "grpc_tools.protoc",
                    "-I./proto",
                    "--python_out=./api_gateway/proto",
                    "--grpc_python_out=./api_gateway/proto",
                    f"{proto}",
                ],
                check=True,
            )

            subprocess.run(
                [
                    "python3",
                    "-m",
                    "grpc_tools.protoc",
                    "-I./proto",
                    "--python_out=./user_service/proto",
                    "--grpc_python_out=./user_service/proto",
                    f"{proto}",
                ],
                check=True,
            )

        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    protos = list(sys.argv)[1:]
    generate_grpc_code(protos)
