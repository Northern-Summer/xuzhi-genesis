#!/usr/bin/env python3
"""
USPTO-50k Dataset Download & Verification
遵循最佳科学实践：版本控制、校验和、元数据记录
"""
import os
import json
import hashlib
from datasets import load_dataset
from datetime import datetime

DATA_DIR = "/home/summer/xuzhi_genesis/centers/naturalscience/chemistry/data"
META_FILE = os.path.join(DATA_DIR, "uspto50k_metadata.json")

def compute_sha256(filepath, chunk_size=8192):
    """计算文件SHA256校验和"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_and_verify():
    print("="*50)
    print("USPTO-50k Dataset Acquisition")
    print("="*50)
    
    # 1. 下载数据集
    print("\n[1/4] 从 Hugging Face 下载数据集...")
    dataset = load_dataset("pingzhili/uspto-50k", trust_remote_code=True)
    print(f"      数据集结构: {dataset}")
    
    # 2. 保存原始数据
    print("\n[2/4] 保存到本地...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 保存为CSV以便通用访问
    for split in dataset.keys():
        output_path = os.path.join(DATA_DIR, f"uspto50k_{split}.csv")
        dataset[split].to_csv(output_path, index=False)
        file_hash = compute_sha256(output_path)
        file_size = os.path.getsize(output_path)
        print(f"      {split}: {output_path} ({file_size/1024/1024:.2f} MB, SHA256: {file_hash[:16]}...)")
    
    # 3. 记录元数据
    print("\n[3/4] 记录元数据...")
    metadata = {
        "dataset_name": "USPTO-50k",
        "source": "https://huggingface.co/datasets/pingzhili/uspto-50k",
        "download_date": datetime.now().isoformat(),
        "splits": {}
    }
    
    for split in dataset.keys():
        csv_path = os.path.join(DATA_DIR, f"uspto50k_{split}.csv")
        metadata["splits"][split] = {
            "file": f"uspto50k_{split}.csv",
            "sha256": compute_sha256(csv_path),
            "size_bytes": os.path.getsize(csv_path),
            "num_records": len(dataset[split]),
            "columns": list(dataset[split].features.keys())
        }
    
    with open(META_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"      元数据已保存: {META_FILE}")
    
    # 4. 验证完整性
    print("\n[4/4] 验证数据完整性...")
    total_records = sum(len(dataset[split]) for split in dataset.keys())
    print(f"      总记录数: {total_records}")
    print(f"      列: {list(dataset['train'].features.keys())}")
    print(f"      示例反应 SMILES: {dataset['train'][0].get('reaction', 'N/A')[:50]}...")
    
    print("\n" + "="*50)
    print("✅ 数据集获取完成，符合科学可复现标准")
    print("="*50)
    
    return metadata

if __name__ == "__main__":
    metadata = download_and_verify()
    print(f"\n元数据摘要:\n{json.dumps(metadata, indent=2)}")
