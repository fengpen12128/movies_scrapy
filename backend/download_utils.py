import time
import json
from datetime import datetime
import threading
from loguru import logger

from tqdm import tqdm
import psycopg2


class DownloadProgressTracker:
    def __init__(self, total_files):
        self.total_files = 0
        self.lock = threading.Lock()
        self.current_file = ""
        self.total_size = 0
        self.size_unit = 'B'
        self.formatted_size = ''
        self.progress_bar = tqdm(
            total=total_files, unit='file', desc='Downloading', ncols=100)

    def update(self, increment=1, file_size=0):
        with self.lock:
            self.progress_bar.update(increment)
            self.total_size += file_size
            self._update_size_unit()
            self._update_description()

    def set_current_file(self, filename):
        with self.lock:
            self.current_file = filename
            self._update_description()

    def _update_size_unit(self):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = self.total_size
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        self.size_unit = units[unit_index]
        self.formatted_size = f"{size:.2f}"

    def _update_description(self):
        self.progress_bar.set_postfix_str(
            f'Current: {self.current_file} | Total: {self.formatted_size} {self.size_unit}'
        )

    def close(self):
        self.progress_bar.close()


class DownloadStatisticsTracker:
    def __init__(self):
        self.start_time = time.time()
        self.end_time = None
        self.success_count = 0
        self.failure_count = 0
        self.total_size = 0
        self.db_connection = self._get_postgresql_connection()

    def _get_postgresql_connection(self):
        try:
            postgres_config = {
                'host': '192.168.1.22',
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

    def record_download(self, url, success, size):
        with self.db_connection.cursor() as cursor:
            if success:
                self.record_success()
                cursor.execute(
                    "UPDATE download_urls SET status = 1, size = %s WHERE url = %s",
                    (size, url)
                )
            else:
                self.record_failure()
                cursor.execute(
                    "UPDATE download_urls SET status = -1, size = %s WHERE url = %s",
                    (size, url)
                )
            self.db_connection.commit()
        self.record_size(size)

    def record_success(self):
        self.success_count += 1

    def record_failure(self):
        self.failure_count += 1

    def record_size(self, size):
        self.total_size += size

    def finish(self):
        self.end_time = time.time()

    @staticmethod
    def _format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def get_statistics(self):
        return {
            'total_size_str': self._format_size(self.total_size),
            'total_size': str(self.total_size),
            "start_time": datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.fromtimestamp(self.end_time).strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "duration": round(self.end_time - self.start_time, 2) if self.end_time else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_count": self.success_count + self.failure_count
        }

    def print_statistics(self):
        stats = self.get_statistics()
        print(json.dumps(stats, indent=4))
