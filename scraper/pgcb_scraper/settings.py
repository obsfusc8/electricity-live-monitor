BOT_NAME = 'pgcb_scraper'

SPIDER_MODULES = ['pgcb_scraper.spiders']
NEWSPIDER_MODULE = 'pgcb_scraper.spiders'

ROBOTSTXT_OBEY = False

ITEM_PIPELINES = {
   'pgcb_scraper.pipelines.ClickHousePipeline': 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
