import os
import subprocess
import sys


def generate_grpc_code(name: str, proto: str):
    if not os.path.exists(proto):
        print(f"No such file {proto}")
        sys.exit(1)

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
                f"--python_out=./{name}_service/proto",
                f"--grpc_python_out=./{name}_service/proto",
                f"{proto}",
            ],
            check=True,
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    os.makedirs("api_gateway/proto", exist_ok=True)
    os.makedirs("user_service/proto", exist_ok=True)
    os.makedirs("post_service/proto", exist_ok=True)
    os.makedirs("stats_service/proto", exist_ok=True)

    generate_grpc_code("user", "./proto/user.proto")
    generate_grpc_code("post", "./proto/post.proto")
    generate_grpc_code("stats", "./proto/stats.proto")
