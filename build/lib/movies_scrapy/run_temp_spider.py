import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.javdb import JavdbSpider
from config import temp_urls


def run_temp_spider(urls):
    # 更新 temp_urls
    temp_urls.clear()
    temp_urls.extend(urls)

    # 设置爬虫进程
    process = CrawlerProcess(get_project_settings())

    # 添加爬虫到进程，设置模式为 'temp'
    process.crawl(JavdbSpider, mode='temp')

    # 启动爬虫进程
    process.start()

# if __name__ == "__main__":
#     # 从命令行参数获取 URL
#     if len(sys.argv) < 2:
#         print("Usage: python run_temp_spider.py <url1> <max_pages1> [<url2> <max_pages2> ...]")
#         sys.exit(1)

#     # 解析命令行参数
#     urls = [(sys.argv[i], int(sys.argv[i+1])) for i in range(1, len(sys.argv), 2)]

#     # 运行临时爬虫
#     run_temp_spider(urls)


if __name__ == "__main__":

    # 解析命令行参数
    urls = [
        ('https://javdb.com/actors/qOA9', 2)
    ]

    # 运行临时爬虫
    run_temp_spider(urls)
