#!/usr/bin/env python3
"""
Power Grid Bangladesh - Master Scraper Runner
Runs both PGCB Hourly and BPDB Daily spiders and syncs data to ClickHouse
"""
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_scrapers():
    print("==================================================")
    print("Starting Bangladesh Power Grid Scraping Process...")
    print("==================================================")
    
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'pgcb_scraper.settings')
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    print("[1/2] Scheduling PGCB Hourly Generation Spider...")
    process.crawl('pgcb')
    
    print("[2/2] Scheduling BPDB Daily Generation Spider...")
    process.crawl('bpdb')
    
    print("Executing spiders concurrently...")
    process.start()
    print("All scraping jobs finished successfully!")

if __name__ == '__main__':
    run_scrapers()
