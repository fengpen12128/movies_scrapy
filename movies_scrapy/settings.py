import os
import sys
BOT_NAME = "movies_scrapy"

SPIDER_MODULES = ["movies_scrapy.spiders"]
NEWSPIDER_MODULE = "movies_scrapy.spiders"


# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# 在 settings.py 中配置
RETRY_ENABLED = True  # 启用重试中间件
RETRY_TIMES = 3  # 每个请求的最大重试次数，即总共尝试 4 次（初次请求 + 3 次重试）
RETRY_HTTP_CODES = [500, 502, 503, 504, 522,
                    524, 408, 403, 429]  # 配置需要重试的 HTTP 状态码
RETRY_PRIORITY_ADJUST = -1  # 重试请求的优先级调整值

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32


# 设置每个请求之间的延迟（单位：秒）。这可以用来减慢爬虫的速度。
DOWNLOAD_DELAY = 0.5
# 置为 True 可以在 DOWNLOAD_DELAY 的基础上随机化延迟时间，使得每次请求的延迟时间不同。
RANDOMIZE_DOWNLOAD_DELAY = True
# Scrapy 应该达到的目标并发请求数。
AUTOTHROTTLE_TARGET_CONCURRENCY = 10.0

DOWNLOADER_MIDDLEWARES = {
    "movies_scrapy.middlewares.RandomUserAgentMiddleware": 100,
    "movies_scrapy.middlewares.RequestLoggingMiddleware": 200,
    # "movies_scrapy.middlewares.SaveHtmlMiddleware": 300,
    "movies_scrapy.middlewares.MinioUploadMiddleware": 400,
}


ITEM_PIPELINES = {
    # "movies_scrapy.pipelines.MongoPipeline": 1,
    #  "movies_scrapy.pipelines.CustomImageVideoPipeline": 2,
    "movies_scrapy.pipelines.PostgreSQLPipeline": 3,
    "movies_scrapy.pipelines.DownloadURLsPipeline": 4,
}


REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Redis configuration
REDIS_HOST = '192.168.31.19'
REDIS_PORT = 6379
REDIS_DB = 8
REDIS_KEY = 'javdb:scheduled_scrapyed_url'



SCRAPEOPS_API_KEY = 'a925fde0-def1-4452-90e1-4992687830d0'
USER_AGENT_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
USER_AGENT_ENABLE = True
NUM_RESULT = 50

SCRAPYAPI_KEY = '6a43fd4b7c5e2e043f2d0f1960768f39'

# LOG_LEVEL = 'DEBUG'
LOG_LEVEL = 'INFO'


DOWNLOAD_WARN_SIZE = 300 * 1024 * 1024  # 设置为100MB

# PostgreSQL settings
POSTGRES_DB = 'moviesApp'
POSTGRES_USER = 'admin'
POSTGRES_PASSWORD = 'admin123'
POSTGRES_HOST = '192.168.31.19'
POSTGRES_PORT = '5432'


MINIO_ENDPOINT = '192.168.31.19:20000'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'admin123'
MINIO_BUCKET = 'movies-html'
MINIO_SECURE = False


# 将项目根目录添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
