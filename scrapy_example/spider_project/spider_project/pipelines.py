# -*- coding: utf-8 -*-
"""
数据处理管道
负责清洗、验证和保存爬取的数据
"""

import json
import csv
import os
from datetime import datetime


class JsonWriterPipeline:
    """JSON文件输出管道"""

    def __init__(self):
        self.file = None
        self.items = []

    def open_spider(self, spider):
        """爬虫启动时调用"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"products_{timestamp}.json"
        spider.logger.info(f"JSON管道启动，将保存数据到 {filename}")

    def close_spider(self, spider):
        """爬虫关闭时调用"""
        if self.items:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
            spider.logger.info(f"JSON管道关闭，共保存 {len(self.items)} 条数据到 {filename}")

    def process_item(self, item, spider):
        """处理每个爬取到的数据项"""
        self.items.append(dict(item))
        return item


class CsvWriterPipeline:
    """CSV文件输出管道"""

    def __init__(self):
        self.file = None
        self.writer = None
        self.filename = None

    def open_spider(self, spider):
        """爬虫启动时调用"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"products_{timestamp}.csv"
        self.file = open(self.filename, 'w', encoding='utf-8-sig', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=[
            'product_id', 'product_name', 'product_price', 'product_category',
            'product_rating', 'product_sales', 'product_shop', 'product_url',
            'product_image', 'crawl_time'
        ])
        self.writer.writeheader()
        spider.logger.info(f"CSV管道启动，将保存数据到 {self.filename}")

    def close_spider(self, spider):
        """爬虫关闭时调用"""
        if self.file:
            self.file.close()
            spider.logger.info(f"CSV管道关闭，数据已保存到 {self.filename}")

    def process_item(self, item, spider):
        """处理每个爬取到的数据项"""
        self.writer.writerow(dict(item))
        return item


class DataCleanPipeline:
    """数据清洗管道"""

    def process_item(self, item, spider):
        """清洗和验证数据"""
        if not item.get('product_name'):
            spider.logger.warning("产品名称为空，跳过")
            return None

        if item.get('product_price'):
            item['product_price'] = self._clean_price(item['product_price'])

        if item.get('product_sales'):
            item['product_sales'] = self._clean_sales(item['product_sales'])

        if item.get('product_rating'):
            item['product_rating'] = self._clean_rating(item['product_rating'])

        return item

    def _clean_price(self, price):
        """清洗价格数据"""
        if isinstance(price, str):
            import re
            cleaned = re.sub(r'[^\d.]', '', price)
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return price

    def _clean_sales(self, sales):
        """清洗销量数据"""
        if isinstance(sales, str):
            import re
            cleaned = re.sub(r'[^\d万]', '', sales)
            if '万' in cleaned:
                return float(cleaned.replace('万', '')) * 10000
            try:
                return int(cleaned)
            except ValueError:
                return 0
        return sales

    def _clean_rating(self, rating):
        """清洗评分数据"""
        if isinstance(rating, str):
            import re
            cleaned = re.sub(r'[^\d.]', '', rating)
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return rating
