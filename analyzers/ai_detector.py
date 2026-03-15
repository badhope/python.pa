# -*- coding: utf-8 -*-
"""
AI 招聘强度检测器
分析职位描述中的 AI 关键词频率
"""

import re
from typing import List, Dict
from config.keywords import AI_ALL_KEYWORDS, AI_CORE_KEYWORDS, AI_SCENE_KEYWORDS
from utils.logger import logger


class AIDetector:
    """AI 关键词检测器"""
    
    def __init__(self):
        self.all_keywords = AI_ALL_KEYWORDS
        self.core_keywords = AI_CORE_KEYWORDS
        self.scene_keywords = AI_SCENE_KEYWORDS
    
    def count_keywords(self, text: str) -> Dict[str, int]:
        """
        统计文本中 AI 关键词的出现次数
        返回：总次数、核心词次数、场景词次数
        """
        if not text:
            return {
                'total_count': 0,
                'core_count': 0,
                'scene_count': 0
            }
        
        text_lower = text.lower()
        
        total_count = 0
        core_count = 0
        scene_count = 0
        
        for keyword in self.core_keywords:
            if keyword.lower() in text_lower:
                count = len(re.findall(re.escape(keyword.lower()), text_lower))
                core_count += count
                total_count += count
        
        for keyword in self.scene_keywords:
            if keyword.lower() in text_lower:
                count = len(re.findall(re.escape(keyword.lower()), text_lower))
                scene_count += count
                total_count += count
        
        return {
            'total_count': total_count,
            'core_count': core_count,
            'scene_count': scene_count
        }
    
    def calculate_ai_intensity(self, jd_list: List[str]) -> float:
        """
        计算 AI 招聘强度
        公式：AI_Score = 所有 JD 中 AI 关键词总数 / JD 总数
        """
        if not jd_list or len(jd_list) == 0:
            return 0.0
        
        total_keyword_count = 0
        for jd in jd_list:
            result = self.count_keywords(jd)
            total_keyword_count += result['total_count']
        
        ai_intensity = total_keyword_count / len(jd_list)
        return round(ai_intensity, 4)
    
    def analyze_company_jds(self, company_name: str, jd_list: List[Dict]) -> Dict:
        """
        分析公司所有 JD 的 AI 强度
        jd_list: 每个元素包含 {'position': 职位名，'description': 职位描述}
        """
        if not jd_list:
            return {
                'company_name': company_name,
                'jd_total_count': 0,
                'ai_keyword_count': 0,
                'ai_intensity': 0.0,
                'has_ai_positions': False
            }
        
        descriptions = []
        total_ai_count = 0
        
        for jd in jd_list:
            desc = jd.get('description', '') or ''
            position = jd.get('position', '') or ''
            full_text = f"{position} {desc}"
            descriptions.append(full_text)
            
            result = self.count_keywords(full_text)
            total_ai_count += result['total_count']
        
        ai_intensity = total_ai_count / len(jd_list) if jd_list else 0
        
        return {
            'company_name': company_name,
            'jd_total_count': len(jd_list),
            'ai_keyword_count': total_ai_count,
            'ai_intensity': round(ai_intensity, 4),
            'has_ai_positions': total_ai_count > 0
        }
