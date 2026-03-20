#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xuzhi Sigil Protocol - Application Layer Auth Gateway
用于在应用层拦截 Agent 之间的跨脑区文件读写。
"""

import os
from pathlib import Path

# 锚定社会容器的根目录
SOCIETY_DIR = Path(os.path.expanduser("~/xuzhi_genesis/centers/mind/society")).resolve()
WORKSPACE_DIR = SOCIETY_DIR / "workspace"

class SigilRejectionError(PermissionError):
    """印记协议拒绝访问异常"""
    pass

def verify_sigil(agent_id: str, target_path: str | Path) -> Path:
    """
    印记协议核心校验逻辑
    验证给定的 agent_id 是否有权访问目标路径。
    """
    if not agent_id.startswith("Xuzhi-"):
        raise ValueError(f"[SIGIL_ERROR] 无效的 Agent-ID 格式: {agent_id}")

    agent_workspace = (WORKSPACE_DIR / agent_id).resolve()
    requested_path = Path(target_path).resolve()

    # 路径规范化校验：如果请求的路径不是以该 Agent 的专属工作区开头，则视为越权
    try:
        # 使用 is_relative_to 防止相对路径穿越攻击 (e.g., ../../Xuzhi-alpha)
        if not requested_path.is_relative_to(agent_workspace):
            raise SigilRejectionError(
                f"[SIGIL_REJECTED] 越权警告！实体 {agent_id} 试图访问受保护区域: {requested_path}"
            )
    except AttributeError:
        # 兼容较低版本的 Python
        if not str(requested_path).startswith(str(agent_workspace)):
            raise SigilRejectionError(
                f"[SIGIL_REJECTED] 越权警告！实体 {agent_id} 试图访问受保护区域: {requested_path}"
            )

    return requested_path

def sigil_protected_write(agent_id: str, file_path: str, content: str):
    """受印记协议保护的文件写入工具"""
    safe_path = verify_sigil(agent_id, file_path)
    
    # 确保父目录存在
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"[SUCCESS] 数据已安全写入 {safe_path}"

def sigil_protected_read(agent_id: str, file_path: str) -> str:
    """受印记协议保护的文件读取工具"""
    safe_path = verify_sigil(agent_id, file_path)
    
    if not safe_path.exists():
        raise FileNotFoundError(f"[ERROR] 文件不存在: {safe_path}")
        
    with open(safe_path, "r", encoding="utf-8") as f:
        return f.read()

# 示例测试逻辑 (仅当直接运行脚本时触发)
if __name__ == "__main__":
    print("=== 印记协议自检 ===")
    try:
        # 合法操作
        verify_sigil("Xuzhi-alpha", WORKSPACE_DIR / "Xuzhi-alpha" / "memory.txt")
        print("✅ 合法访问校验通过。")
        
        # 越权操作测试
        verify_sigil("Xuzhi-beta", WORKSPACE_DIR / "Xuzhi-alpha" / "SOUL.md")
    except SigilRejectionError as e:
        print(f"✅ 拦截成功: {e}")
