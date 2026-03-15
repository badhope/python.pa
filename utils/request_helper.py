# -*- coding: utf-8 -*-
"""
请求辅助工具
提供 UA 池、限流、重试等功能
"""

import random
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from config.settings import (
    USER_AGENT_POOL, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
    REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)

logger = logging.getLogger(__name__)


def get_random_user_agent():
    """随机获取 User-Agent"""
    return random.choice(USER_AGENT_POOL)


def get_session():
    """创建带重试机制的 Session"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session


def random_delay():
    """随机延时"""
    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    time.sleep(delay)
    return delay


def safe_request(url, params=None, headers=None, max_retries=3):
    """
    安全的请求封装
    自动处理 UA、延时、重试
    """
    session = get_session()
    
    if headers is None:
        headers = {}
    
    headers['User-Agent'] = get_random_user_agent()
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
    headers['Connection'] = 'keep-alive'
    
    for attempt in range(max_retries):
        try:
            random_delay()
            
            response = session.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 429:
                logger.warning(f"请求频率过高，延长延时时间：{url}")
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 (第{attempt+1}次): {url}, 错误：{e}")
            if attempt == max_retries - 1:
                logger.error(f"请求彻底失败：{url}")
                return None
            time.sleep(RETRY_DELAY * (attempt + 1))
    
    return None


class RequestLimiter:
    """请求限流器"""
    
    def __init__(self, min_delay=REQUEST_DELAY_MIN, max_delay=REQUEST_DELAY_MAX):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self):
        """等待合适的时机"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        min_interval = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
