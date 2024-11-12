import scrapy
from scrapy import signals
import redis
from ..javdbparse_sp import javdb_parser
import os
import time
from ..config import scheduled_urls
import psycopg2
from datetime import datetime
import json
from psycopg2.extras import Json


class JavdbSpider(scrapy.Spider):
    name = "javdb"
    allowed_domains = ["javdb.com"]

    def __init__(self, *args, **kwargs):
        super(JavdbSpider, self).__init__(*args, **kwargs)
        self.mode = kwargs.get('mode', 'scheduled')
        self.batch_id = kwargs.get('batch_id', str(int(time.time())))
        self.crawl_params = kwargs
        self.logger.info(kwargs)  # Store all parameters
        if self.mode == 'temp':
            urls_list = kwargs.get('urls', '')
            urls_list = json.loads(urls_list)
            self.start_urls = [url_info['url'] for url_info in urls_list]
            self.max_pages = {
                url_info['url']: url_info['maxPage'] for url_info in urls_list}
            self.save_flags = {url_info['url']: url_info.get(
                'save', False) for url_info in urls_list}
        self.redis_cli = None
        self.redis_key = None
        self.db_connection = None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(JavdbSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)

        # Set up Redis client
        spider.redis_cli = redis.StrictRedis(
            host=crawler.settings.get('REDIS_HOST'),
            port=crawler.settings.get('REDIS_PORT'),
            db=crawler.settings.get('REDIS_DB')
        )
        spider.redis_key = crawler.settings.get('REDIS_KEY')

        return spider

    def spider_opened(self, spider):
        self.db_connection = psycopg2.connect(
            dbname=self.crawler.settings.get('POSTGRES_DB'),
            user=self.crawler.settings.get('POSTGRES_USER'),
            password=self.crawler.settings.get('POSTGRES_PASSWORD'),
            host=self.crawler.settings.get('POSTGRES_HOST'),
            port=self.crawler.settings.get('POSTGRES_PORT')
        )
        self.insert_crawl_start()

    def insert_crawl_start(self):
        try:
            with self.db_connection.cursor() as cursor:
                insert_query = """
                INSERT INTO crawl_stat (batch_id,job_id, started_time, crawl_params,execute_type)
                VALUES (%s, %s, %s,%s,%s);
                """
                self.logger.info(self.crawl_params)
                cursor.execute(insert_query, (self.batch_id, self.crawl_params['_job'],
                               datetime.now(), Json(self.crawl_params), self.mode))
                self.db_connection.commit()

                self.logger.info(
                    f"Crawl start recorded for batch_id: {self.batch_id}")
        except Exception as e:
            self.logger.error(f"Error inserting crawl start data: {e}")

    def spider_closed(self, spider):
        self.logger.info('Spider closed')
        stats = spider.crawler.stats.get_stats()
        total_time = stats.get('elapsed_time_seconds', 0)
        self.logger.info(f"Total time: {total_time} seconds")

        try:
            with self.db_connection.cursor() as cursor:
                update_query = """
                UPDATE crawl_stat
                SET  end_time = %s
                WHERE batch_id = %s;
                """
                cursor.execute(update_query, (datetime.now(), self.batch_id))
                self.db_connection.commit()
                self.logger.info(
                    f"Crawl end recorded for batch_id: {self.batch_id}")
        except Exception as e:
            self.logger.error(f"Error updating crawl end data: {e}")
        finally:
            if self.db_connection:
                self.db_connection.close()

    def start_requests(self):
        self.logger.info(f'batch_id: {self.batch_id}')
        self.logger.info(f'Crawling mode: {self.mode}')

        if self.mode == 'temp':
            urls_to_crawl = self.max_pages.items()
        else:
            urls_to_crawl = scheduled_urls

        for url, max_pages in urls_to_crawl:
            for page in range(1, max_pages + 1):
                yield scrapy.Request(f"{url}?page={page}&f=download&locale=en",
                                     callback=self.parse)

    def parse(self, response):
        detail_urls = response.xpath(
            '//div[@class="item"]/a[@class="box"]/@href').getall()
        for uri in detail_urls:
            count = self.redis_cli.hget(self.redis_key, uri)
            if count is None or int(count) <= 30:
                full_url = response.urljoin(uri)
                yield scrapy.Request(url=full_url, callback=self.parse_detail, meta={'is_detail_url': True})
            else:
                self.logger.info(f'Skipping already processed URI: {uri}')

    def parse_detail(self, response):
        uri = os.path.basename(response.url)
        item = javdb_parser(response.text, f'/v/{uri}')
        item['batch_id'] = self.batch_id

        # Check if release_date exists and is valids
        if 'release_date' in item and item['release_date']:
            try:
                release_date = datetime.strptime(
                    item['release_date'], '%Y-%m-%d')
                if release_date < datetime(2014, 1, 1):
                    self.logger.info(
                        f"Skipping item {item['code']} ==>  {item['release_date']}")
                    return  # Skip the item
                else:
                    yield item
            except ValueError:
                self.logger.warning(
                    f"Invalid release date format for {uri}: {item['release_date']}")
                return  # Skip the item if the date format is invalid
        else:
            self.logger.warning(f"No release date found for {uri}")
            return  # Skip the item if no release date is found
