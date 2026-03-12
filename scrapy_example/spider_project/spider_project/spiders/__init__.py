# -*- coding: utf-8 -*-
"""
产品爬虫主程序
演示如何使用Scrapy框架爬取网站数据
"""

import scrapy
import json
import re
from datetime import datetime
from spider_project.items import ProductItem


class ProductSpider(scrapy.Spider):
    """产品信息爬虫"""

    name = "product_spider"
    allowed_domains = ["example.com"]

    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
    }

    def __init__(self, *args, **kwargs):
        super(ProductSpider, self).__init__(*args, **kwargs)
        self.page_count = 0
        self.max_pages = 5

    def start_requests(self):
        """
        爬虫起始请求
        这里使用示例URL，实际使用时替换为真实目标网站
        """
        base_url = "http://example.com/products"
        
        for page in range(1, self.max_pages + 1):
            url = f"{base_url}?page={page}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_product_list,
                meta={'page': page},
                dont_filter=False
            )

    def parse_product_list(self, response):
        """
        解析产品列表页面
        提取产品详情页URL
        """
        self.page_count += 1
        self.logger.info(f"正在解析第 {response.meta['page']} 页产品列表")

        # 示例选择器 - 根据实际网站结构调整
        # 产品列表容器
        product_selectors = response.css('div.product-item')
        
        if not product_selectors:
            product_selectors = response.xpath('//div[@class="product"]')

        for product_sel in product_selectors:
            # 提取产品详情页URL
            detail_url = product_sel.css('a.product-link::attr(href)').get()
            
            if detail_url:
                # 构建完整URL
                if not detail_url.startswith('http'):
                    detail_url = response.urljoin(detail_url)
                
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_product_detail,
                    meta={'page': response.meta['page']}
                )

        # 处理分页 - 如果存在下一页
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page and self.page_count < self.max_pages:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_product_list,
                meta={'page': response.meta['page'] + 1}
            )

    def parse_product_detail(self, response):
        """
        解析产品详情页面
        提取产品详细信息
        """
        self.logger.info(f"正在解析产品详情: {response.url}")

        item = ProductItem()

        # 产品ID
        product_id = response.css('span.product-id::text').get()
        if not product_id:
            product_id = response.xpath('//span[@class="id"]/text()').get()
        item['product_id'] = product_id

        # 产品名称
        product_name = response.css('h1.product-title::text').get()
        if not product_name:
            product_name = response.xpath('//h1[@class="title"]/text()').get()
        item['product_name'] = product_name.strip() if product_name else None

        # 产品价格
        product_price = response.css('span.price::text').get()
        if not product_price:
            product_price = response.xpath('//span[@class="product-price"]/text()').get()
        item['product_price'] = product_price

        # 产品分类
        category = response.css('div.category span::text').getall()
        item['product_category'] = ' > '.join([c.strip() for c in category]) if category else None

        # 产品评分
        rating = response.css('span.rating-score::text').get()
        if not rating:
            rating = response.xpath('//span[@class="score"]/text()').get()
        item['product_rating'] = rating

        # 销量
        sales = response.css('span.sales-count::text').get()
        if not sales:
            sales = response.xpath('//span[@class="sales"]/text()').get()
        item['product_sales'] = sales

        # 店铺名称
        shop = response.css('a.shop-name::text').get()
        if not shop:
            shop = response.xpath('//a[@class="shop"]/text()').get()
        item['product_shop'] = shop

        # 产品URL
        item['product_url'] = response.url

        # 产品图片
        product_image = response.css('img.product-image::attr(src)').get()
        if not product_image:
            product_image = response.xpath('//img[@class="main-image"]/@src').get()
        item['product_image'] = product_image

        # 爬取时间
        item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        yield item


class JsonProductSpider(scrapy.Spider):
    """JSON API产品爬虫 - 适用于返回JSON数据的网站"""

    name = "json_product_spider"
    allowed_domains = ["example.com"]

    def start_requests(self):
        """发送API请求获取产品数据"""
        api_url = "http://example.com/api/products"
        
        for page in range(1, 6):
            url = f"{api_url}?page={page}&size=20"
            yield scrapy.Request(
                url=url,
                callback=self.parse_json_response,
                meta={'page': page}
            )

    def parse_json_response(self, response):
        """解析JSON响应数据"""
        try:
            data = json.loads(response.text)
            
            products = data.get('data', [])
            for product in products:
                item = ProductItem()
                item['product_id'] = product.get('id')
                item['product_name'] = product.get('name')
                item['product_price'] = product.get('price')
                item['product_category'] = product.get('category')
                item['product_rating'] = product.get('rating')
                item['product_sales'] = product.get('sales')
                item['product_shop'] = product.get('shop', {}).get('name') if isinstance(product.get('shop'), dict) else product.get('shop')
                item['product_url'] = product.get('url')
                item['product_image'] = product.get('image')
                item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                yield item

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}, URL: {response.url}")


class DemoSpider(scrapy.Spider):
    """演示爬虫 - 使用本地HTML文件测试"""

    name = "demo_spider"
    allowed_domains = []

    def __init__(self, *args, **kwargs):
        super(DemoSpider, self).__init__(*args, **kwargs)
        self.crawled_count = 0

    def start_requests(self):
        """生成测试用的示例数据"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Demo Products</title></head>
        <body>
            <div class="product-item">
                <a class="product-link" href="/product/1">Product 1</a>
                <span class="product-id">P001</span>
                <span class="price">99.99</span>
                <span class="rating-score">4.5</span>
                <span class="sales-count">1000</span>
                <a class="shop-name">Shop A</a>
                <img class="product-image" src="/images/p1.jpg"/>
                <div class="category"><span>Electronics</span></div>
            </div>
            <div class="product-item">
                <a class="product-link" href="/product/2">Product 2</a>
                <span class="product-id">P002</span>
                <span class="price">199.99</span>
                <span class="rating-score">4.8</span>
                <span class="sales-count">5000</span>
                <a class="shop-name">Shop B</a>
                <img class="product-image" src="/images/p2.jpg"/>
                <div class="category"><span>Electronics</span></div>
            </div>
        </body>
        </html>
        """

        from scrapy.http import HtmlResponse
        response = HtmlResponse(
            url="http://example.com/demo",
            body=html_content.encode('utf-8'),
            encoding='utf-8'
        )
        
        return [self.parse_product_list(response)]

    def parse_product_list(self, response):
        """解析产品列表"""
        product_selectors = response.css('div.product-item')
        
        for product_sel in product_selectors:
            item = ProductItem()
            item['product_id'] = product_sel.css('span.product-id::text').get()
            item['product_name'] = product_sel.css('a.product-link::text').get()
            item['product_price'] = product_sel.css('span.price::text').get()
            item['product_rating'] = product_sel.css('span.rating-score::text').get()
            item['product_sales'] = product_sel.css('span.sales-count::text').get()
            item['product_shop'] = product_sel.css('a.shop-name::text').get()
            item['product_image'] = product_sel.css('img.product-image::attr(src)').get()
            item['product_category'] = product_sel.css('div.category span::text').get()
            item['product_url'] = response.urljoin(product_sel.css('a.product-link::attr(href)').get())
            item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.crawled_count += 1
            yield item

        self.logger.info(f"演示爬虫完成，共爬取 {self.crawled_count} 个产品")
