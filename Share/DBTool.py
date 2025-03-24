import json
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.schema import CreateTable
import math
import datetime

class DBTool:
    def __init__(self, config_path="config.json"):
        """初始化資料庫設定"""
        # 設定 config.json 的絕對路徑（專案根目錄的上一層）
        self.current_dir = Path(__file__).resolve().parent
        self.config_path =(self.current_dir.parent / "config.json").resolve()
        self.engine = self.get_connection()

    def load_config(self):
        """讀取 JSON 設定檔"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()
            config = json.loads(content)
            return config
        except FileNotFoundError:
            print("設定檔未找到，請確認 'config.json' 是否存在")
            return None
        except json.JSONDecodeError:
            print("設定檔 JSON 格式錯誤")
            return None

    def get_connection(self, connection_name="Default"):
        """取得 MSSQL 連線"""
        config = self.load_config()
        if not config:
            return None

        if connection_name in config["ConnectionSetting"]:
            conn_str = config["ConnectionSetting"][connection_name]
            engine = create_engine(conn_str)
            return engine
        else:
            print(f"找不到指定的連線名稱: {connection_name}")
            return None

    def execute_query(self, sql, params=None, fetch_one=False):
        """
        執行 SQL 指令，並可帶入參數
        :param sql: SQL 指令 (支援 SELECT, INSERT, UPDATE, DELETE)
        :param params: SQL 參數 (dict)
        :param fetch_one: 是否只取回單筆資料 (預設為 False)
        :return: 結果集 (list 或 dict)
        """
        if not self.engine:
            print("資料庫連線未建立，無法執行 SQL")
            return None

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})

                if sql.strip().lower().startswith("select"):
                    data = result.mappings().all()
                    return data[0] if fetch_one else data
                else:
                    conn.commit()
                    return result.rowcount  # 回傳影響的資料筆數 (INSERT/UPDATE/DELETE)

        except Exception as e:
            print(f"執行 SQL 時發生錯誤: {e}")
            return None

    def create_table(self, table):
        """
        建立資料表，可接受 Table 物件或 SQL Script
        :param table: SQLAlchemy Table 物件 或 SQL 指令字串
        """
        if not self.engine:
            print("資料庫連線未建立，無法建立表格")
            return None

        try:
            with self.engine.connect() as conn:
                if isinstance(table, Table):
                    # 若傳入的是 SQLAlchemy Table 物件，則建立表格
                    metadata = MetaData()
                    table.metadata = metadata
                    metadata.create_all(self.engine)
                    print(f"表格 {table.name} 建立成功")
                elif isinstance(table, str):
                    # 若傳入的是 SQL Script，則執行 SQL 指令
                    conn.execute(text(table))
                    conn.commit()
                    print("表格建立成功")
                else:
                    print("參數錯誤，請提供 Table 物件或 SQL 指令")
        except Exception as e:
            print(f"建立表格時發生錯誤: {e}")

    def insert(self, table_name, data):
        """插入資料"""
        columns = ", ".join(data.keys())
        values = ", ".join([f":{key}" for key in data.keys()])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
        return self.execute_query(sql, data)

    def update(self, table_name, data, condition):
        """更新資料"""
        set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
        condition_clause = " AND ".join([f"{key} = :{key}" for key in condition.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition_clause}"
        return self.execute_query(sql, {**data, **condition})

    def delete(self, table_name, condition):
        """刪除資料"""
        condition_clause = " AND ".join([f"{key} = :{key}" for key in condition.keys()])
        sql = f"DELETE FROM {table_name} WHERE {condition_clause}"
        return self.execute_query(sql, condition)

    def select(self, table_name, condition=None, fetch_one=False):
        """查詢資料"""
        where_clause = ""
        params = {}

        if condition:
            where_clause = "WHERE " + " AND ".join([f"{key} = :{key}" for key in condition.keys()])
            params = condition

        sql = f"SELECT * FROM {table_name} {where_clause}"
        return self.execute_query(sql, params, fetch_one)

    def generate_create_table_sql(self, table):
        """ 產生 `CREATE TABLE` SQL Script """
        if not isinstance(table, Table):
            print("請提供 SQLAlchemy Table 物件")
            return None
        return str(CreateTable(table).compile(self.engine))

    def generate_insert_sql(self, table_name, data):
        """ 產生 `INSERT INTO` SQL Script，並包含實際數值 """
        data = self.__replace_nan_with_null(data)  # 轉換 NaN 為 None
        columns = ", ".join(data.keys())
        values = ", ".join([self.__format_value(value) for value in data.values()])
        return f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

    def generate_update_sql(self, table_name, data, condition):
        """ 產生 `UPDATE` SQL Script，並包含實際數值 """
        data = self.__replace_nan_with_null(data)  # 轉換 NaN 為 None
        condition = self.__replace_nan_with_null(condition)  # 轉換 NaN 為 None
        set_clause = ", ".join([f"{key} = {self.__format_value(value)}" for key, value in data.items()])
        condition_clause = " AND ".join([f"{key} = {self.__format_value(value)}" for key, value in condition.items()])
        return f"UPDATE {table_name} SET {set_clause} WHERE {condition_clause}"

    def generate_delete_sql(self, table_name, condition):
        """ 產生 `DELETE` SQL Script，並直接帶入數值 """
        condition = self.__replace_nan_with_null(condition)  # 轉換 NaN 為 None
        condition_clause = " AND ".join([f"{key} = {self.__format_value(value)}" for key, value in condition.items()])
        return f"DELETE FROM {table_name} WHERE {condition_clause};"

    def __format_value(self, value):
        """ 私有方法：格式化 SQL 值，確保字串加上引號，日期時間轉為字串 """
        if isinstance(value, str):
            return "N'{}'".format(value.replace("'", "''"))  # 字串前面加 N，支援 Unicode
        elif isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
            return "N'{}'".format(value.strftime('%Y-%m-%d %H:%M:%S'))  # 日期時間轉字串
        elif value is None or (isinstance(value, float) and math.isnan(value)):  # NaN 轉換為 NULL
            return "NULL"
        return str(value)  # 其他類型（int、float）直接轉字串

    def __replace_nan_with_null(self, data_dict):
        """ 遍歷 dictionary，將 NaN 值轉換為 None（對應 SQL 的 NULL） """
        return {key: None if isinstance(value, float) and math.isnan(value) else value for key, value in data_dict.items()}



