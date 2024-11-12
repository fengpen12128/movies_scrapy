import random
from urllib.parse import urlparse
import os
import redis
import hashlib
from minio import Minio
from minio.error import S3Error
import io


class RandomUserAgentMiddleware():
    def __init__(self):
        self.user_agents = ['Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)',
                            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2',
                            'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1']

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.user_agents)
        return None


class RequestLoggingMiddleware:
    def process_request(self, request, spider):
        spider.logger.info(f"Request : {request.url}")
        return None


class SaveHtmlMiddleware:
    def __init__(self, redis_host, redis_port, redis_db, redis_key, save_path):
        self.redis_cli = redis.StrictRedis(
            host=redis_host, port=redis_port, db=redis_db)
        self.redis_key = redis_key
        self.save_path = save_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get('REDIS_HOST'),
            redis_port=crawler.settings.get('REDIS_PORT'),
            redis_db=crawler.settings.get('REDIS_DB'),
            redis_key=crawler.settings.get('REDIS_KEY'),
            save_path=crawler.settings.get('HTML_STORE')
        )

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        if not request.meta.get('is_detail_url', False):
            return response

        parsed_url = urlparse(response.url)
        url_path = parsed_url.path

        try:
            file_name = self._generate_file_name(url_path)
            self._save_html_content(response.body, file_name)
            self.redis_cli.hincrby(self.redis_key, url_path, 1)
        except Exception as e:
            spider.logger.error(f"Error saving HTML: {e}")
            # self.redis_cli.srem(self.redis_key, url_path)

        return response

    def _generate_file_name(self, url_path):
        file_name = url_path.replace(
            '/', '_') or str(random.randint(1000000, 9999999))
        hashed_name = hashlib.sha256(file_name.encode()).hexdigest()[:8]
        return f'{hashed_name}@{file_name}.html'

    def _save_html_content(self, content, file_name):
        file_path = os.path.join(self.save_path, file_name)
        with open(file_path, 'wb') as f:
            f.write(content)


class MinioUploadMiddleware:
    def __init__(self, minio_endpoint, minio_access_key, minio_secret_key,
                 minio_bucket, redis_host, redis_port, redis_db, redis_key, secure=False):
        self.minio_client = Minio(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=secure
        )
        self.bucket = minio_bucket
        self.redis_cli = redis.StrictRedis(
            host=redis_host, port=redis_port, db=redis_db)
        self.redis_key = redis_key

        # 确保 bucket 存在
        if not self.minio_client.bucket_exists(self.bucket):
            self.minio_client.make_bucket(self.bucket)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            minio_endpoint=crawler.settings.get('MINIO_ENDPOINT'),
            minio_access_key=crawler.settings.get('MINIO_ACCESS_KEY'),
            minio_secret_key=crawler.settings.get('MINIO_SECRET_KEY'),
            minio_bucket=crawler.settings.get('MINIO_BUCKET'),
            redis_host=crawler.settings.get('REDIS_HOST'),
            redis_port=crawler.settings.get('REDIS_PORT'),
            redis_db=crawler.settings.get('REDIS_DB'),
            redis_key=crawler.settings.get('REDIS_KEY'),
            secure=crawler.settings.getbool('MINIO_SECURE', False)
        )

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        if not request.meta.get('is_detail_url', False):
            return response

        parsed_url = urlparse(response.url)
        url_path = parsed_url.path

        try:
            file_name = self._generate_file_name(url_path)
            self._upload_to_minio(response.body, file_name)
            self.redis_cli.hincrby(self.redis_key, url_path, 1)
        except Exception as e:
            spider.logger.error(f"Error uploading to MinIO: {e}")

        return response

    def _generate_file_name(self, url_path):
        file_name = url_path.replace(
            '/', '_') or str(random.randint(1000000, 9999999))
        hashed_name = hashlib.sha256(file_name.encode()).hexdigest()[:8]
        return f'{hashed_name}@{file_name}.html'

    def _upload_to_minio(self, content, file_name):
        content_bytes = io.BytesIO(content)
        content_bytes.seek(0)
        self.minio_client.put_object(
            bucket_name=self.bucket,
            object_name=file_name,
            data=content_bytes,
            length=len(content),
            content_type='text/html'
        )
