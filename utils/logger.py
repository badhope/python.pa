# -*- coding: utf-8 -*-
"""
日志配置
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config.settings import LOG_DIR, LOG_FORMAT, LOG_LEVEL


def setup_logger(name='panel_data'):
    """
    配置日志记录器
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(LOG_FORMAT)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    log_file = os.path.join(LOG_DIR, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logger()
