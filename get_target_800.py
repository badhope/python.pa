# -*- coding: utf-8 -*-
"""
第一阶段：获取800家上市公司目标名单
功能：获取沪深300、中证500、中证1000成分股，清洗筛选后生成目标名单
作者：AI Assistant
日期：2026-03-15
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')


def check_akshare_installation():
    """
    检查 akshare 库是否已安装
    """
    try:
        import akshare as ak
        print("✓ akshare 库已安装")
        print(f"  版本：{ak.__version__}")
        return True
    except ImportError:
        print("✗ akshare 库未安装")
        print("\n安装命令：")
        print("  pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return False


def get_index_constituents(index_name, max_retries=3):
    """
    获取指数成分股列表
    
    参数：
        index_name: 指数名称（'沪深300', '中证500', '中证1000'）
        max_retries: 最大重试次数
    
    返回：
        DataFrame: 成分股列表（code, name）
    """
    import akshare as ak
    import time
    
    print(f"\n正在获取 {index_name} 成分股...")
    
    for attempt in range(max_retries):
        try:
            # 根据指数名称选择对应的接口
            if index_name == '沪深300':
                df = ak.index_stock_cons_weight_csindex(symbol='000300')
            elif index_name == '中证500':
                df = ak.index_stock_cons_weight_csindex(symbol='000905')
            elif index_name == '中证1000':
                df = ak.index_stock_cons_weight_csindex(symbol='000852')
            else:
                print(f"✗ 不支持的指数：{index_name}")
                return pd.DataFrame()
            
            # 提取股票代码和名称
            if '成分券代码' in df.columns and '成分券名称' in df.columns:
                result = df[['成分券代码', '成分券名称']].copy()
                result.columns = ['code', 'name']
            elif '股票代码' in df.columns and '股票名称' in df.columns:
                result = df[['股票代码', '股票名称']].copy()
                result.columns = ['code', 'name']
            else:
                # 尝试其他可能的列名
                print(f"  警告：未找到标准列名，尝试自动识别...")
                result = df.iloc[:, :2].copy()
                result.columns = ['code', 'name']
            
            print(f"✓ 成功获取 {len(result)} 只股票")
            return result
            
        except Exception as e:
            print(f"✗ 第 {attempt+1} 次尝试失败：{e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"✗ {index_name} 获取失败，已达最大重试次数")
                return pd.DataFrame()


def clean_stock_list(df):
    """
    清洗股票列表
    
    清洗规则：
    1. 剔除 ST、*ST 股票
    2. 剔除退市股票
    3. 去除重复项
    4. 标准化股票代码格式
    
    参数：
        df: 原始股票列表 DataFrame
    
    返回：
        DataFrame: 清洗后的股票列表
    """
    print("\n开始清洗股票列表...")
    initial_count = len(df)
    
    # 1. 去除重复项
    df = df.drop_duplicates(subset=['code'], keep='first')
    print(f"  去重：{initial_count} → {len(df)}")
    
    # 2. 剔除 ST、*ST 股票
    st_mask = df['name'].str.contains('ST|退市', case=False, na=False)
    df = df[~st_mask]
    print(f"  剔除 ST/退市：{len(df)}")
    
    # 3. 标准化股票代码（6位数字）
    df['code'] = df['code'].astype(str).str.zfill(6)
    
    # 4. 剔除无效代码（非6位数字）
    valid_mask = df['code'].str.match(r'^\d{6}$')
    df = df[valid_mask]
    print(f"  有效代码：{len(df)}")
    
    # 5. 去除名称中的特殊字符
    df['name'] = df['name'].str.strip()
    
    print(f"✓ 清洗完成：{initial_count} → {len(df)}")
    
    return df.reset_index(drop=True)


def get_industry_info(stock_codes):
    """
    获取股票行业信息
    
    参数：
        stock_codes: 股票代码列表
    
    返回：
        DataFrame: 包含行业信息的股票列表
    """
    import akshare as ak
    import time
    
    print("\n正在获取行业信息...")
    
    try:
        # 尝试获取行业分类数据
        print("  尝试方法 1：使用 ak.stock_board_industry_name_em()...")
        try:
            industry_df = ak.stock_board_industry_name_em()
            print(f"  ✓ 成功获取行业分类数据：{len(industry_df)} 条")
            
            # 提取股票代码和行业
            if '股票代码' in industry_df.columns:
                result = industry_df[['股票代码', '股票名称', '行业名称']].copy()
                result.columns = ['code', 'name', 'industry']
                result['code'] = result['code'].astype(str).str.zfill(6)
                return result
        except Exception as e:
            print(f"  ✗ 方法 1 失败：{e}")
        
        # 备用方法：逐个查询（较慢）
        print("  尝试方法 2：逐个查询行业信息（较慢）...")
        result_list = []
        
        for i, code in enumerate(stock_codes[:100]):  # 先测试前100个
            try:
                df = ak.stock_individual_info_em(symbol=code)
                if not df.empty:
                    industry = df[df['item'] == '行业']['value'].values[0] if '行业' in df['item'].values else '未知'
                    result_list.append({'code': code, 'industry': industry})
                
                if (i + 1) % 10 == 0:
                    print(f"    进度：{i+1}/{len(stock_codes[:100])}")
                    time.sleep(1)
                    
            except Exception as e:
                result_list.append({'code': code, 'industry': '未知'})
        
        if result_list:
            return pd.DataFrame(result_list)
        
    except Exception as e:
        print(f"  ✗ 获取行业信息失败：{e}")
        print("  将使用默认行业分类")
    
    # 如果所有方法都失败，返回空行业
    return pd.DataFrame({'code': stock_codes, 'industry': ['未知'] * len(stock_codes)})


def create_backup_data():
    """
    创建备用数据（当网络接口失败时使用）
    
    返回：
        DataFrame: 备用股票列表
    """
    print("\n使用备用数据方案...")
    
    # 预设的沪深300部分成分股（示例）
    backup_data = {
        'code': [
            '600519', '600036', '601318', '600000', '600030',
            '601166', '600887', '600276', '600048', '600104',
        ],
        'name': [
            '贵州茅台', '招商银行', '中国平安', '浦发银行', '中信证券',
            '兴业银行', '伊利股份', '恒瑞医药', '保利发展', '上汽集团',
        ],
        'industry': [
            '食品饮料', '银行', '保险', '银行', '证券',
            '银行', '食品饮料', '医药生物', '房地产', '汽车',
        ]
    }
    
    df = pd.DataFrame(backup_data)
    print(f"✓ 已加载备用数据：{len(df)} 只股票")
    print("  注意：备用数据仅包含示例股票，建议检查网络连接后重试")
    
    return df


def main():
    """
    主函数：获取并清洗800家上市公司名单
    """
    print("=" * 70)
    print("第一阶段：获取800家上市公司目标名单")
    print("=" * 70)
    
    # 1. 检查 akshare 库
    if not check_akshare_installation():
        print("\n请先安装 akshare 库后再运行")
        return None
    
    import akshare as ak
    
    # 2. 获取三大指数成分股
    all_stocks = []
    
    indices = ['沪深300', '中证500', '中证1000']
    
    for index_name in indices:
        df = get_index_constituents(index_name)
        if not df.empty:
            df['source_index'] = index_name
            all_stocks.append(df)
        else:
            print(f"⚠ {index_name} 获取失败，继续下一个...")
    
    # 3. 合并所有股票
    if all_stocks:
        combined_df = pd.concat(all_stocks, ignore_index=True)
        print(f"\n合并后总数：{len(combined_df)} 只股票")
    else:
        print("\n✗ 所有指数获取失败，使用备用数据")
        combined_df = create_backup_data()
    
    # 4. 清洗股票列表
    cleaned_df = clean_stock_list(combined_df)
    
    # 5. 获取行业信息
    try:
        industry_df = get_industry_info(cleaned_df['code'].tolist())
        
        if not industry_df.empty and 'industry' in industry_df.columns:
            # 合并行业信息
            final_df = cleaned_df.merge(industry_df[['code', 'industry']], on='code', how='left')
            final_df['industry'] = final_df['industry'].fillna('未知')
        else:
            final_df = cleaned_df.copy()
            final_df['industry'] = '未知'
    except Exception as e:
        print(f"\n⚠ 获取行业信息时出错：{e}")
        final_df = cleaned_df.copy()
        final_df['industry'] = '未知'
    
    # 6. 限制为800家（如果超过）
    if len(final_df) > 800:
        print(f"\n股票数量超过800家，将随机选取800家...")
        final_df = final_df.sample(n=800, random_state=42).sort_values('code').reset_index(drop=True)
    
    # 7. 保存结果
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'target_800.csv')
    final_df[['code', 'name', 'industry']].to_csv(
        output_file,
        index=False,
        encoding='utf-8-sig'
    )
    
    print("\n" + "=" * 70)
    print("✓ 第一阶段完成！")
    print("=" * 70)
    print(f"\n最终股票数量：{len(final_df)} 家")
    print(f"输出文件：{output_file}")
    
    # 8. 显示统计信息
    print("\n统计信息：")
    print(f"  - 总股票数：{len(final_df)}")
    print(f"  - 行业分布：")
    industry_counts = final_df['industry'].value_counts().head(10)
    for industry, count in industry_counts.items():
        print(f"      {industry}: {count} 家")
    
    # 9. 显示前10条记录
    print("\n前10条记录：")
    print(final_df[['code', 'name', 'industry']].head(10).to_string(index=False))
    
    return final_df


if __name__ == '__main__':
    result = main()
    
    if result is not None:
        print("\n" + "=" * 70)
        print("下一步操作：")
        print("=" * 70)
        print("1. 检查生成的文件：data/target_800.csv")
        print("2. 运行第二阶段：python main_scraper.py")
        print("=" * 70)
