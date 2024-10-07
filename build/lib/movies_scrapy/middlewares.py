
import random
from urllib.parse import urlparse
import os
import redis
import hashlib


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
    def __init__(self, redis_host, redis_port, redis_db, redis_key):
        self.redis_cli = redis.StrictRedis(
            host=redis_host, port=redis_port, db=redis_db)
        self.redis_key = redis_key
        self.save_path = '/Users/fengpan/Downloads/saved_html'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get('REDIS_HOST'),
            redis_port=crawler.settings.get('REDIS_PORT'),
            redis_db=crawler.settings.get('REDIS_DB'),
            redis_key=crawler.settings.get('REDIS_KEY')
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