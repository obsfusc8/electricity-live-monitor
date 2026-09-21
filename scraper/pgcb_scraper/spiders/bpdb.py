import scrapy
from datetime import datetime

class BpdbSpider(scrapy.Spider):
    name = 'bpdb'
    allowed_domains = ['misc.bpdb.gov.bd']
    
    def start_requests(self):
        # Date can be dynamic, today's date
        today = datetime.now().strftime("%d-%m-%Y")
        url = f'https://misc.bpdb.gov.bd/daily-generation?date={today}'
        yield scrapy.Request(url, self.parse)

    def parse(self, response):
        # Extract the date from the date picker
        date_val = response.xpath('//input[@id="date"]/@value').get()
        if not date_val:
            date_val = datetime.now().strftime("%d-%m-%Y")
            
        rows = response.xpath('//table[contains(@class, "table-bordered")]/tbody/tr')
        
        for row in rows:
            cols = row.xpath('./td')
            if len(cols) >= 11:
                # If first column is Sl, parse the rest
                sl = cols[0].xpath('./text()').get(default='').strip()
                if not sl.isdigit():
                    continue

                def get_float(xpath_sel):
                    text = xpath_sel.xpath('./text()').get(default='').strip()
                    try:
                        return float(text)
                    except ValueError:
                        return 0.0
                
                item = {
                    'date': date_val,
                    'station_name': cols[1].xpath('./text()').get(default='').strip(),
                    'unit_capacity': cols[2].xpath('./text()').get(default='').strip(),
                    'installed_capacity': get_float(cols[3]),
                    'present_capacity': get_float(cols[4]),
                    'forecast_day_peak': get_float(cols[5]),
                    'forecast_eve_peak': get_float(cols[6]),
                    'actual_day_peak': get_float(cols[7]),
                    'actual_eve_peak': get_float(cols[8]),
                    'probable_day_peak': get_float(cols[9]),
                    'probable_eve_peak': get_float(cols[10])
                }
                yield item
