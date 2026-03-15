"""
第四阶段：统计分析与绘图
功能：
1. 相关性热力图
2. OLS 回归分析（含交互项）
3. 调节效应可视化
4. VIF 检验
5. 生成回归结果表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 配置 ====================
INPUT_FILE = 'data/final_panel_data.csv'
OUTPUT_DIR = 'data/analysis_results'

# ==================== 主流程 ====================
def main():
    print("=" * 70)
    print("第四阶段：统计分析与绘图")
    print("=" * 70)
    print(f"\n开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. 读取数据
    print("\n" + "=" * 70)
    print("步骤 1: 读取数据")
    print("=" * 70)
    
    df = pd.read_csv(INPUT_FILE)
    print(f"\n✓ 数据量：{len(df)} 家公司")
    print(f"✓ 变量：{list(df.columns)}")
    
    # 2. 相关性分析
    print("\n" + "=" * 70)
    print("步骤 2: 相关性分析")
    print("=" * 70)
    
    # 选择分析变量
    analysis_vars = ['perf_per_capita', 'ai_intensity', 'exec_cognition', 'soe', 
                     'firm_size', 'roa']
    
    corr_matrix = df[analysis_vars].corr()
    print("\n变量相关性矩阵：")
    print(corr_matrix.round(4))
    
    # 保存相关性矩阵
    corr_matrix.to_csv(f'{OUTPUT_DIR}/correlation_matrix.csv', encoding='utf-8-sig')
    print(f"\n✓ 相关性矩阵已保存")
    
    # 绘制相关性热力图
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='RdYlBu', center=0, 
                fmt='.3f', square=True, linewidths=0.5,
                cbar_kws={'shrink': 0.8})
    plt.title('变量相关性热力图', fontsize=16, fontweight='bold')
    plt.xticks(fontsize=10, rotation=45, ha='right')
    plt.yticks(fontsize=10)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/Fig_1_Correlation_Heatmap.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ 相关性热力图已保存：{OUTPUT_DIR}/Fig_1_Correlation_Heatmap.png")
    
    # 3. OLS 回归分析
    print("\n" + "=" * 70)
    print("步骤 3: OLS 回归分析")
    print("=" * 70)
    
    # 模型 1: 主效应模型
    print("\n【模型 1】主效应模型")
    print("-" * 70)
    
    X1 = df[['ai_intensity', 'exec_cognition', 'soe', 'firm_size', 'roa']]
    X1 = sm.add_constant(X1)
    y1 = df['perf_per_capita']
    
    model1 = sm.OLS(y1, X1).fit(cov_type='HC3')  # 使用稳健标准误
    
    print(model1.summary())
    
    # 模型 2: 加入交互项（调节效应）
    print("\n【模型 2】调节效应模型（加入交互项）")
    print("-" * 70)
    
    # 创建交互项
    df['ai_x_cognition'] = df['ai_intensity'] * df['exec_cognition']
    df['ai_x_soe'] = df['ai_intensity'] * df['soe']
    
    X2 = df[['ai_intensity', 'exec_cognition', 'soe', 'ai_x_cognition', 'ai_x_soe', 
             'firm_size', 'roa']]
    X2 = sm.add_constant(X2)
    y2 = df['perf_per_capita']
    
    model2 = sm.OLS(y2, X2).fit(cov_type='HC3')
    
    print(model2.summary())
    
    # 模型 3: 分组回归（国企 vs 民企）
    print("\n【模型 3】分组回归")
    print("-" * 70)
    
    # 国企组
    soe_df = df[df['soe'] == 1]
    if len(soe_df) > 10:
        X3_soe = soe_df[['ai_intensity', 'exec_cognition', 'firm_size', 'roa']]
        X3_soe = sm.add_constant(X3_soe)
        y3_soe = soe_df['perf_per_capita']
        model3_soe = sm.OLS(y3_soe, X3_soe).fit(cov_type='HC3')
        print("\n国企组 (N={}):".format(len(soe_df)))
        print(model3_soe.summary())
    else:
        print("\n国企组样本不足")
        model3_soe = None
    
    # 民企组
    private_df = df[df['soe'] == 0]
    if len(private_df) > 10:
        X3_private = private_df[['ai_intensity', 'exec_cognition', 'firm_size', 'roa']]
        X3_private = sm.add_constant(X3_private)
        y3_private = private_df['perf_per_capita']
        model3_private = sm.OLS(y3_private, X3_private).fit(cov_type='HC3')
        print("\n民企组 (N={}):".format(len(private_df)))
        print(model3_private.summary())
    else:
        print("\n民企组样本不足")
        model3_private = None
    
    # 4. 保存回归结果
    print("\n" + "=" * 70)
    print("步骤 4: 保存回归结果")
    print("=" * 70)
    
    # 提取回归结果
    results_summary = []
    
    # 模型 1
    results_summary.append({
        'Variable': 'const',
        'Model1_Coef': model1.params['const'],
        'Model1_Pval': model1.pvalues['const'],
        'Model1_Coef_str': f"{model1.params['const']:.4f}",
        'Model2_Coef': model2.params['const'],
        'Model2_Pval': model2.pvalues['const'],
        'Model2_Coef_str': f"{model2.params['const']:.4f}"
    })
    
    for var in ['ai_intensity', 'exec_cognition', 'soe', 'firm_size', 'roa']:
        row = {
            'Variable': var,
            'Model1_Coef': model1.params[var],
            'Model1_Pval': model1.pvalues[var],
            'Model1_Coef_str': format_coef(model1.params[var], model1.pvalues[var]),
            'Model2_Coef': model2.params[var],
            'Model2_Pval': model2.pvalues[var],
            'Model2_Coef_str': format_coef(model2.params[var], model2.pvalues[var])
        }
        results_summary.append(row)
    
    # 交互项
    for var in ['ai_x_cognition', 'ai_x_soe']:
        row = {
            'Variable': var,
            'Model1_Coef': np.nan,
            'Model1_Pval': np.nan,
            'Model1_Coef_str': '-',
            'Model2_Coef': model2.params[var],
            'Model2_Pval': model2.pvalues[var],
            'Model2_Coef_str': format_coef(model2.params[var], model2.pvalues[var])
        }
        results_summary.append(row)
    
    # R-squared
    results_summary.append({
        'Variable': 'R-squared',
        'Model1_Coef': model1.rsquared,
        'Model1_Pval': np.nan,
        'Model1_Coef_str': f"{model1.rsquared:.4f}",
        'Model2_Coef': model2.rsquared,
        'Model2_Pval': np.nan,
        'Model2_Coef_str': f"{model2.rsquared:.4f}"
    })
    
    results_summary.append({
        'Variable': 'Adj. R-squared',
        'Model1_Coef': model1.rsquared_adj,
        'Model1_Pval': np.nan,
        'Model1_Coef_str': f"{model1.rsquared_adj:.4f}",
        'Model2_Coef': model2.rsquared_adj,
        'Model2_Pval': np.nan,
        'Model2_Coef_str': f"{model2.rsquared_adj:.4f}"
    })
    
    results_summary.append({
        'Variable': 'Observations',
        'Model1_Coef': int(model1.nobs),
        'Model1_Pval': np.nan,
        'Model1_Coef_str': str(int(model1.nobs)),
        'Model2_Coef': int(model2.nobs),
        'Model2_Pval': np.nan,
        'Model2_Coef_str': str(int(model2.nobs))
    })
    
    results_df = pd.DataFrame(results_summary)
    results_df.to_csv(f'{OUTPUT_DIR}/Table_2_Regression_Results.csv', 
                      index=False, encoding='utf-8-sig')
    print(f"✓ 回归结果表已保存：{OUTPUT_DIR}/Table_2_Regression_Results.csv")
    
    # 5. VIF 检验
    print("\n" + "=" * 70)
    print("步骤 5: VIF 多重共线性检验")
    print("=" * 70)
    
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X2.columns
    vif_data["VIF"] = [variance_inflation_factor(X2.values, i) 
                       for i in range(X2.shape[1])]
    
    print("\nVIF 检验结果：")
    print(vif_data)
    
    vif_data.to_csv(f'{OUTPUT_DIR}/VIF_Test.csv', index=False, encoding='utf-8-sig')
    print(f"\n✓ VIF 检验结果已保存")
    
    # 判断多重共线性
    max_vif = vif_data["VIF"].max()
    if max_vif > 10:
        print(f"\n⚠ 警告：存在严重多重共线性 (max VIF = {max_vif:.2f})")
    elif max_vif > 5:
        print(f"\n⚠ 注意：存在中度多重共线性 (max VIF = {max_vif:.2f})")
    else:
        print(f"\n✓ 多重共线性在可接受范围内 (max VIF = {max_vif:.2f})")
    
    # 6. 调节效应可视化
    print("\n" + "=" * 70)
    print("步骤 6: 调节效应可视化")
    print("=" * 70)
    
    # 图 2: AI 强度 × 高管认知 对人均创收的影响
    plt.figure(figsize=(10, 8))
    
    # 分组：高管认知高低组
    cognition_median = df['exec_cognition'].median()
    df['cognition_high'] = (df['exec_cognition'] >= cognition_median).astype(int)
    
    # 按 AI 强度三分组
    ai_low = df['ai_intensity'].quantile(0.33)
    ai_high = df['ai_intensity'].quantile(0.67)
    
    df['ai_group'] = pd.cut(df['ai_intensity'], 
                            bins=[-np.inf, ai_low, ai_high, np.inf],
                            labels=['低 AI', '中 AI', '高 AI'])
    
    # 绘制交互效应图
    sns.boxplot(data=df, x='ai_group', y='perf_per_capita', 
                hue='cognition_high', palette='Set2')
    plt.xlabel('AI 招聘强度', fontsize=12, fontweight='bold')
    plt.ylabel('人均创收 (万元)', fontsize=12, fontweight='bold')
    plt.title('高管认知的调节效应', fontsize=14, fontweight='bold')
    plt.legend(['民企认知低', '民企认知高'], loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/Fig_2_Moderation_Effect.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ 调节效应图已保存：{OUTPUT_DIR}/Fig_2_Moderation_Effect.png")
    
    # 图 3: 产权性质的调节效应
    plt.figure(figsize=(10, 6))
    
    # 按产权性质分组
    group_means = df.groupby(['soe', 'ai_group'])['perf_per_capita'].mean().unstack()
    
    group_means.plot(kind='bar', figsize=(10, 6), color=['#FF6B6B', '#4ECDC4'])
    plt.xlabel('产权性质', fontsize=12, fontweight='bold')
    plt.ylabel('人均创收 (均值)', fontsize=12, fontweight='bold')
    plt.title('产权性质的调节效应', fontsize=14, fontweight='bold')
    plt.legend(['低 AI', '中 AI', '高 AI'], loc='upper left')
    plt.xticks([0, 1], ['民企', '国企'], rotation=0)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/Fig_3_SOE_Moderation.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ 产权性质调节效应图已保存：{OUTPUT_DIR}/Fig_3_SOE_Moderation.png")
    
    # 7. 生成分析摘要
    print("\n" + "=" * 70)
    print("步骤 7: 生成分析摘要")
    print("=" * 70)
    
    summary_text = generate_analysis_summary(df, model1, model2, vif_data)
    with open(f'{OUTPUT_DIR}/analysis_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary_text)
    print(f"✓ 分析摘要已保存：{OUTPUT_DIR}/analysis_summary.txt")
    
    print("\n" + "=" * 70)
    print("✓ 第四阶段完成！")
    print("=" * 70)
    print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n输出文件：")
    print(f"  1. {OUTPUT_DIR}/Fig_1_Correlation_Heatmap.png - 相关性热力图")
    print(f"  2. {OUTPUT_DIR}/Fig_2_Moderation_Effect.png - 调节效应图")
    print(f"  3. {OUTPUT_DIR}/Fig_3_SOE_Moderation.png - 产权性质调节效应")
    print(f"  4. {OUTPUT_DIR}/Table_2_Regression_Results.csv - 回归结果表")
    print(f"  5. {OUTPUT_DIR}/VIF_Test.csv - VIF 检验结果")
    print(f"  6. {OUTPUT_DIR}/analysis_summary.txt - 分析摘要")
    
    return model1, model2

def format_coef(coef, pval):
    """格式化回归系数（带显著性星号）"""
    if pd.isna(coef):
        return '-'
    
    stars = ''
    if pval < 0.01:
        stars = '***'
    elif pval < 0.05:
        stars = '**'
    elif pval < 0.1:
        stars = '*'
    
    return f"{coef:.4f}{stars}"

def generate_analysis_summary(df, model1, model2, vif_data):
    """生成分析摘要"""
    summary = []
    summary.append("=" * 70 + "\n")
    summary.append("实证分析摘要报告\n")
    summary.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    summary.append("=" * 70 + "\n\n")
    
    # 样本描述
    summary.append("【样本描述】\n")
    summary.append(f"  - 总样本量：{len(df)} 家公司\n")
    summary.append(f"  - 国企：{df['soe'].sum()} 家 ({df['soe'].mean()*100:.2f}%)\n")
    summary.append(f"  - 民企：{len(df) - df['soe'].sum()} 家 ({(1-df['soe'].mean())*100:.2f}%)\n\n")
    
    # 描述性统计
    summary.append("【主要变量描述性统计】\n")
    summary.append(f"  - AI 强度：均值={df['ai_intensity'].mean():.4f}, 标准差={df['ai_intensity'].std():.4f}\n")
    summary.append(f"  - 人均创收：均值={df['perf_per_capita'].mean()/10000:.2f}万元，标准差={df['perf_per_capita'].std()/10000:.2f}万元\n")
    summary.append(f"  - 高管认知：均值={df['exec_cognition'].mean():.4f}, 标准差={df['exec_cognition'].std():.4f}\n\n")
    
    # 回归结果
    summary.append("【回归分析主要发现】\n\n")
    
    summary.append("模型 1（主效应）：\n")
    summary.append(f"  - AI 强度系数：{model1.params['ai_intensity']:.4f} ")
    if model1.pvalues['ai_intensity'] < 0.01:
        summary.append("(p<0.01 ***)\n")
    elif model1.pvalues['ai_intensity'] < 0.05:
        summary.append("(p<0.05 **)\n")
    elif model1.pvalues['ai_intensity'] < 0.1:
        summary.append("(p<0.1 *)\n")
    else:
        summary.append("(不显著)\n")
    
    summary.append(f"  - R² = {model1.rsquared:.4f}, 调整 R² = {model1.rsquared_adj:.4f}\n\n")
    
    summary.append("模型 2（调节效应）：\n")
    summary.append(f"  - AI×认知交互项系数：{model2.params['ai_x_cognition']:.4f} ")
    if model2.pvalues['ai_x_cognition'] < 0.01:
        summary.append("(p<0.01 ***)\n")
    elif model2.pvalues['ai_x_cognition'] < 0.05:
        summary.append("(p<0.05 **)\n")
    elif model2.pvalues['ai_x_cognition'] < 0.1:
        summary.append("(p<0.1 *)\n")
    else:
        summary.append("(不显著)\n")
    
    summary.append(f"  - AI×产权交互项系数：{model2.params['ai_x_soe']:.4f} ")
    if model2.pvalues['ai_x_soe'] < 0.01:
        summary.append("(p<0.01 ***)\n")
    elif model2.pvalues['ai_x_soe'] < 0.05:
        summary.append("(p<0.05 **)\n")
    elif model2.pvalues['ai_x_soe'] < 0.1:
        summary.append("(p<0.1 *)\n")
    else:
        summary.append("(不显著)\n")
    
    summary.append(f"  - R² = {model2.rsquared:.4f}, 调整 R² = {model2.rsquared_adj:.4f}\n\n")
    
    # VIF 检验
    summary.append("【多重共线性检验】\n")
    summary.append(f"  - 最大 VIF 值：{vif_data['VIF'].max():.4f}\n")
    if vif_data['VIF'].max() < 5:
        summary.append("  - 结论：不存在严重多重共线性问题\n\n")
    else:
        summary.append("  - 结论：存在一定多重共线性，需谨慎解释\n\n")
    
    # 研究结论
    summary.append("【主要研究结论】\n")
    summary.append("  1. AI 招聘强度对企业人均创收的影响：\n")
    if model1.pvalues['ai_intensity'] < 0.05:
        if model1.params['ai_intensity'] > 0:
            summary.append("     AI 招聘强度显著正向影响企业人均创收\n")
        else:
            summary.append("     AI 招聘强度显著负向影响企业人均创收\n")
    else:
        summary.append("     AI 招聘强度对企业人均创收的影响不显著\n")
    
    summary.append("\n  2. 高管认知的调节效应：\n")
    if model2.pvalues['ai_x_cognition'] < 0.05:
        if model2.params['ai_x_cognition'] > 0:
            summary.append("     高管理性认知正向调节 AI 招聘与绩效的关系\n")
            summary.append("     即：高管理性背景越强，AI 招聘的积极效应越明显\n")
        else:
            summary.append("     高管理性认知负向调节 AI 招聘与绩效的关系\n")
    else:
        summary.append("     高管认知的调节效应不显著\n")
    
    summary.append("\n  3. 产权性质的调节效应：\n")
    if model2.pvalues['ai_x_soe'] < 0.05:
        if model2.params['ai_x_soe'] > 0:
            summary.append("     产权性质正向调节 AI 招聘与绩效的关系\n")
            summary.append("     即：国企中 AI 招聘的积极效应更强\n")
        else:
            summary.append("     产权性质负向调节 AI 招聘与绩效的关系\n")
            summary.append("     即：民企中 AI 招聘的积极效应更强\n")
    else:
        summary.append("     产权性质的调节效应不显著\n")
    
    summary.append("\n" + "=" * 70 + "\n")
    
    return ''.join(summary)

if __name__ == "__main__":
    model1, model2 = main()
