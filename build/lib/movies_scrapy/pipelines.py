import scrapy
import os
from scrapy.pipelines.files import FilesPipeline
import pymongo
from datetime import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json


class CustomImageVideoPipeline(FilesPipeline):
    total_download_size = 0  # 新增变量用于统计下载总大小

    def get_media_requests(self, item, info):
        if item.get('has_downloaded', False):
            return []

        image_urls = [item['url']
                      for item in item.get('media_urls', []) if item['type'] != 3]
        video_urls = [f"http:{item['url']}" if not item['url'].startswith(
            'http') else item['url'] for item in item.get('media_urls', []) if item['type'] == 3]

        urls = image_urls
        return [scrapy.Request(u) for u in urls]

    def file_path(self, request, response=None, info=None, *, item=None):
        # 自定义文件保存路径
        code = item.get('code', '')
        file_name = os.path.basename(request.url)
        return f'{code}/{file_name}'

    def item_completed(self, results, item, info):
        if item.get('has_downloaded', False):
            return []
        # 统计下载的文件大小
        for ok, result in results:
            if ok:
                file_size = f'/root/download_data/{result["path"]}'  # 获取文件路径
                total_size = os.path.getsize(file_size)  # 获取文件大小
                CustomImageVideoPipeline.total_download_size += total_size  # 累加到总大小
        return item


class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        self.db = None
        self.client = None
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'py_crawal'),
            mongo_collection=crawler.settings.get(
                'MONGO_COLLECTION', 'movies_test')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        collection = self.db[self.mongo_collection]
        code = item.get('code')
        if code:
            existing_record = collection.find_one({'code': code})
            save_data = dict(item)

            if existing_record:
                save_data['updated_time'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                save_data['created_time'] = existing_record['created_time']
                collection.update_one({'_id': existing_record['_id']}, {
                                      '$set': save_data})
                spider.logger.info(f"mongo 存在 {code}, 执行更新")
                item['has_downloaded'] = True
            else:
                save_data['created_time'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                collection.insert_one(save_data)
        return item


class PostgreSQLPipeline:
    def __init__(self, db_params):
        self.db_params = db_params
        self.conn = None
        self.cur = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_params={
                'dbname': crawler.settings.get('POSTGRES_DB'),
                'user': crawler.settings.get('POSTGRES_USER'),
                'password': crawler.settings.get('POSTGRES_PASSWORD'),
                'host': crawler.settings.get('POSTGRES_HOST'),
                'port': crawler.settings.get('POSTGRES_PORT')
            }
        )

    def open_spider(self, spider):
        self.conn = psycopg2.connect(**self.db_params)
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        if not item.get('code'):
            return item

        code = item.get('code')
        save_data = dict(item)

        # Check if the record already exists
        self.cur.execute(
            "SELECT id, created_time FROM crawl_source_data WHERE code = %s", (code,))
        existing_record = self.cur.fetchone()

        if existing_record:
            # Update existing record
            created_time = existing_record[1]
            save_data['created_time'] = created_time
            save_data['updated_time'] = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')
            update_query = sql.SQL("""
                UPDATE crawl_source_data
                SET data = %s
                WHERE id = %s
            """)
            self.cur.execute(
                update_query, (Json(save_data), existing_record[0]))
            spider.logger.info(f"postgresql 存在 {code}, 执行更新")
            item['has_downloaded'] = True
        else:
            # Insert new record
            insert_query = sql.SQL("""
                INSERT INTO crawl_source_data (data)
                VALUES (%s)
            """)
            save_data['created_time'] = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')
            self.cur.execute(insert_query, (Json(save_data),))

        self.conn.commit()
        return item


class DownloadURLsPipeline:
    def __init__(self, db_params):
        self.db_params = db_params
        self.conn = None
        self.cur = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_params={
                'dbname': crawler.settings.get('POSTGRES_DB'),
                'user': crawler.settings.get('POSTGRES_USER'),
                'password': crawler.settings.get('POSTGRES_PASSWORD'),
                'host': crawler.settings.get('POSTGRES_HOST'),
                'port': crawler.settings.get('POSTGRES_PORT')
            }
        )

    def open_spider(self, spider):
        self.conn = psycopg2.connect(**self.db_params)
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        if not item.get('code') or item.get('has_downloaded', False):
            return item

        batch_id = item.get('batch_id')
        code = item.get('code')
        media_urls = item.get('media_urls', [])

        insert_query = sql.SQL("""
            INSERT INTO download_urls (batch_id, url, code, type)
            VALUES %s
        """)

        values = [
            (batch_id, media_url.get('url'), code, int(media_url.get('type')))
            for media_url in media_urls
        ]

        if values:
            from psycopg2.extras import execute_values
            execute_values(self.cur, insert_query, values)
            self.conn.commit()

        return item
