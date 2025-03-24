import json
from pathlib import Path

class ConfigTool:
    def __init__(self, config_filename="config.json"):
        """初始化資料庫設定"""
        self.current_dir = Path(__file__).resolve().parent
        self.config_path = (self.current_dir.parent / config_filename).resolve()
        self._config_cache = None  # 用於快取設定

    def get_config(self):
        """讀取並回傳設定檔內容"""
        if self._config_cache is None:  # 只在第一次讀取
            try:
                with self.config_path.open(encoding="utf-8") as f:
                    self._config_cache = json.load(f)
            except FileNotFoundError:
                print(f"設定檔未找到: {self.config_path}")
                self._config_cache = {}
            except json.JSONDecodeError as e:
                print(f"設定檔解析錯誤: {e}")
                self._config_cache = {}
        return self._config_cache

    def get_value(self, key, default=None):
        """取得設定值，支援巢狀 key（如 'AppSettings.scheduleUrl'）"""
        keys = key.split(".")
        config = self.get_config()
        for k in keys:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return default
        return config
