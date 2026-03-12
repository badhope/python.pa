# -*- coding: utf-8 -*-
"""
Selenium 动态网页爬虫示例
处理JavaScript渲染的页面
"""

import json
import csv
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SeleniumSpider:
    """Selenium动态网页爬虫"""

    def __init__(self, base_url: str = "http://example.com", max_pages: int = 5, browser: str = "chrome"):
        """
        初始化爬虫

        Args:
            base_url: 目标网站基础URL
            max_pages: 最大爬取页数
            browser: 使用的浏览器 (chrome/firefox)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.browser = browser
        self.driver = None
        self.products: List[Dict] = []
        
        self.request_delay = 2.0
        self.page_load_timeout = 30
        self.implicit_wait = 10
        
        self._init_driver()

    def _init_driver(self):
        """初始化浏览器驱动"""
        try:
            if self.browser.lower() == "chrome":
                options = ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                options.add_argument(f"user-agent={user_agent}")
                
                self.driver = webdriver.Chrome(options=options)
                
            elif self.browser.lower() == "firefox":
                options = FirefoxOptions()
                options.add_argument("--headless")
                options.add_argument("--width=1920")
                options.add_argument("--height=1080")
                
                self.driver = webdriver.Firefox(options=options)
            else:
                raise ValueError(f"不支持的浏览器: {self.browser}")
            
            self.driver.set_page_load_timeout(self.page_load_timeout)
            self.driver.implicitly_wait(self.implicit_wait)
            
            logger.info(f"浏览器驱动初始化成功: {self.browser}")
            
        except WebDriverException as e:
            logger.error(f"浏览器驱动初始化失败: {e}")
            raise

    def _random_delay(self):
        """随机延迟"""
        delay = self.request_delay + random.uniform(0, 1)
        time.sleep(delay)

    def _wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"等待元素超时: {selector}")
            return None

    def _wait_for_elements(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10):
        """等待多个元素出现"""
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, selector))
            )
            return elements
        except TimeoutException:
            logger.warning(f"等待元素超时: {selector}")
            return []

    def scroll_to_load(self, scroll_pause: float = 1.0, max_scrolls: int = 3):
        """滚动页面以触发懒加载"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_page(self, url: str) -> bool:
        """加载页面"""
        try:
            self._random_delay()
            self.driver.get(url)
            self._random_delay()
            return True
        except WebDriverException as e:
            logger.error(f"页面加载失败: {e}")
            return False

    def parse_product_list(self) -> List[str]:
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
                elements = self._wait_for_elements(selector, timeout=5)
                if elements:
                    for elem in elements:
                        href = elem.get_attribute('href')
                        if href and '/product/' in href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_urls:
                                product_urls.append(full_url)
                    if product_urls:
                        break
            except Exception:
                continue
        
        if not product_urls:
            logger.warning("未找到产品链接")
        
        return product_urls

    def parse_product_detail(self, url: str) -> Optional[Dict]:
        """解析产品详情页"""
        if not self.get_page(url):
            return None
        
        time.sleep(1)
        self.scroll_to_load(scroll_pause=0.5, max_scrolls=2)
        
        product = {}
        
        product['product_id'] = self._extract_text([
            'span.product-id',
            'span[data-id]',
            '#productId',
        ])
        
        product['product_name'] = self._extract_text([
            'h1.product-title',
            'h1.product-name',
            'div.product-info h1',
            'h1[itemprop="name"]',
        ])
        
        product['product_price'] = self._extract_text([
            'span.price',
            'span.product-price',
            'div.price span',
            '[itemprop="price"]',
        ])
        
        product['product_category'] = self._extract_text([
            'div.category-breadcrumb',
            'nav.breadcrumb',
            '[itemprop="breadcrumb"]',
        ])
        
        product['product_rating'] = self._extract_text([
            'span.rating-score',
            'div.rating span',
            '[itemprop="ratingValue"]',
        ])
        
        product['product_sales'] = self._extract_text([
            'span.sales-count',
            'div.sales',
            '[itemprop="sales"]',
        ])
        
        product['product_shop'] = self._extract_text([
            'a.shop-name',
            'span.shop-name',
            '[itemprop="seller"]',
        ])
        
        product['product_url'] = url
        
        product['product_image'] = self._extract_attribute([
            'img.product-image',
            'div.main-image img',
        ], 'src')
        
        product['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return product

    def _extract_text(self, selectors: List[str]) -> Optional[str]:
        """尝试多个选择器提取文本"""
        for selector in selectors:
            try:
                elem = self._wait_for_element(selector, timeout=3)
                if elem:
                    text = elem.text.strip()
                    if text:
                        return text
            except Exception:
                continue
        return None

    def _extract_attribute(self, selectors: List[str], attr: str) -> Optional[str]:
        """尝试多个选择器提取属性"""
        for selector in selectors:
            try:
                elem = self._wait_for_element(selector, timeout=3)
                if elem:
                    value = elem.get_attribute(attr)
                    if value:
                        return value
            except Exception:
                continue
        return None

    def crawl(self) -> List[Dict]:
        """执行爬取任务"""
        logger.info(f"开始爬取 {self.base_url}")
        
        for page in range(1, self.max_pages + 1):
            logger.info(f"正在爬取第 {page}/{self.max_pages} 页")
            
            list_url = f"{self.base_url}/products?page={page}"
            
            if not self.get_page(list_url):
                logger.error(f"获取列表页失败: {list_url}")
                continue
            
            time.sleep(2)
            self.scroll_to_load()
            
            product_urls = self.parse_product_list()
            logger.info(f"第 {page} 页找到 {len(product_urls)} 个产品")
            
            for product_url in product_urls:
                logger.info(f"爬取产品: {product_url}")
                
                product = self.parse_product_detail(product_url)
                
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

    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Selenium 动态网页爬虫')
    parser.add_argument('--url', type=str, default='http://example.com', help='目标网站URL')
    parser.add_argument('--pages', type=int, default=5, help='爬取页数')
    parser.add_argument('--browser', type=str, default='chrome', choices=['chrome', 'firefox'], help='使用的浏览器')
    parser.add_argument('--no-headless', action='store_true', help='不使用无头模式')
    parser.add_argument('--output-json', action='store_true', help='保存为JSON')
    parser.add_argument('--output-csv', action='store_true', help='保存为CSV')
    
    args = parser.parse_args()
    
    try:
        with SeleniumSpider(base_url=args.url, max_pages=args.pages, browser=args.browser) as spider:
            products = spider.crawl()
            
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
