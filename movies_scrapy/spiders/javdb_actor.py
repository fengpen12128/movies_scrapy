import scrapy
from loguru import logger
import os
import requests  # 新增导入


class JavdbActorSpider(scrapy.Spider):
    name = "javdb_actor"
    allowed_domains = ["javdb.com"]
    start_urls = ["https://javdb.com"]

    base_urls = [
        ('https://javdb.com/actors/censored', 30),
    ]

    def start_requests(self):
        for url, max_pages in self.base_urls:
            for page in range(1, max_pages + 1):
                yield scrapy.Request(f"{url}?page={page}", callback=self.parse)

    def parse(self, response):
        actors = response.xpath(
            '//div[@id="actors"]/div[@class="box actor-box"]')
        for actor in actors:
            img_src = actor.xpath('.//img/@src').get()
            a_title = actor.xpath('.//a/@title').get()
            strong_text = actor.xpath('.//strong/text()').get()

            if img_src and strong_text:
                strong_text = str(strong_text)
                self.download_image(img_src, strong_text.strip())

            print(img_src, a_title, strong_text)

    def download_image(self, url, filename):
        response = requests.get(url)
        if response.status_code == 200:
            with open(f"/root/movies_scrapy/actor_img/{filename}.jpg", 'wb') as f:
                f.write(response.content)
        else:
            logger.error(f"Failed to download image from {url}")
