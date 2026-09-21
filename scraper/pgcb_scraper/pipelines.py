import requests
import json
import logging
import os

class ClickHousePipeline:
    def __init__(self):
        self.url = os.getenv('CLICKHOUSE_URL', 'http://localhost:8123/')
        self.db = os.getenv('CLICKHOUSE_DB', 'powergrid')
        self.user = os.getenv('CLICKHOUSE_USER', 'default')
        self.password = os.getenv('CLICKHOUSE_PASSWORD', '')
        self.auth = (self.user, self.password) if self.password else None

        
    def open_spider(self, spider):
        # Initialize databases and tables
        create_db = f"CREATE DATABASE IF NOT EXISTS {self.db}"
        requests.post(self.url, data=create_db, auth=self.auth)
        
        # PGCB Table
        create_pgcb_table = f"""
        CREATE TABLE IF NOT EXISTS {self.db}.pgcb_generation (
            date String,
            time String,
            generation_mw Float32,
            gas Float32,
            liquid_fuel Float32,
            coal Float32,
            hydro Float32,
            solar Float32,
            wind Float32,
            india_bheramara Float32,
            india_tripura Float32,
            india_adani Float32,
            nepal Float32,
            remarks String,
            scraped_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (date, time)
        """
        requests.post(self.url, data=create_pgcb_table, auth=self.auth)

        # BPDB Table
        create_bpdb_table = f"""
        CREATE TABLE IF NOT EXISTS {self.db}.bpdb_generation (
            date String,
            station_name String,
            unit_capacity String,
            installed_capacity Float32,
            present_capacity Float32,
            forecast_day_peak Float32,
            forecast_eve_peak Float32,
            actual_day_peak Float32,
            actual_eve_peak Float32,
            probable_day_peak Float32,
            probable_eve_peak Float32,
            scraped_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (date, station_name)
        """
        requests.post(self.url, data=create_bpdb_table, auth=self.auth)

    def process_item(self, item, spider):
        if spider.name == 'pgcb':
            query = f"INSERT INTO {self.db}.pgcb_generation FORMAT JSONEachRow"
            # Sanitize and handle empty strings by putting 0.0 or keeping as string
            data = json.dumps(dict(item))
            res = requests.post(self.url, data=query + '\\n' + data, auth=self.auth)
            if res.status_code != 200:
                logging.error(f"ClickHouse Insert Error: {res.text}")
        elif spider.name == 'bpdb':
            query = f"INSERT INTO {self.db}.bpdb_generation FORMAT JSONEachRow"
            data = json.dumps(dict(item))
            res = requests.post(self.url, data=query + '\\n' + data, auth=self.auth)
            if res.status_code != 200:
                logging.error(f"ClickHouse Insert Error: {res.text}")
        return item
