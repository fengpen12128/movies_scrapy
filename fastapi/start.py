import subprocess

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    output, error = process.communicate()
    return process.returncode, output, error

def main():
    # 构建Docker镜像
    print("Building Docker image...")
    returncode, output, error = run_command("docker build -t movies_scrapy_fastapi .")

    if returncode != 0:
        print("Docker image build failed. Please check the Dockerfile and try again.")
        print("Error:", error)
        return

    print("Docker image built successfully.")

    # 检查是否存在同名容器，如果存在则停止并删除
    returncode, output, error = run_command("docker ps -aq -f name=movies_scrapy_fastapi")
    if output.strip():
        print("Stopping and removing existing container...")
        run_command("docker stop movies_scrapy_fastapi")
        run_command("docker rm movies_scrapy_fastapi")

    # 运行新的容器
    print("Running new container...")
    returncode, output, error = run_command("docker run -d --name movies_scrapy_fastapi --network host movies_scrapy_fastapi")

    if returncode != 0:
        print("Failed to start the container. Please check the logs.")
        print("Error:", error)
        return

    # 检查容器是否成功运行
    returncode, output, error = run_command("docker ps -q -f name=movies_scrapy_fastapi")
    if output.strip():
        print("Container is running successfully.")
    else:
        print("Failed to start the container. Please check the logs.")

if __name__ == "__main__":
    main()
