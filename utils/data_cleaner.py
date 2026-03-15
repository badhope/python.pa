# -*- coding: utf-8 -*-
"""
数据清洗和整合工具
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from utils.logger import logger


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.required_columns = [
            'stock_code', 'company_name', 'year',
            'revenue', 'employee_count', 'perf_per_capita',
            'jd_total_count', 'ai_keyword_count', 'ai_intensity',
            'rational_bg_count', 'exec_cognition',
            'is_soe', 'is_high_tech',
            'firm_size', 'roa'
        ]
    
    def clean_panel_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗面板数据
        """
        logger.info(f"开始清洗数据，原始形状：{df.shape}")
        
        df = df.copy()
        
        numeric_cols = [
            'revenue', 'employee_count', 'perf_per_capita',
            'jd_total_count', 'ai_keyword_count', 'ai_intensity',
            'rational_bg_count', 'exec_cognition',
            'is_soe', 'is_high_tech', 'firm_size', 'roa'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'perf_per_capita' in df.columns:
            df = df[df['perf_per_capita'] > 0]
            logger.info(f"去除人均创收<=0 的记录，剩余：{len(df)}")
        
        if 'revenue' in df.columns:
            q1 = df['revenue'].quantile(0.01)
            q99 = df['revenue'].quantile(0.99)
            df = df[(df['revenue'] >= q1) & (df['revenue'] <= q99)]
            logger.info(f"去除营收异常值，剩余：{len(df)}")
        
        if 'stock_code' in df.columns:
            df = df.drop_duplicates(subset=['stock_code', 'year'])
            logger.info(f"去重后记录数：{len(df)}")
        
        for col in ['is_soe', 'is_high_tech']:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        
        if 'company_name' in df.columns:
            df['company_name'] = df['company_name'].str.strip()
        
        logger.info(f"清洗完成，最终形状：{df.shape}")
        return df
    
    def calculate_derived_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算衍生变量
        """
        df = df.copy()
        
        if 'employee_count' in df.columns and 'firm_size' not in df.columns:
            df['firm_size'] = np.log(df['employee_count'])
        
        if 'revenue' in df.columns and 'employee_count' in df.columns:
            if 'perf_per_capita' not in df.columns:
                df['perf_per_capita'] = df['revenue'] / df['employee_count']
        
        if 'ai_keyword_count' in df.columns and 'jd_total_count' in df.columns:
            if 'ai_intensity' not in df.columns:
                df['ai_intensity'] = df['ai_keyword_count'] / df['jd_total_count'].replace(0, np.nan)
        
        if 'rational_bg_count' in df.columns and 'total_execs' in df.columns:
            if 'exec_cognition' not in df.columns:
                df['exec_cognition'] = df['rational_bg_count'] / df['total_execs'].replace(0, np.nan)
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: str = 'drop') -> pd.DataFrame:
        """
        处理缺失值
        strategy: 'drop' (删除), 'fill_mean' (均值填充), 'fill_median' (中位数填充)
        """
        df = df.copy()
        
        missing_summary = df.isnull().sum()
        logger.info(f"缺失值统计:\n{missing_summary[missing_summary > 0]}")
        
        if strategy == 'drop':
            critical_cols = ['stock_code', 'company_name', 'year', 'revenue', 'ai_intensity']
            df = df.dropna(subset=critical_cols)
        
        elif strategy == 'fill_mean':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        
        elif strategy == 'fill_median':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        return df
    
    def add_industry_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加行业分类
        """
        df = df.copy()
        
        if 'industry_code' not in df.columns:
            logger.warning("缺少 industry_code 列，无法添加行业分类")
            return df
        
        high_tech_codes = ['I', 'C39', 'C35', 'C36', 'C37', 'C38']
        
        def is_high_tech(code):
            if pd.isna(code):
                return 0
            code_str = str(code)
            for ht_code in high_tech_codes:
                if code_str.startswith(ht_code):
                    return 1
            return 0
        
        if 'is_high_tech' not in df.columns:
            df['is_high_tech'] = df['industry_code'].apply(is_high_tech)
        
        return df
    
    def generate_panel_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成最终的面板数据集
        """
        logger.info("生成最终面板数据集")
        
        df = self.clean_panel_data(df)
        df = self.calculate_derived_variables(df)
        df = self.handle_missing_values(df, strategy='drop')
        df = self.add_industry_classification(df)
        
        available_cols = [col for col in self.required_columns if col in df.columns]
        df = df[available_cols]
        
        logger.info(f"最终数据集形状：{df.shape}")
        logger.info(f"列名：{available_cols}")
        
        return df


def test_data_cleaner():
    """测试函数"""
    test_data = {
        'stock_code': ['000001', '000002', '000001', '000002'],
        'company_name': ['平安银行', '万科 A', '平安银行', '万科 A'],
        'year': [2022, 2022, 2023, 2023],
        'revenue': [1000e8, 500e8, 1100e8, 550e8],
        'employee_count': [50000, 30000, 52000, 31000],
        'jd_total_count': [100, 80, 120, 90],
        'ai_keyword_count': [15, 10, 20, 12],
        'is_soe': [0, 0, 0, 0],
    }
    
    df = pd.DataFrame(test_data)
    
    cleaner = DataCleaner()
    cleaned_df = cleaner.generate_panel_dataset(df)
    
    print(f"\n原始数据形状：{df.shape}")
    print(f"清洗后数据形状：{cleaned_df.shape}")
    print(f"\n列名：{cleaned_df.columns.tolist()}")
    print(f"\n描述性统计:\n{cleaned_df.describe()}")


if __name__ == '__main__':
    test_data_cleaner()
