import asyncio
import os
from typing import List, Dict, Any
import aiohttp
from loguru import logger
import aiofiles
from download_utils import DownloadProgressTracker, DownloadStatisticsTracker
from psycopg2 import extras
from aiohttp_socks import ProxyConnector
import psycopg2
from enum import Enum


class DownloadStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FileDownloader:
    HEADERS = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36"
    }
    MAIN_STORAGE_PATH = '/Users/fengpan/Downloads/download_data'
    SEMAPHORE_LIMIT = 20
    CHUNK_SIZE = 8192

    def __init__(self):
        self.progress_tracker: DownloadProgressTracker = None
        self.stats_tracker = DownloadStatisticsTracker()
        self.status = DownloadStatus.NOT_STARTED

    async def download_image(self, url: str, filename: str, folder: str, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession) -> None:
        async with semaphore:
            try:
                self.progress_tracker.set_current_file(filename)

                async with session.get(url, ssl=False) as response:
                    folder_path = os.path.join(self.MAIN_STORAGE_PATH, folder)
                    os.makedirs(folder_path, exist_ok=True)
                    file_path = os.path.join(folder_path, filename)
                    size = 0

                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.CHUNK_SIZE):
                            size += len(chunk)
                            self.progress_tracker.update(0, len(chunk))
                            await f.write(chunk)

                self.progress_tracker.update(1, 0)
                self.stats_tracker.record_download(url, True, size)
            except Exception as e:
                logger.error(
                    f"Download failed {url} to {folder}/{filename}: {e}")
                self.progress_tracker.update(1, 0)
                self.stats_tracker.record_download(url, False, 0)

    async def start_download(self, task_config: List[Dict[str, str]]) -> None:
        semaphore = asyncio.Semaphore(self.SEMAPHORE_LIMIT)
        proxy_url = 'socks5://127.0.0.1:7890'
        connector = ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            tasks = [
                self.download_image(item['url'], os.path.basename(
                    item['url']), item['code'], semaphore, session)
                for item in task_config
            ]
            await asyncio.gather(*tasks)

        self.progress_tracker.close()
        self.stats_tracker.finish()
        self.stats_tracker.print_statistics()

    @staticmethod
    def get_postgresql_connection():
        try:
            postgres_config = {
                'host': '127.0.0.1',
                'port': 5432,
                'user': 'postgres',
                'password': 'admin123',
                'database': 'postgres'
            }

            connection = psycopg2.connect(**postgres_config)
            logger.info("Connected to PostgreSQL")

            return connection
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def reset(self):
        self.progress_tracker = None
        self.stats_tracker = DownloadStatisticsTracker()
        self.status = DownloadStatus.NOT_STARTED
        self.total_records = 0

    def start(self):
        self.reset()  # Reset the state before starting a new download
        self.status = DownloadStatus.IN_PROGRESS
        postgre_conn = self.get_postgresql_connection()

        with postgre_conn.cursor(cursor_factory=extras.DictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM download_urls WHERE status = 0 AND type = 1")
            rows = cursor.fetchall()

            # Convert rows to list of dictionaries
            source_data = [dict(row) for row in rows]

        self.progress_tracker = DownloadProgressTracker(len(source_data))
        self.total_records = len(source_data)
        logger.info(
            f'Starting download task with {len(source_data)} records...')
        asyncio.run(self.start_download(source_data))
        self.status = DownloadStatus.COMPLETED

    def get_statistics(self) -> Dict[str, Any]:
        stats = self.stats_tracker.get_statistics()
        stats['status'] = self.status.value
        stats['total_records'] = self.total_records
        if self.total_records > 0:
            stats['percent'] = int(
                (stats['success_count'] + stats['failure_count']) / self.total_records * 100)
        else:
            stats['percent'] = 0
        return stats


if __name__ == "__main__":
    downloader = FileDownloader()
    downloader.start()
