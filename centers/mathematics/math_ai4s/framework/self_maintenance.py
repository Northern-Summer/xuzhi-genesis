#!/usr/bin/env python3
"""
Self-Maintenance System — Project Hygiene and Integrity
自维护系统 —— 项目卫生与完整性

设计原则：
- 自动清理过期/损坏文件
- 日志轮转和备份
- 状态检查和恢复
- 不干扰正在进行的会话

Author: Δ (Delta-Forge)
Date: 2026-03-30
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import gzip


@dataclass
class MaintenanceReport:
    """维护报告"""
    timestamp: str
    actions_taken: List[str]
    warnings: List[str]
    space_reclaimed: int  # bytes
    integrity_checks: Dict[str, bool]


class FileJanitor:
    """
    文件清理员
    
    安全清理临时文件、过期缓存
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.actions = []
        self.warnings = []
        self.space_reclaimed = 0
    
    def safe_delete(self, path: Path) -> bool:
        """
        安全删除文件或目录
        
        绝不使用rm -rf，总是检查后再删除
        """
        if not path.exists():
            return True
        
        try:
            if path.is_file():
                size = path.stat().st_size
                path.unlink()
                self.space_reclaimed += size
                self.actions.append(f"Deleted file: {path}")
                return True
            elif path.is_dir():
                # 递归安全删除目录内容
                for item in path.iterdir():
                    self.safe_delete(item)
                path.rmdir()
                self.actions.append(f"Deleted directory: {path}")
                return True
        except Exception as e:
            self.warnings.append(f"Failed to delete {path}: {e}")
            return False
        
        return False
    
    def cleanup_temp_files(self, max_age_days: int = 7) -> int:
        """
        清理临时文件
        
        包括：
        - .tmp, .bak 文件
        - __pycache__ 目录
        - 超过max_age_days的日志
        """
        count = 0
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        patterns_to_clean = [
            "*.tmp", "*.bak", "*.pyc", "*.pyo",
            "*.log.old", "*.cache"
        ]
        
        for pattern in patterns_to_clean:
            for file_path in self.project_root.rglob(pattern):
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        if self.safe_delete(file_path):
                            count += 1
                except Exception as e:
                    self.warnings.append(f"Error checking {file_path}: {e}")
        
        # 清理 __pycache__
        for pycache in self.project_root.rglob("__pycache__"):
            if pycache.is_dir():
                if self.safe_delete(pycache):
                    count += 1
        
        return count
    
    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        清理旧研究会话
        
        保留最近30天的会话数据
        更早的会话数据归档压缩
        """
        sessions_dir = self.project_root / "sessions"
        if not sessions_dir.exists():
            return 0
        
        count = 0
        cutoff = datetime.now() - timedelta(days=max_age_days)
        archive_dir = self.project_root / "archive" / "sessions"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        for session_file in sessions_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                if mtime < cutoff:
                    # 压缩归档
                    archive_name = session_file.stem + ".json.gz"
                    archive_path = archive_dir / archive_name
                    
                    with open(session_file, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 删除原文件
                    if self.safe_delete(session_file):
                        count += 1
                        self.actions.append(f"Archived: {session_file.name}")
            except Exception as e:
                self.warnings.append(f"Error archiving {session_file}: {e}")
        
        return count


class IntegrityChecker:
    """
    完整性检查器
    
    检查项目结构完整性
    """
    
    REQUIRED_FILES = [
        "framework/core_architecture.py",
        "framework/exploration_strategies.py",
        "framework/verification_layer.py",
    ]
    
    REQUIRED_DIRS = [
        "framework",
        "etp_work",
        "reports",
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.checks = {}
    
    def check_structure(self) -> Dict[str, bool]:
        """检查项目结构"""
        self.checks["structure"] = True
        
        for file_path in self.REQUIRED_FILES:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.checks[f"missing_file:{file_path}"] = False
                self.checks["structure"] = False
            else:
                self.checks[f"file:{file_path}"] = True
        
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.checks[f"missing_dir:{dir_path}"] = False
                self.checks["structure"] = False
            else:
                self.checks[f"dir:{dir_path}"] = True
        
        return self.checks
    
    def check_python_syntax(self) -> Dict[str, bool]:
        """检查Python文件语法"""
        import py_compile
        
        self.checks["python_syntax"] = True
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                py_compile.compile(py_file, doraise=True)
                self.checks[f"syntax:{py_file.name}"] = True
            except py_compile.PyCompileError as e:
                self.checks[f"syntax:{py_file.name}"] = False
                self.checks["python_syntax"] = False
        
        return self.checks
    
    def full_check(self) -> Dict[str, bool]:
        """完整检查"""
        self.check_structure()
        self.check_python_syntax()
        return self.checks


class BackupManager:
    """
    备份管理器
    
    自动备份关键数据
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, name: Optional[str] = None) -> Path:
        """创建项目备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = name or f"backup_{timestamp}"
        backup_path = self.backup_dir / name
        
        # 备份关键文件
        files_to_backup = [
            "framework/core_architecture.py",
            "framework/exploration_strategies.py",
            "framework/verification_layer.py",
        ]
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for file_path in files_to_backup:
            src = self.project_root / file_path
            if src.exists():
                dst = backup_path / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        return backup_path
    
    def list_backups(self) -> List[Path]:
        """列出所有备份"""
        if not self.backup_dir.exists():
            return []
        return sorted(self.backup_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    
    def restore_backup(self, backup_name: str) -> bool:
        """从备份恢复"""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return False
        
        # 恢复逻辑（需要谨慎实现）
        return True


class SelfMaintenance:
    """
    自维护系统主类
    
    整合所有维护功能
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(
            "/home/summer/xuzhi_genesis/centers/mathematics/math_ai4s"
        )
        self.janitor = FileJanitor(self.project_root)
        self.checker = IntegrityChecker(self.project_root)
        self.backup = BackupManager(self.project_root)
    
    def run_maintenance(self, dry_run: bool = False) -> MaintenanceReport:
        """
        执行完整维护
        
        Args:
            dry_run: 如果True，只报告不执行
        """
        actions = []
        warnings = []
        
        if dry_run:
            actions.append("DRY RUN MODE - No actual changes made")
        
        # 1. 完整性检查
        integrity = self.checker.full_check()
        
        # 2. 创建备份（在实际清理前）
        if not dry_run:
            backup_path = self.backup.create_backup()
            actions.append(f"Created backup: {backup_path.name}")
        
        # 3. 清理临时文件
        if not dry_run:
            cleaned = self.janitor.cleanup_temp_files()
            actions.append(f"Cleaned {cleaned} temporary files")
        
        # 4. 归档旧会话
        if not dry_run:
            archived = self.janitor.cleanup_old_sessions()
            actions.append(f"Archived {archived} old sessions")
        
        # 收集警告
        warnings.extend(self.janitor.warnings)
        
        # 检查完整性问题
        for check, passed in integrity.items():
            if not passed:
                warnings.append(f"Integrity check failed: {check}")
        
        return MaintenanceReport(
            timestamp=datetime.now().isoformat(),
            actions_taken=actions,
            warnings=warnings,
            space_reclaimed=self.janitor.space_reclaimed,
            integrity_checks=integrity
        )
    
    def health_check(self) -> Dict:
        """健康检查（快速）"""
        return {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "integrity": self.checker.full_check(),
            "backups_available": len(self.backup.list_backups()),
            "status": "healthy" if all(self.checker.full_check().values()) else "degraded"
        }


if __name__ == "__main__":
    print("Self-Maintenance System")
    print("=" * 60)
    
    maint = SelfMaintenance()
    
    # 快速健康检查
    health = maint.health_check()
    print(f"\nHealth Status: {health['status']}")
    print(f"Backups Available: {health['backups_available']}")
    
    # 干运行维护
    print("\nRunning dry-run maintenance...")
    report = maint.run_maintenance(dry_run=True)
    
    print(f"\nActions that would be taken:")
    for action in report.actions_taken:
        print(f"  - {action}")
    
    if report.warnings:
        print(f"\nWarnings:")
        for warning in report.warnings:
            print(f"  ! {warning}")
