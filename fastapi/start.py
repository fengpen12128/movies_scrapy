import subprocess


def run_command(command):
    subprocess.run(command, shell=True, check=True)


def main():
    # 构建Docker镜像
    run_command("docker build -t movies_scrapy_fastapi .")

    # 检查是否存在同名容器，如果存在则停止并删除
    if subprocess.run("docker ps -aq -f name=movies_scrapy_fastapi", shell=True, capture_output=True, text=True).stdout.strip():
        run_command("docker stop movies_scrapy_fastapi")
        run_command("docker rm movies_scrapy_fastapi")

    # 运行新的容器，并挂载/root/download_data/
    run_command(
        "docker run -d --name movies_scrapy_fastapi --network host -v /root/download_data:/root/download_data movies_scrapy_fastapi")


if __name__ == "__main__":
    main()
