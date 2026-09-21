import scrapy

class PgcbSpider(scrapy.Spider):
    name = 'pgcb'
    allowed_domains = ['erp.powergrid.gov.bd']
    start_urls = ['https://erp.powergrid.gov.bd/w/generations/view_generations']

    def parse(self, response):
        # Find all rows in the table body
        rows = response.xpath('//table/tbody/tr')
        
        for row in rows:
            cols = row.xpath('./td')
            if len(cols) >= 14:
                def get_float(xpath_sel):
                    text = xpath_sel.xpath('./text()').get(default='').strip()
                    try:
                        return float(text)
                    except ValueError:
                        return 0.0

                item = {
                    'date': cols[0].xpath('./text()').get(default='').strip(),
                    'time': cols[1].xpath('./text()').get(default='').strip(),
                    'generation_mw': get_float(cols[2]),
                    'gas': get_float(cols[3]),
                    'liquid_fuel': get_float(cols[4]),
                    'coal': get_float(cols[5]),
                    'hydro': get_float(cols[6]),
                    'solar': get_float(cols[7]),
                    'wind': get_float(cols[8]),
                    'india_bheramara': get_float(cols[9]),
                    'india_tripura': get_float(cols[10]),
                    'india_adani': get_float(cols[11]),
                    'nepal': get_float(cols[12]),
                    'remarks': cols[13].xpath('./text()').get(default='').strip()
                }
                yield item
