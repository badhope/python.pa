# -*- coding: utf-8 -*-
"""
高管背景分析器
分析高管简历中的理性学科背景
"""

import re
from typing import List, Dict, Optional
from config.keywords import RATIONAL_KEYWORDS, HUMANITIES_KEYWORDS, EXECUTIVE_TITLES, DEGREE_KEYWORDS
from utils.logger import logger


class ExecAnalyzer:
    """高管背景分析器"""
    
    def __init__(self):
        self.rational_keywords = RATIONAL_KEYWORDS
        self.humanities_keywords = HUMANITIES_KEYWORDS
        self.executive_titles = EXECUTIVE_TITLES
        self.degree_keywords = DEGREE_KEYWORDS
    
    def extract_education_info(self, resume_text: str) -> List[Dict]:
        """
        从简历文本中提取教育背景信息
        返回：教育经历列表 [{'degree': 学位，'major': 专业，'school': 学校}]
        """
        if not resume_text:
            return []
        
        educations = []
        
        education_keywords = ['毕业', '学位', '学历', '就读', '专业', '学院', '大学']
        
        lines = resume_text.split('\n')
        current_education = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_education_line = any(kw in line for kw in education_keywords)
            has_degree = any(kw in line for kw in self.degree_keywords)
            
            if is_education_line or has_degree:
                if current_education:
                    educations.append(current_education)
                    current_education = {}
                
                current_education['raw_text'] = line
                
                for degree_kw in self.degree_keywords:
                    if degree_kw in line:
                        current_education['degree'] = degree_kw
                        break
                
                for rational_kw in self.rational_keywords:
                    if rational_kw in line:
                        current_education['major'] = rational_kw
                        current_education['is_rational'] = True
                        break
                else:
                    for humanities_kw in self.humanities_keywords:
                        if humanities_kw in line:
                            current_education['major'] = humanities_kw
                            current_education['is_rational'] = False
                            break
        
        if current_education:
            educations.append(current_education)
        
        return educations
    
    def is_rational_major(self, major_text: str) -> bool:
        """
        判断专业是否属于理性学科
        """
        if not major_text:
            return False
        
        major_lower = major_text.lower()
        
        for rational_kw in self.rational_keywords:
            if rational_kw.lower() in major_lower:
                return True
        
        return False
    
    def has_rational_background(self, resume_text: str) -> bool:
        """
        判断该高管是否具有理性学科背景
        规则：若任一教育经历的专业属于理性学科，则标记为 1
        """
        if not resume_text:
            return False
        
        educations = self.extract_education_info(resume_text)
        
        for edu in educations:
            if edu.get('is_rational', False):
                return True
            
            major = edu.get('major', '')
            if major and self.is_rational_major(major):
                return True
        
        return False
    
    def analyze_executives(self, exec_list: List[Dict]) -> Dict:
        """
        分析高管团队的整体理性背景
        exec_list: [{'name': 姓名，'title': 职位，'resume': 简历文本}]
        返回：统计结果
        """
        if not exec_list:
            return {
                'total_execs': 0,
                'rational_bg_count': 0,
                'exec_cognition_ratio': 0.0,
                'has_rational_ceo': False,
                'details': []
            }
        
        rational_count = 0
        has_rational_ceo = False
        details = []
        
        for exec_info in exec_list:
            name = exec_info.get('name', '未知')
            title = exec_info.get('title', '')
            resume = exec_info.get('resume', '')
            
            is_rational = self.has_rational_background(resume)
            if is_rational:
                rational_count += 1
                
                if any(ceo_title in title.upper() for ceo_title in ['CEO', '总经理', '总裁', '董事长']):
                    has_rational_ceo = True
            
            details.append({
                'name': name,
                'title': title,
                'has_rational_bg': is_rational
            })
        
        total_execs = len(exec_list)
        exec_cognition_ratio = rational_count / total_execs if total_execs > 0 else 0
        
        return {
            'total_execs': total_execs,
            'rational_bg_count': rational_count,
            'exec_cognition_ratio': round(exec_cognition_ratio, 4),
            'has_rational_ceo': has_rational_ceo,
            'details': details
        }
    
    def extract_exec_info_from_text(self, text: str) -> List[Dict]:
        """
        从年报文本中提取高管信息
        这是一个简化版本，实际需要根据年报格式调整
        """
        execs = []
        
        lines = text.split('\n')
        current_exec = {}
        
        for line in lines:
            line = line.strip()
            
            for title in self.executive_titles:
                if title in line:
                    if current_exec:
                        execs.append(current_exec)
                        current_exec = {}
                    
                    current_exec['title'] = title
                    
                    name_match = re.search(r'([A-Za-z·]{2,10})', line)
                    if name_match:
                        current_exec['name'] = name_match.group(1)
                    
                    current_exec['resume'] = line
                    break
        
        if current_exec:
            execs.append(current_exec)
        
        return execs
