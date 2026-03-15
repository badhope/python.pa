"""
第三阶段：数据清洗与变量构建
功能：
1. 数据清洗（剔除关键变量缺失样本）
2. 变量计算
3. 缩尾处理（1% 和 99% Winsorize）
4. 生成最终数据集
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# ==================== 配置 ====================
INPUT_FILE = 'data/raw_data_800.csv'
OUTPUT_FILE = 'data/final_panel_data.csv'
LOG_FILE = 'data/cleaning_log.txt'

# ==================== 缩尾处理函数 ====================
def winsorize_series(series, lower=0.01, upper=0.99):
    """
    对连续变量进行缩尾处理（Winsorize）
    """
    quantiles = series.quantile([lower, upper])
    return series.clip(quantiles[lower], quantiles[upper])

# ==================== 主流程 ====================
def main():
    print("=" * 70)
    print("第三阶段：数据清洗与变量构建")
    print("=" * 70)
    print(f"\n开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 读取原始数据
    print("\n" + "=" * 70)
    print("步骤 1: 读取原始数据")
    print("=" * 70)
    
    if not os.path.exists(INPUT_FILE):
        print(f"\n错误：文件 {INPUT_FILE} 不存在！")
        return
    
    df = pd.read_csv(INPUT_FILE)
    print(f"\n原始数据量：{len(df)} 家公司")
    print(f"原始列名：{list(df.columns)}")
    
    # 2. 数据清洗
    print("\n" + "=" * 70)
    print("步骤 2: 数据清洗")
    print("=" * 70)
    
    # 记录清洗日志
    log_lines = []
    log_lines.append(f"数据清洗日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_lines.append("=" * 70 + "\n")
    log_lines.append(f"原始数据量：{len(df)} 家公司\n\n")
    
    # 2.1 检查关键变量缺失
    key_vars = ['revenue', 'employee_count', 'total_assets', 'net_profit', 
                'rational_bg_count', 'exec_cognition', 'ai_intensity']
    
    missing_count = df[key_vars].isnull().sum()
    print("\n关键变量缺失统计：")
    for var in key_vars:
        print(f"  - {var}: {missing_count[var]} 个缺失值")
        if missing_count[var] > 0:
            log_lines.append(f"变量 {var} 缺失：{missing_count[var]} 个\n")
    
    # 2.2 剔除关键变量缺失的样本
    df_clean = df.dropna(subset=key_vars)
    dropped = len(df) - len(df_clean)
    print(f"\n剔除关键变量缺失样本：{dropped} 家")
    log_lines.append(f"\n剔除关键变量缺失样本：{dropped} 家\n")
    
    if dropped > 0:
        log_lines.append("剔除的样本详情：\n")
        dropped_df = df[~df.index.isin(df_clean.index)]
        for idx, row in dropped_df.iterrows():
            log_lines.append(f"  - {row['stock_code']} {row['company_name']}: ")
            missing_vars = [var for var in key_vars if pd.isnull(row[var])]
            log_lines.append(f"缺失变量：{', '.join(missing_vars)}\n")
    
    # 2.3 检查异常值（营收、员工数为负或零）
    abnormal = df_clean[(df_clean['revenue'] <= 0) | (df_clean['employee_count'] <= 0)]
    if len(abnormal) > 0:
        print(f"\n发现异常值（营收或员工数<=0）：{len(abnormal)} 家")
        log_lines.append(f"\n异常值样本：{len(abnormal)} 家\n")
        df_clean = df_clean[(df_clean['revenue'] > 0) & (df_clean['employee_count'] > 0)]
        log_lines.append(f"剔除异常值样本：{len(abnormal)} 家\n")
    
    print(f"\n清洗后数据量：{len(df_clean)} 家公司")
    print(f"有效样本率：{len(df_clean)/len(df)*100:.2f}%")
    
    # 3. 变量构建
    print("\n" + "=" * 70)
    print("步骤 3: 变量构建")
    print("=" * 70)
    
    # 3.1 人均创收（performance per capita）
    df_clean['perf_per_capita'] = df_clean['revenue'] / df_clean['employee_count']
    print("\n✓ 人均创收 (perf_per_capita) = 营收 / 员工数")
    
    # 3.2 企业规模（lnSize）
    df_clean['firm_size'] = np.log(df_clean['total_assets'])
    print("✓ 企业规模 (firm_size) = ln(总资产)")
    
    # 3.3 ROA（资产回报率）- 如果原始数据没有，则计算
    if 'roa' not in df_clean.columns or df_clean['roa'].isnull().all():
        df_clean['roa'] = df_clean['net_profit'] / df_clean['total_assets']
        print("✓ ROA = 净利润 / 总资产")
    
    # 3.4 产权性质虚拟变量（is_soe 已经是 0/1）
    df_clean['soe'] = df_clean['is_soe'].astype(int)
    print("✓ 产权性质 (soe) = 国企虚拟变量 (1=国企，0=民企)")
    
    # 3.5 高管理性背景比例
    df_clean['exec_cognition'] = df_clean['rational_bg_count'] / df_clean['total_execs']
    print("✓ 高管认知 (exec_cognition) = 理性背景高管数 / 高管总数")
    
    # 4. 缩尾处理
    print("\n" + "=" * 70)
    print("步骤 4: 缩尾处理 (Winsorize 1% 和 99%)")
    print("=" * 70)
    
    continuous_vars = ['perf_per_capita', 'firm_size', 'roa', 'ai_intensity', 'exec_cognition']
    
    for var in continuous_vars:
        original_mean = df_clean[var].mean()
        df_clean[var] = winsorize_series(df_clean[var], lower=0.01, upper=0.99)
        new_mean = df_clean[var].mean()
        print(f"\n{var}:")
        print(f"  缩尾前均值：{original_mean:.4f}")
        print(f"  缩尾后均值：{new_mean:.4f}")
        log_lines.append(f"\n变量 {var} 缩尾处理：\n")
        log_lines.append(f"  缩尾前均值：{original_mean:.4f}\n")
        log_lines.append(f"  缩尾后均值：{new_mean:.4f}\n")
    
    # 5. 保存最终数据集
    print("\n" + "=" * 70)
    print("步骤 5: 保存最终数据集")
    print("=" * 70)
    
    # 选择最终需要的列
    final_columns = [
        'stock_code', 'company_name', 'year',
        'ai_intensity',           # 核心解释变量
        'perf_per_capita',        # 被解释变量
        'exec_cognition',         # 调节变量 1
        'soe',                    # 调节变量 2
        'firm_size',              # 控制变量
        'roa',                    # 控制变量
        'total_execs',            # 高管总数
        'rational_bg_count',      # 理性背景高管数
        'revenue',                # 原始变量
        'employee_count',         # 原始变量
        'total_assets',           # 原始变量
        'net_profit'              # 原始变量
    ]
    
    # 检查列是否存在
    available_columns = [col for col in final_columns if col in df_clean.columns]
    df_final = df_clean[available_columns].copy()
    
    # 保存
    df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✓ 最终数据集已保存：{OUTPUT_FILE}")
    print(f"✓ 最终样本量：{len(df_final)} 家公司")
    print(f"✓ 变量数量：{len(final_columns)} 个")
    
    # 6. 描述性统计
    print("\n" + "=" * 70)
    print("步骤 6: 描述性统计")
    print("=" * 70)
    
    desc_stats = df_final[continuous_vars].describe()
    print("\n连续变量描述性统计：")
    print(desc_stats)
    
    # 保存描述性统计
    desc_stats.to_csv('data/Table_1_Descriptive_Stats.csv', encoding='utf-8-sig')
    print(f"\n✓ 描述性统计已保存：data/Table_1_Descriptive_Stats.csv")
    
    # 分类变量统计
    print("\n分类变量统计：")
    print(f"  - 国企 (soe=1): {df_final['soe'].sum()} 家 ({df_final['soe'].mean()*100:.2f}%)")
    print(f"  - 民企 (soe=0): {len(df_final) - df_final['soe'].sum()} 家 ({(1-df_final['soe'].mean())*100:.2f}%)")
    
    # 7. 保存清洗日志
    log_lines.append("\n" + "=" * 70 + "\n")
    log_lines.append(f"最终数据量：{len(df_final)} 家公司\n")
    log_lines.append(f"有效样本率：{len(df_final)/len(df)*100:.2f}%\n")
    log_lines.append("\n最终变量列表：\n")
    for col in available_columns:
        log_lines.append(f"  - {col}\n")
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)
    print(f"\n✓ 清洗日志已保存：{LOG_FILE}")
    
    # 8. 数据预览
    print("\n" + "=" * 70)
    print("数据预览 (前 5 行)")
    print("=" * 70)
    print(df_final.head())
    
    print("\n" + "=" * 70)
    print("✓ 第三阶段完成！")
    print("=" * 70)
    print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n输出文件：")
    print(f"  1. {OUTPUT_FILE} - 最终面板数据集")
    print(f"  2. data/Table_1_Descriptive_Stats.csv - 描述性统计")
    print(f"  3. {LOG_FILE} - 清洗日志")
    
    return df_final

if __name__ == "__main__":
    df_final = main()
