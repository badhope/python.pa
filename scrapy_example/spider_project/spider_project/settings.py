# -*- coding: utf-8 -*-
"""
Scrapy项目配置文件
"""

BOT_NAME = "spider_project"

SPIDER_MODULES = ["spider_project.spiders"]
NEWSPIDER_MODULE = "spider_project.spiders"

# 爬虫名称
ROBOTSTXT_OBEY = True

# 用户代理配置
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 并发请求配置
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# 下载延迟（秒）- 避免请求过快
DOWNLOAD_DELAY = 1

# 请求超时时间（秒）
DOWNLOAD_TIMEOUT = 30

# 是否启用cookies
COOKIES_ENABLED = True

# HTTP缓存配置
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# 自动限速配置
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# 请求头配置
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 爬虫中间件配置
SPIDER_MIDDLEWARES = {
    "spider_project.middlewares.SpiderProjectSpiderMiddleware": 543,
}

# 下载器中间件配置
DOWNLOADER_MIDDLEWARES = {
    "spider_project.middlewares.SpiderProjectDownloaderMiddleware": 543,
    "spider_project.middlewares.RandomUserAgentMiddleware": 400,
    "spider_project.middlewares.ProxyMiddleware": 410,
}

# 管道配置
ITEM_PIPELINES = {
    "spider_project.pipelines.DataCleanPipeline": 100,
    "spider_project.pipelines.JsonWriterPipeline": 300,
    "spider_project.pipelines.CsvWriterPipeline": 400,
}

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# 关闭Telnet Console
TELNETCONSOLE_ENABLED = False

# 启用自动分析
AUTOSPIDER_ENABLED = False

# 关闭AWS访问
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
