import scrapy
from ..actor_profile_parser import parser


class JavdbActorProfileSpider(scrapy.Spider):
    name = "javdb_actor_profile"
    allowed_domains = ["javdb.com"]

    def __init__(self, url_file='a.txt', *args, **kwargs):
        super(JavdbActorProfileSpider, self).__init__(*args, **kwargs)
        # 从文件读取URL列表
        with open(url_file, 'r', encoding='utf-8') as f:
            self.start_urls = [line.strip() for line in f if line.strip()]

    def parse(self, response):
        # 使用 actor_profile_parser 解析响应
        result = parser(response)
        yield result
