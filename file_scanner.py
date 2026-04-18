import os
import threading
import heapq
from send2trash import send2trash

class FileScanner:
    def __init__(self, finished_callback=None):
        self.finished_callback = finished_callback
        self._stop_event = threading.Event()
        self.largest_files = [] # Min-heap: elements are (size, path, timestamp)
        
    def start_scan(self, path="C:\\"):
        self._stop_event.clear()
        self.largest_files = []
        threading.Thread(target=self._scan, args=(path,), daemon=True).start()

    def stop_scan(self):
        self._stop_event.set()

    def _scan(self, start_path):
        try:
            self._scan_dir(start_path)
        except Exception as e:
            print(f"Scan error: {e}")
        
        # Sort largest files descending
        sorted_files = sorted(self.largest_files, key=lambda x: x[0], reverse=True)
        if self.finished_callback:
            self.finished_callback(sorted_files)

    def _scan_dir(self, current_path):
        if self._stop_event.is_set():
            return
            
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if self._stop_event.is_set():
                        break
                    try:
                        if entry.is_symlink():
                            continue
                            
                        if entry.is_file():
                            stat = entry.stat()
                            size = stat.st_size
                            if size > 0:
                                file_info = (size, entry.path, stat.st_mtime)
                                if len(self.largest_files) < 50:
                                    heapq.heappush(self.largest_files, file_info)
                                elif size > self.largest_files[0][0]:
                                    heapq.heapreplace(self.largest_files, file_info)
                        elif entry.is_dir():
                            self._scan_dir(entry.path)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass

    @staticmethod
    def delete_file(path, use_recycle_bin=False):
        try:
            if use_recycle_bin:
                send2trash(path)
            else:
                os.remove(path)
            return True, "File deleted successfully."
        except Exception as e:
            return False, str(e)
