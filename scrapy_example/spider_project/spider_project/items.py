# -*- coding: utf-8 -*-
"""
数据模型定义文件
定义爬虫需要提取的数据结构
"""

import scrapy


class ProductItem(scrapy.Item):
    """产品数据模型"""
    product_id = scrapy.Field()          # 产品ID
    product_name = scrapy.Field()        # 产品名称
    product_price = scrapy.Field()        # 产品价格
    product_category = scrapy.Field()     # 产品分类
    product_rating = scrapy.Field()       # 产品评分
    product_sales = scrapy.Field()        # 销量
    product_shop = scrapy.Field()          # 店铺名称
    product_url = scrapy.Field()          # 产品URL
    product_image = scrapy.Field()        # 产品图片URL
    crawl_time = scrapy.Field()           # 爬取时间
