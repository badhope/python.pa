# -*- coding: utf-8 -*-
"""
全局配置文件
"""

import os
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')

# 日志配置
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# 请求配置
USER_AGENT_POOL = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

# 请求延时配置 (秒)
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 5.0

# 超时配置 (秒)
REQUEST_TIMEOUT = 30

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5

# 目标网站配置
WEBSITES = {
    '51job': {
        'base_url': 'https://www.51job.com',
        'search_url': 'https://search.51job.com/',
        'company_url_pattern': 'https://jobs.51job.com/company/{company_id}.html',
        'jobs_api': 'https://api.51job.com/api/job/search.php',
    },
    'cninfo': {
        'base_url': 'http://www.cninfo.com.cn',
        'search_url': 'http://www.cninfo.com.cn/new/commonText/search',
        'report_url_pattern': 'http://static.cninfo.com.cn/{report_id}',
    },
    'sina': {
        'base_url': 'https://finance.sina.com.cn',
        'stock_url_pattern': 'https://finance.sina.com.cn/realstock/company/{stock_code}/nc.shtml',
    }
}

# 测试样本配置
TEST_SAMPLE_SIZE = 50
TEST_SAMPLE_CONFIG = {
    'soe_count': 25,  # 国企数量
    'private_count': 25,  # 民企数量
    'high_tech_count': 25,  # 高科技行业
    'traditional_count': 25,  # 传统行业
}

# 数据输出配置
OUTPUT_COLUMNS = [
    'stock_code', 'company_name', 'year',
    'revenue', 'employee_count', 'perf_per_capita',
    'jd_total_count', 'ai_keyword_count', 'ai_intensity',
    'exec_list', 'rational_bg_count', 'exec_cognition',
    'is_soe', 'industry_code', 'is_high_tech',
    'firm_size', 'roa'
]

# PDF 解析配置
PDF_PARSER = 'pdfplumber'  # 可选：'pdfplumber', 'PyMuPDF'

# 日期时间
CURRENT_DATE = datetime.now().strftime('%Y%m%d')
