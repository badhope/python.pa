# -*- coding: utf-8 -*-
"""
Pyppeteer 无头浏览器爬虫示例
展示现代网页爬取能力，处理JavaScript渲染页面
"""

import json
import csv
import asyncio
import time
import random
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

import pyppeteer
from pyppeteer import launch
from pyppeteer.errors import PyppeteerError, TimeoutError


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PyppeteerSpider:
    """Pyppeteer无头浏览器爬虫"""

    def __init__(self, base_url: str = "http://example.com", max_pages: int = 5):
        """
        初始化爬虫

        Args:
            base_url: 目标网站基础URL
            max_pages: 最大爬取页数
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.browser = None
        self.page = None
        self.products: List[Dict] = []
        
        self.request_delay = 1.5
        self.page_load_timeout = 30000
        self.navigation_timeout = 30000
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]

    async def _init_browser(self):
        """初始化浏览器"""
        try:
            self.browser = await launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--window-size=1920,1080',
                    '--start-maximized',
                ],
                ignoreDefaultArgs=['--enable-automation'],
                ignoreHTTPSErrors=True,
            )
            
            self.page = await self.browser.newPage()
            
            await self.page.setUserAgent(random.choice(self.user_agents))
            await self.page.setViewport({'width': 1920, 'height': 1080})
            
            await self.page.setRequestInterception(True)
            
            async def request_handler(request):
                resource_type = request.resourceType
                if resource_type in ['image', 'media', 'font']:
                    await request.abort()
                else:
                    await request.continue_()
            
            self.page.on('request', request_handler)
            
            logger.info("浏览器初始化成功")
            
        except PyppeteerError as e:
            logger.error(f"浏览器初始化失败: {e}")
            raise

    async def _random_delay(self):
        """随机延迟"""
        delay = self.request_delay + random.uniform(0, 1)
        await asyncio.sleep(delay)

    async def get_page(self, url: str) -> bool:
        """加载页面"""
        try:
            await self._random_delay()
            
            await self.page.goto(
                url,
                {
                    'waitUntil': 'networkidle2',
                    'timeout': self.page_load_timeout
                }
            )
            
            await asyncio.sleep(1)
            return True
            
        except TimeoutError:
            logger.warning(f"页面加载超时: {url}")
            return False
        except PyppeteerError as e:
            logger.error(f"页面加载失败: {e}")
            return False

    async def scroll_to_load(self, scroll_pause: float = 1.0, max_scrolls: int = 3):
        """滚动页面以触发懒加载"""
        last_height = await self.page.evaluate('document.body.scrollHeight')
        
        for _ in range(max_scrolls):
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(scroll_pause)
            
            new_height = await self.page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

    async def parse_product_list(self) -> List[str]:
        """解析产品列表页，获取产品URL列表"""
        product_urls = []
        
        product_selectors = [
            'div.product-item a.product-link',
            'div.product a[href*="/product/"]',
            'div.goods-item a.item-link',
            'li.product a[href]',
            'a[href*="/product/"]',
        ]
        
        for selector in product_selectors:
            try:
                elements = await self.page.querySelectorAll(selector)
                if elements:
                    for elem in elements:
                        href = await elem.evaluate('el => el.href')
                        if href and '/product/' in href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_urls:
                                product_urls.append(full_url)
                    if product_urls:
                        break
            except Exception as e:
                logger.debug(f"选择器 {selector} 匹配失败: {e}")
                continue
        
        if not product_urls:
            logger.warning("未找到产品链接")
        
        return product_urls

    async def parse_product_detail(self, url: str) -> Optional[Dict]:
        """解析产品详情页"""
        if not await self.get_page(url):
            return None
        
        await asyncio.sleep(1)
        await self.scroll_to_load(scroll_pause=0.5, max_scrolls=2)
        
        product = {}
        
        product['product_id'] = await self._extract_text([
            'span.product-id',
            'span[data-id]',
            '#productId',
        ])
        
        product['product_name'] = await self._extract_text([
            'h1.product-title',
            'h1.product-name',
            'div.product-info h1',
            'h1[itemprop="name"]',
        ])
        
        product['product_price'] = await self._extract_text([
            'span.price',
            'span.product-price',
            'div.price span',
            '[itemprop="price"]',
        ])
        
        product['product_category'] = await self._extract_text([
            'div.category-breadcrumb',
            'nav.breadcrumb',
            '[itemprop="breadcrumb"]',
        ])
        
        product['product_rating'] = await self._extract_text([
            'span.rating-score',
            'div.rating span',
            '[itemprop="ratingValue"]',
        ])
        
        product['product_sales'] = await self._extract_text([
            'span.sales-count',
            'div.sales',
            '[itemprop="sales"]',
        ])
        
        product['product_shop'] = await self._extract_text([
            'a.shop-name',
            'span.shop-name',
            '[itemprop="seller"]',
        ])
        
        product['product_url'] = url
        
        product['product_image'] = await self._extract_attribute([
            'img.product-image',
            'div.main-image img',
        ], 'src')
        
        product['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return product

    async def _extract_text(self, selectors: List[str]) -> Optional[str]:
        """尝试多个选择器提取文本"""
        for selector in selectors:
            try:
                elem = await self.page.querySelector(selector)
                if elem:
                    text = await self.page.evaluate('el => el.textContent.trim()', elem)
                    if text:
                        return text
            except Exception:
                continue
        return None

    async def _extract_attribute(self, selectors: List[str], attr: str) -> Optional[str]:
        """尝试多个选择器提取属性"""
        for selector in selectors:
            try:
                elem = await self.page.querySelector(selector)
                if elem:
                    value = await self.page.evaluate(f'el => el.getAttribute("{attr}")', elem)
                    if value:
                        return value
            except Exception:
                continue
        return None

    async def crawl(self) -> List[Dict]:
        """执行爬取任务"""
        logger.info(f"开始爬取 {self.base_url}")
        
        await self._init_browser()
        
        try:
            for page_num in range(1, self.max_pages + 1):
                logger.info(f"正在爬取第 {page_num}/{self.max_pages} 页")
                
                list_url = f"{self.base_url}/products?page={page_num}"
                
                if not await self.get_page(list_url):
                    logger.error(f"获取列表页失败: {list_url}")
                    continue
                
                await asyncio.sleep(2)
                await self.scroll_to_load()
                
                product_urls = await self.parse_product_list()
                logger.info(f"第 {page_num} 页找到 {len(product_urls)} 个产品")
                
                for product_url in product_urls:
                    logger.info(f"爬取产品: {product_url}")
                    
                    product = await self.parse_product_detail(product_url)
                    
                    if product and product.get('product_name'):
                        self.products.append(product)
                        logger.info(f"成功爬取产品: {product.get('product_name')}")
                    else:
                        logger.warning(f"产品数据解析失败: {product_url}")
        
        finally:
            await self.close()
        
        logger.info(f"爬取完成，共获取 {len(self.products)} 个产品")
        return self.products

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("浏览器已关闭")

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


async def main_async(base_url: str = "http://example.com", max_pages: int = 5):
    """异步主函数"""
    spider = PyppeteerSpider(base_url=base_url, max_pages=max_pages)
    products = await spider.crawl()
    return products


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pyppeteer 无头浏览器爬虫')
    parser.add_argument('--url', type=str, default='http://example.com', help='目标网站URL')
    parser.add_argument('--pages', type=int, default=5, help='爬取页数')
    parser.add_argument('--output-json', action='store_true', help='保存为JSON')
    parser.add_argument('--output-csv', action='store_true', help='保存为CSV')
    
    args = parser.parse_args()
    
    try:
        products = asyncio.get_event_loop().run_until_complete(
            main_async(args.url, args.pages)
        )
        
        spider = PyppeteerSpider(base_url=args.url, max_pages=args.pages)
        spider.products = products
        
        if args.output_json:
            spider.save_to_json()
        
        if args.output_csv:
            spider.save_to_csv()
        
        if not args.output_json and not args.output_csv:
            spider.save_to_json()
            spider.save_to_csv()
        
        print(f"\n爬取完成！共获取 {len(products)} 条数据")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        raise


if __name__ == "__main__":
    main()
