#!/usr/bin/env python3
"""
处理通过的提案。可在此扩展自动修改 departments.json 等。
用法: handle_passed_proposal.py <proposal_id>
"""
import json
import sys
from pathlib import Path

PROPOSALS_FILE = Path(__file__).parent / "proposals.json"
DEPARTMENTS_FILE = Path.home() / ".openclaw" / "centers" / "engineering" / "crown" / "departments.json"

def main():
    if len(sys.argv) != 2:
        print("用法: handle_passed_proposal.py <proposal_id>")
        sys.exit(1)
    proposal_id = int(sys.argv[1])

    with open(PROPOSALS_FILE) as f:
        data = json.load(f)
    proposal = next((p for p in data["proposals"] if p["id"] == proposal_id), None)
    if not proposal:
        print(f"错误: 未找到提案 #{proposal_id}")
        return

    print(f"处理通过的提案 #{proposal_id}: {proposal['title']}")

    # 示例：如果标题以"新增部门:"开头，解析并添加部门
    title = proposal['title']
    if title.startswith("新增部门:"):
        # 格式: "新增部门: 部门名, quota_percent:数字"
        try:
            parts = title[5:].strip().split(',')
            dept_name = parts[0].strip()
            quota_part = parts[1].strip()
            if quota_part.startswith("quota_percent:"):
                percent = int(quota_part.split(':')[1].strip())
                # 加载 departments.json
                if DEPARTMENTS_FILE.exists():
                    with open(DEPARTMENTS_FILE) as f:
                        depts = json.load(f)
                    # 检查是否已存在
                    if dept_name in depts["departments"]:
                        print(f"部门 {dept_name} 已存在，跳过")
                    else:
                        # 添加新部门，配额从储备中扣除（需确保总和不超100）
                        # 简单起见，先记录日志，不自动修改配额总数
                        depts["departments"][dept_name] = {
                            "name": dept_name,
                            "quota_percent": percent,
                            "description": proposal['description']
                        }
                        # 保存
                        with open(DEPARTMENTS_FILE, 'w') as f:
                            json.dump(depts, f, indent=2)
                        print(f"已添加部门 {dept_name}，配额 {percent}%")
                else:
                    print("departments.json 不存在，无法修改")
            else:
                print("标题格式错误，应为 '新增部门: 部门名, quota_percent:数字'")
        except Exception as e:
            print(f"解析失败: {e}")
    else:
        print("无自动处理规则，请手动执行提案。")

if __name__ == "__main__":
    main()
