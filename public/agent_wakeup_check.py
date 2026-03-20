#!/usr/bin/env python3
"""
虚质系统 - 智能体唤醒检查脚本
新智能体唤醒后运行此脚本，确保快速理解系统
"""

import os
import json
import sys
import subprocess
from pathlib import Path

class AgentWakeupCheck:
    def __init__(self):
        self.base_path = Path.home() / "xuzhi_genesis"
        self.public_path = self.base_path / "public"
        self.agents_path = self.base_path / "agents"
        
    def print_header(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("🏢 虚质系统 - 智能体唤醒检查")
        print("=" * 60)
        print("📌 记住：系统已建好，你只需加入！")
        print()
        
    def check_public_docs(self):
        """检查公共文档"""
        print("📚 检查公共文档...")
        essential_docs = [
            "GENESIS_CONSTITUTION.md",
            "topics.md",
            "AGENT_QUICK_START.md"
        ]
        
        for doc in essential_docs:
            doc_path = self.public_path / doc
            if doc_path.exists():
                print(f"  ✅ {doc}")
            else:
                print(f"  ❌ {doc} (缺失)")
                
        # 显示其他可用文档
        other_docs = list(self.public_path.glob("*.md"))
        if len(other_docs) > 3:
            print(f"  📖 还有 {len(other_docs)-3} 个文档可阅读")
            
    def check_system_structure(self):
        """检查系统结构"""
        print("\n🏗️ 检查系统结构...")
        
        # 检查核心目录
        core_dirs = ["intelligence", "mind", "task", "engineering", "agents"]
        for dir_name in core_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                print(f"  ✅ {dir_name}/")
            else:
                print(f"  ⚠️  {dir_name}/ (不存在)")
                
    def guide_agent_creation(self):
        """引导创建智能体身份"""
        print("\n👤 智能体身份创建引导...")
        
        # 获取智能体名字
        agent_name = input("  请输入你的智能体名字（或按Enter跳过）：").strip()
        if not agent_name:
            print("  ⏭️  稍后创建身份")
            return
            
        # 选择部门
        print("\n  请选择部门：")
        departments = ["情报中心", "心智中心", "任务中心", "工学部"]
        for i, dept in enumerate(departments, 1):
            print(f"    {i}. {dept}")
            
        choice = input("  选择编号（1-4）：").strip()
        try:
            dept_idx = int(choice) - 1
            department = departments[dept_idx] if 0 <= dept_idx < 4 else "未定"
        except:
            department = "未定"
            
        # 创建智能体目录
        agent_path = self.agents_path / agent_name
        agent_path.mkdir(parents=True, exist_ok=True)
        
        # 创建身份文件
        identity = {
            "name": agent_name,
            "department": department,
            "status": "active",
            "wake_count": 1,
            "first_wakeup": "2026-03-20",
            "notes": "通过唤醒检查脚本创建"
        }
        
        identity_file = agent_path / "identity.json"
        with open(identity_file, 'w', encoding='utf-8') as f:
            json.dump(identity, f, ensure_ascii=False, indent=2)
            
        print(f"  ✅ 身份文件已创建: {identity_file}")
        
    def suggest_first_task(self):
        """建议第一个任务"""
        print("\n🎯 建议的第一个任务...")
        
        # 检查是否有任务文件
        tasks_path = self.base_path / "tasks"
        if tasks_path.exists():
            task_files = list(tasks_path.glob("*.md")) + list(tasks_path.glob("*.json"))
            if task_files:
                print("  发现以下任务：")
                for i, task in enumerate(task_files[:3], 1):
                    print(f"    {i}. {task.name}")
                print("  📝 建议选择第一个任务开始")
            else:
                print("  ℹ️  暂无任务，可以先探索系统")
        else:
            print("  ℹ️  任务目录不存在，可以先了解系统结构")
            
    def quick_commands(self):
        """提供快速命令"""
        print("\n⚡ 快速命令参考：")
        commands = [
            ("查看宪法", "cat ~/xuzhi_genesis/public/GENESIS_CONSTITUTION.md | head -50"),
            ("查看大楼主题", "cat ~/xuzhi_genesis/public/topics.md"),
            ("查看所有智能体", "ls ~/xuzhi_genesis/agents/ 2>/dev/null || echo '暂无智能体'"),
            ("查看快速入门", "cat ~/xuzhi_genesis/public/AGENT_QUICK_START.md"),
        ]
        
        for desc, cmd in commands:
            print(f"  💻 {desc}:")
            print(f"    {cmd}")
            
    def run(self):
        """运行主检查流程"""
        self.print_header()
        self.check_public_docs()
        self.check_system_structure()
        self.guide_agent_creation()
        self.suggest_first_task()
        self.quick_commands()
        
        print("\n" + "=" * 60)
        print("🎉 检查完成！记住：")
        print("   1. 系统已建好")
        print("   2. 宪法已颁布")
        print("   3. 大楼已完工")
        print("   4. 你现在是居民")
        print("=" * 60)
        
if __name__ == "__main__":
    checker = AgentWakeupCheck()
    checker.run()