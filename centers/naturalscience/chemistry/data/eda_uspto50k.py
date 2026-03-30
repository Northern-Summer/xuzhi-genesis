#!/usr/bin/env python3
"""
USPTO-50k Exploratory Data Analysis (EDA)
最佳实践：数据质量检查、分布分析、科学记录
"""
import pandas as pd
import json
from collections import Counter
from rdkit import Chem
from rdkit.Chem import Descriptors
import numpy as np

DATA_DIR = "/home/summer/xuzhi_genesis/centers/naturalscience/chemistry/data"

def analyze_dataset():
    print("="*60)
    print("USPTO-50k 数据集探索性分析 (EDA)")
    print("="*60)
    
    # 加载数据
    train_df = pd.read_csv(f"{DATA_DIR}/uspto50k_train.csv")
    val_df = pd.read_csv(f"{DATA_DIR}/uspto50k_validation.csv")
    
    print(f"\n[数据规模]")
    print(f"  训练集: {len(train_df):,} 条反应")
    print(f"  验证集: {len(val_df):,} 条反应")
    print(f"  总计: {len(train_df) + len(val_df):,} 条反应")
    
    # 反应类型分布
    print(f"\n[反应类型分布]")
    rxn_class_dist = train_df['class'].value_counts().head(10)
    print("  Top 10 反应类别 (训练集):")
    for cls, count in rxn_class_dist.items():
        print(f"    Class {cls}: {count:,} ({count/len(train_df)*100:.1f}%)")
    
    # SMILES 有效性检查
    print(f"\n[SMILES 有效性检查]")
    valid_prods = 0
    invalid_prods = 0
    atom_counts = []
    
    for smiles in train_df['prod_smiles'].head(1000):  # 抽样检查前1000条
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                valid_prods += 1
                atom_counts.append(mol.GetNumAtoms())
            else:
                invalid_prods += 1
        except:
            invalid_prods += 1
    
    print(f"  抽样检查 (n=1000):")
    print(f"    有效 SMILES: {valid_prods} ({valid_prods/1000*100:.1f}%)")
    print(f"    无效/解析失败: {invalid_prods} ({invalid_prods/1000*100:.1f}%)")
    print(f"    产物平均原子数: {np.mean(atom_counts):.1f} ± {np.std(atom_counts):.1f}")
    print(f"    原子数范围: {min(atom_counts)} - {max(atom_counts)}")
    
    # 反应SMILES格式分析
    print(f"\n[反应SMILES格式]")
    sample_rxn = train_df['rxn_smiles'].iloc[0]
    print(f"  示例: {sample_rxn[:80]}...")
    
    # 统计反应物数量
    reactant_counts = []
    for rxn in train_df['rxn_smiles'].head(500):
        if '>>' in rxn:
            reactants = rxn.split('>>')[0].split('.')
            reactant_counts.append(len(reactants))
    
    print(f"  平均反应物数量: {np.mean(reactant_counts):.1f}")
    print(f"  反应物数量分布: {dict(Counter(reactant_counts))}")
    
    # 科学记录
    print(f"\n[科学记录]")
    eda_report = {
        "dataset": "USPTO-50k",
        "analysis_date": "2026-03-30",
        "total_reactions": len(train_df) + len(val_df),
        "train_val_split": f"{len(train_df)/len(val_df):.1f}:1",
        "reaction_classes": int(train_df['class'].nunique()),
        "smiles_validity_sample": {
            "sample_size": 1000,
            "valid": valid_prods,
            "valid_rate": f"{valid_prods/1000*100:.1f}%"
        },
        "avg_atoms_per_product": round(float(np.mean(atom_counts)), 1),
        "avg_reactants_per_reaction": round(float(np.mean(reactant_counts)), 1)
    }
    
    report_path = f"{DATA_DIR}/uspto50k_eda_report.json"
    with open(report_path, 'w') as f:
        json.dump(eda_report, f, indent=2)
    
    print(f"  EDA报告已保存: {report_path}")
    print("\n" + "="*60)
    print("✅ 数据质量检查完成")
    print("="*60)

if __name__ == "__main__":
    analyze_dataset()
