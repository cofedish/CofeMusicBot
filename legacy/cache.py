import os
from collections import OrderedDict

class LRUCache:
    """Реализуем LRU-кэш для хранения загруженных файлов."""
    def __init__(self, cache_dir, max_size_gb):
        self.cache = OrderedDict()  # трек ID -> путь к файлу
        self.cache_dir = cache_dir
        self.max_size = max_size_gb * 1024 * 1024 * 1024  # Размер в байтах
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_cache_size(self):
        """Возвращает текущий размер кэша в байтах."""
        total_size = 0
        for path in self.cache.values():
            if os.path.exists(path):
                total_size += os.path.getsize(path)
        return total_size

    def delete_lru(self):
        """Удаляет самый редко используемый файл (LRU)."""
        if self.cache:
            lru_item, path = self.cache.popitem(last=False)
            if os.path.exists(path):
                os.remove(path)
                print(f"Удален файл {path} (LRU кэш)")

    def add_to_cache(self, video_id, file_path):
        """Добавляем файл в кэш и удаляем старые файлы при превышении лимита."""
        self.cache[video_id] = file_path
        while self.get_cache_size() > self.max_size:
            self.delete_lru()
