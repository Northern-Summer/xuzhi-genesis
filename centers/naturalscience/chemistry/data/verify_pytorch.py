#!/usr/bin/env python3
"""
PyTorch GPU/CPU 环境验证
记录硬件状态，为后续优化提供依据
"""
import torch
import json
import os

print("="*60)
print("PyTorch 硬件环境验证")
print("="*60)

# 基本信息
print(f"\n[PyTorch 版本]")
print(f"  {torch.__version__}")

# CUDA 可用性
cuda_available = torch.cuda.is_available()
print(f"\n[CUDA 支持]")
print(f"  可用: {cuda_available}")

if cuda_available:
    print(f"  CUDA版本: {torch.version.cuda}")
    print(f"  GPU数量: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"    显存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
else:
    print(f"  状态: 当前使用CPU模式")
    print(f"  说明: 逆合成模型将使用CPU推理")

# CPU 信息
print(f"\n[CPU 信息]")
print(f"  线程数: {torch.get_num_threads()}")
print(f"  建议: 设置torch.set_num_threads(4)优化性能")

# 内存测试
print(f"\n[内存测试]")
try:
    # 测试能否创建典型大小的张量
    test_tensor = torch.randn(1000, 1000)  # 约4MB
    print(f"  测试张量(1000x1000): 创建成功")
    
    # 模拟分子图 batch
    batch_size = 32
    node_dim = 64
    edge_dim = 32
    max_nodes = 50
    
    node_feat = torch.randn(batch_size, max_nodes, node_dim)
    print(f"  模拟分子图batch ({batch_size}, {max_nodes}, {node_dim}): 创建成功")
    print(f"  预估内存占用: ~{batch_size * max_nodes * node_dim * 4 / 1024**2:.2f} MB")
    
except Exception as e:
    print(f"  错误: {e}")

# 保存报告
report = {
    "pytorch_version": torch.__version__,
    "cuda_available": cuda_available,
    "device": "cuda" if cuda_available else "cpu",
    "num_threads": torch.get_num_threads(),
    "verification_date": "2026-03-30",
    "status": "verified"
}

DATA_DIR = "/home/summer/xuzhi_genesis/centers/naturalscience/chemistry/data"
os.makedirs(DATA_DIR, exist_ok=True)
report_path = os.path.join(DATA_DIR, "pytorch_env_report.json")
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n[报告保存]")
print(f"  {report_path}")

print("\n" + "="*60)
print("✅ PyTorch环境验证完成")
print("="*60)
print(f"\n结论: 使用{report['device'].upper()}模式运行")
if not cuda_available:
    print("优化策略: 使用小batch、模型量化、减少hidden_dim")
