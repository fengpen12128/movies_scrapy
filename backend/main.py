from config import generate_full_urls
from file_download import FileDownloader  # Import the FileDownloader class
import time
from loguru import logger
import json
from scrapyd_api import ScrapydAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi import FastAPI, HTTPException, BackgroundTasks
import sys
import os
import requests

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到 Python 路径
sys.path.append(project_root)


app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，您可以根据需要限制特定域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# Scrapyd API 客户端
scrapyd = ScrapydAPI('http://localhost:6800')


class SpiderRequest(BaseModel):
    urls: list[dict]


@app.post("/run-spider")
async def api_run_spider(request: SpiderRequest):
    try:
        # 准备爬虫参数
        spider_name = 'javdb'
        project_name = 'movies_scrapy'

        # 生成 batch_id
        batch_id = int(time.time())

        # 将 URLs 列表转换为 JSON 字符串
        urls_json = json.dumps(request.urls)
        logger.info(f"Prepared urls_json: {urls_json}")

        # 调度爬虫任务
        task_id = scrapyd.schedule(
            project_name,
            spider_name,
            urls=urls_json,
            mode='temp',
            batch_id=batch_id
        )
        logger.info(f"Scheduled task with ID: {task_id}")

        # 返回任务 ID 和 batch_id
        return {
            "jobId": task_id,
            "batchId": str(batch_id)
        }
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/spider-status/{task_id}")
async def get_spider_status(task_id: str):
    try:
        project_name = 'movies_scrapy'
        jobs = scrapyd.list_jobs(project_name)

        # 检查运行中的任务
        for job in jobs['running']:
            if job['id'] == task_id:
                return {"task_id": task_id, "status": "running"}

        # 检查待处理的任务
        for job in jobs['pending']:
            if job['id'] == task_id:
                return {"task_id": task_id, "status": "pending"}

        # 检查已完成的任务
        for job in jobs['finished']:
            if job['id'] == task_id:
                return {"task_id": task_id, "status": "finished"}

        # 如果任务未找到
        return {"task_id": task_id, "status": "not_found"}

    except Exception as e:
        logger.error(f"Error occurred while checking status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/spider-log/{task_id}", response_class=PlainTextResponse)
async def get_spider_log(task_id: str):
    try:
        project_name = 'movies_scrapy'
        spider_name = 'javdb'
        log_url = f"http://localhost:6800/logs/{project_name}/{spider_name}/{task_id}.log"

        response = requests.get(log_url)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Log file not found")

        log_content = response.text
        return log_content
    except Exception as e:
        logger.error(f"Error occurred while fetching log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Welcome to the Movie Spider API"}


# 创建一个全局的 FileDownloader 实例
file_downloader = FileDownloader()


@app.post("/start-download-sync")
def start_download_sync():
    try:
        file_downloader = FileDownloader()
        file_downloader.start()
        return {"status": "completed", "message": "Download process completed"}
    except Exception as e:
        logger.error(f"Error occurred while starting download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start-download-async")
async def start_download_async(background_tasks: BackgroundTasks):
    try:
        file_downloader = FileDownloader()  # Reset the state before starting
        background_tasks.add_task(file_downloader.start)
        return {"status": "started", "message": "Download process started asynchronously"}
    except Exception as e:
        logger.error(f"Error occurred while starting download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-statistics")
async def get_download_statistics():
    try:
        stats = file_downloader.get_statistics()
        return stats
    except Exception as e:
        logger.error(
            f"Error occurred while fetching download statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scheduled-urls")
async def get_scheduled_urls():
    try:
        urls = generate_full_urls()
        return {"scheduledUrls": urls}
    except Exception as e:
        logger.error(f"Error occurred while fetching scheduled URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
