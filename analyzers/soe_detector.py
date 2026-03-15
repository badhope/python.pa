# -*- coding: utf-8 -*-
"""
产权性质检测器
判断企业是国企还是民企
"""

import re
from typing import Dict, Optional
from config.keywords import SOE_KEYWORDS, PRIVATE_KEYWORDS
from utils.logger import logger


class SOEDetector:
    """国企检测器"""
    
    def __init__(self):
        self.soe_keywords = SOE_KEYWORDS
        self.private_keywords = PRIVATE_KEYWORDS
    
    def detect_ownership(self, controller_text: str) -> int:
        """
        根据实际控制人信息判断产权性质
        返回：1=国企，0=民企
        """
        if not controller_text:
            logger.warning("实际控制人信息为空，默认标记为民企")
            return 0
        
        text_lower = controller_text.lower()
        
        soe_keywords_matched = []
        private_keywords_matched = []
        
        for keyword in self.soe_keywords:
            if keyword.lower() in text_lower:
                soe_keywords_matched.append(keyword)
        
        for keyword in self.private_keywords:
            if keyword.lower() in text_lower:
                private_keywords_matched.append(keyword)
        
        strong_soe_indicators = ['国资委', '国务院国资委', '国有独资', '全民所有制', '中央企业', '央企']
        strong_private_indicators = ['自然人', '个人独资', '有限合伙']
        
        soe_company_patterns = ['中国石油', '中国石化', '国家电网', '中国移动', '中国电信', '中国联通',
                                '中国烟草', '中国铁路', '中国邮政', '中国航天', '中国航空', '中国船舶',
                                '中国兵器', '中国电子', '中国电科', '中粮集团', '中国铝业', '中国五矿',
                                '中国建筑', '中国中铁', '中国铁建', '中国交通', '中国水利', '中国电力',
                                '中国能源', '中国核电', '中国广核', '中国长江', '中国三峡']
        
        for indicator in strong_soe_indicators:
            if indicator.lower() in text_lower:
                logger.info(f"检测到强国企信号：{indicator}")
                return 1
        
        for indicator in strong_private_indicators:
            if indicator.lower() in text_lower:
                logger.info(f"检测到强民企信号：{indicator}")
                return 0
        
        for pattern in soe_company_patterns:
            if pattern.lower() in text_lower:
                logger.info(f"检测到知名国企：{pattern}")
                return 1
        
        if len(soe_keywords_matched) > len(private_keywords_matched):
            return 1
        elif len(private_keywords_matched) > len(soe_keywords_matched):
            return 0
        else:
            if len(soe_keywords_matched) > 0:
                return 1
            else:
                return 0
    
    def extract_controller_info(self, report_text: str) -> Optional[str]:
        """
        从年报文本中提取实际控制人信息
        """
        if not report_text:
            return None
        
        patterns = [
            r'实际控制人 [::]\s*([^\n。]+)',
            r'控股股东 [::]\s*([^\n。]+)',
            r'最终控制人 [::]\s*([^\n。]+)',
            r'公司实际控制人为 ([^\n。]+)',
            r'公司控股股东为 ([^\n。]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, report_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def analyze_company(self, controller_text: str) -> Dict:
        """
        分析公司产权性质
        返回：详细分析结果
        """
        is_soe = self.detect_ownership(controller_text)
        
        matched_keywords = []
        text_lower = controller_text.lower() if controller_text else ''
        
        if is_soe:
            for keyword in self.soe_keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
        else:
            for keyword in self.private_keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
        
        return {
            'is_soe': is_soe,
            'ownership_type': '国企' if is_soe else '民企',
            'controller_text': controller_text,
            'matched_keywords': matched_keywords,
            'confidence': 'high' if len(matched_keywords) > 0 else 'low'
        }
