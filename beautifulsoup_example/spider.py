# -*- coding: utf-8 -*-
"""
Beautiful Soup + Requests 网页爬虫示例
实现简单但功能完整的网页信息提取程序
"""

import requests
import json
import csv
import time
import random
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ProductSpider:
    """产品信息爬虫类"""

    def __init__(self, base_url: str = "http://example.com", max_pages: int = 5):
        """
        初始化爬虫

        Args:
            base_url: 目标网站基础URL
            max_pages: 最大爬取页数
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.products: List[Dict] = []
        
        self.session = requests.Session()
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        self.session.headers.update(self.headers)
        
        self.request_delay = 1.0
        self.max_retries = 3

    def _random_delay(self):
        """随机延迟，避免请求过快"""
        delay = self.request_delay + random.uniform(0, 0.5)
        time.sleep(delay)

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求

        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: 其他requests参数

        Returns:
            Response对象或None
        """
        for attempt in range(self.max_retries):
            try:
                self._random_delay()
                
                if method.upper() == "GET":
                    response = self.session.get(url, timeout=30, **kwargs)
                else:
                    response = self.session.post(url, timeout=30, **kwargs)
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries}): {url}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {e}")
                return None
            
            if attempt < self.max_retries - 1:
                wait_time = (attempt + 1) * 2
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        return None

    def parse_product_list(self, html: str) -> List[str]:
        """
        解析产品列表页面，获取产品详情页URL列表

        Args:
            html: HTML内容

        Returns:
            产品URL列表
        """
        soup = BeautifulSoup(html, 'lxml')
        product_urls = []
        
        product_selectors = [
            'div.product-item a.product-link',
            'div.product a[href*="/product/"]',
            'div.goods-item a.item-link',
            'li.product a[href]',
        ]
        
        for selector in product_selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                break
        
        if not product_urls:
            logger.warning("未找到产品链接，请检查选择器")
        
        return product_urls

    def parse_product_detail(self, html: str, url: str) -> Optional[Dict]:
        """
        解析产品详情页面

        Args:
            html: HTML内容
            url: 产品URL

        Returns:
            产品信息字典
        """
        soup = BeautifulSoup(html, 'lxml')
        
        product = {}
        
        product['product_id'] = self._extract_text(soup, [
            'span.product-id::text',
            'span#productId::text',
            'div[data-id]::attr(data-id)',
        ])
        
        product['product_name'] = self._extract_text(soup, [
            'h1.product-title::text',
            'h1.product-name::text',
            'div.product-info h1::text',
        ])
        
        product['product_price'] = self._extract_text(soup, [
            'span.price::text',
            'span.product-price::text',
            'div.price span::text',
        ])
        
        product['product_category'] = self._extract_text(soup, [
            'div.category-breadcrumb span::text',
            'nav.breadcrumb span::text',
        ])
        
        product['product_rating'] = self._extract_text(soup, [
            'span.rating-score::text',
            'div.rating span::text',
        ])
        
        product['product_sales'] = self._extract_text(soup, [
            'span.sales-count::text',
            'div.sales span::text',
        ])
        
        product['product_shop'] = self._extract_text(soup, [
            'a.shop-name::text',
            'span.shop-name::text',
        ])
        
        product['product_url'] = url
        
        product['product_image'] = self._extract_image(soup, [
            'img.product-image::attr(src)',
            'div.main-image img::attr(src)',
        ])
        
        product['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return product

    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """尝试多个选择器提取文本"""
        for selector in selectors:
            try:
                if '::' in selector:
                    tag, attr = selector.rsplit('::', 1)
                    element = soup.select_one(tag)
                    if element:
                        if attr == 'text':
                            text = element.get_text(strip=True)
                        else:
                            text = element.get(attr, '').strip()
                        if text:
                            return text
                else:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if text:
                            return text
            except Exception:
                continue
        return None

    def _extract_image(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """尝试多个选择器提取图片URL"""
        for selector in selectors:
            try:
                if '::' in selector:
                    tag, attr = selector.rsplit('::', 1)
                    element = soup.select_one(tag)
                    if element:
                        src = element.get(attr, '').strip()
                        if src:
                            return urljoin(self.base_url, src)
            except Exception:
                continue
        return None

    def crawl(self) -> List[Dict]:
        """
        执行爬取任务

        Returns:
            爬取的产品数据列表
        """
        logger.info(f"开始爬取 {self.base_url}")
        
        for page in range(1, self.max_pages + 1):
            logger.info(f"正在爬取第 {page}/{self.max_pages} 页")
            
            list_url = f"{self.base_url}/products?page={page}"
            
            response = self._make_request(list_url)
            if not response:
                logger.error(f"获取列表页失败: {list_url}")
                continue
            
            product_urls = self.parse_product_list(response.text)
            logger.info(f"第 {page} 页找到 {len(product_urls)} 个产品")
            
            for product_url in product_urls:
                logger.info(f"爬取产品: {product_url}")
                
                product_response = self._make_request(product_url)
                if not product_response:
                    logger.warning(f"获取产品详情失败: {product_url}")
                    continue
                
                product = self.parse_product_detail(product_response.text, product_url)
                
                if product and product.get('product_name'):
                    self.products.append(product)
                    logger.info(f"成功爬取产品: {product.get('product_name')}")
                else:
                    logger.warning(f"产品数据解析失败: {product_url}")
        
        logger.info(f"爬取完成，共获取 {len(self.products)} 个产品")
        return self.products

    def save_to_json(self, filename: str = None) -> str:
        """保存数据到JSON文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到 {filename}")
        return filename

    def save_to_csv(self, filename: str = None) -> str:
        """保存数据到CSV文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.csv"
        
        if not self.products:
            logger.warning("没有数据可保存")
            return None
        
        fieldnames = ['product_id', 'product_name', 'product_price', 'product_category',
                      'product_rating', 'product_sales', 'product_shop', 'product_url',
                      'product_image', 'crawl_time']
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)
        
        logger.info(f"数据已保存到 {filename}")
        return filename


class DemoSpider:
    """演示爬虫 - 使用模拟数据进行测试"""

    def __init__(self):
        self.products: List[Dict] = []

    def run(self) -> List[Dict]:
        """运行演示爬虫"""
        logger.info("运行演示爬虫（模拟数据）")
        
        demo_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Demo Products</title></head>
        <body>
            <div class="product-item">
                <a class="product-link" href="/product/1">iPhone 15 Pro</a>
                <span class="product-id">IP15P-001</span>
                <span class="price">¥8999</span>
                <span class="rating-score">4.9</span>
                <span class="sales-count">5000+</span>
                <a class="shop-name">Apple Store</a>
                <img class="product-image" src="/images/iphone15.jpg"/>
                <div class="category-breadcrumb"><span>手机</span><span>智能手机</span></div>
            </div>
            <div class="product-item">
                <a class="product-link" href="/product/2">MacBook Pro</a>
                <span class="product-id">MBP-002</span>
                <span class="price">¥19999</span>
                <span class="rating-score">4.8</span>
                <span class="sales-count">2000+</span>
                <a class="shop-name">Apple Store</a>
                <img class="product-image" src="/images/macbook.jpg"/>
                <div class="category-breadcrumb"><span>电脑</span><span>笔记本电脑</span></div>
            </div>
            <div class="product-item">
                <a class="product-link" href="/product/3">AirPods Pro</a>
                <span class="product-id">APP-003</span>
                <span class="price">¥1899</span>
                <span class="rating-score">4.7</span>
                <span class="sales-count">10000+</span>
                <a class="shop-name">Apple Store</a>
                <img class="product-image" src="/images/airpods.jpg"/>
                <div class="category-breadcrumb"><span>音频</span><span>耳机</span></div>
            </div>
        </body>
        </html>
        """
        
        spider = ProductSpider(base_url="http://example.com", max_pages=1)
        
        product_urls = spider.parse_product_list(demo_html)
        
        for url in product_urls:
            product = {
                'product_id': 'DEMO-001',
                'product_name': 'Demo Product',
                'product_price': '99.99',
                'product_category': 'Demo Category',
                'product_rating': '4.5',
                'product_sales': '100',
                'product_shop': 'Demo Shop',
                'product_url': url,
                'product_image': 'http://example.com/images/demo.jpg',
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.products.append(product)
        
        logger.info(f"演示爬虫完成，共处理 {len(self.products)} 个产品")
        return self.products


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Beautiful Soup + Requests 爬虫')
    parser.add_argument('--url', type=str, default='http://example.com', help='目标网站URL')
    parser.add_argument('--pages', type=int, default=5, help='爬取页数')
    parser.add_argument('--demo', action='store_true', help='运行演示模式')
    parser.add_argument('--output-json', action='store_true', help='保存为JSON')
    parser.add_argument('--output-csv', action='store_true', help='保存为CSV')
    
    args = parser.parse_args()
    
    if args.demo:
        spider = DemoSpider()
        products = spider.run()
    else:
        spider = ProductSpider(base_url=args.url, max_pages=args.pages)
        products = spider.crawl()
    
    if args.output_json:
        spider.save_to_json()
    
    if args.output_csv:
        spider.save_to_csv()
    
    if not args.output_json and not args.output_csv:
        spider.save_to_json()
        spider.save_to_csv()
    
    print(f"\n爬取完成！共获取 {len(products)} 条数据")


if __name__ == "__main__":
    main()
