#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xuzhi File System Guardian - The First Epoch (Patch 1)
遵循【幂等性死律】，并彻底免疫权限升降级造成的路径漂移陷阱。
"""

import os
import pwd
import shutil
import tarfile
import hashlib
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------
# 绝对真理锚点：无论是否 sudo，强制指向 summer 用户实体
# ---------------------------------------------------------
try:
    SUMMER_INFO = pwd.getpwnam("summer")
except KeyError:
    print("[FATAL] 操作系统中不存在 'summer' 用户。守护进程拒绝启动。")
    exit(1)

SYS_USER_UID = SUMMER_INFO.pw_uid
SYS_USER_GID = SUMMER_INFO.pw_gid
ROOT = Path(SUMMER_INFO.pw_dir) / "xuzhi_genesis"

LOG_DIR = ROOT / "logs"
BACKUP_DIR = ROOT / "backups"
ARCHIVE_DIR = ROOT / "archive"

def enforce_ownership(path: Path):
    """强制将属主修正回 summer"""
    os.chown(str(path), SYS_USER_UID, SYS_USER_GID)
    for p in path.rglob("*"):
        os.chown(str(p), SYS_USER_UID, SYS_USER_GID)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = LOG_DIR / "fs_guardian.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    os.chown(str(log_file), SYS_USER_UID, SYS_USER_GID)

def get_file_hash(filepath: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def idempotent_archive(src_path: Path, subdir_name: str):
    if ARCHIVE_DIR in src_path.parents:
        return

    target_dir = ARCHIVE_DIR / subdir_name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_path = target_dir / src_path.name

    if target_path.exists():
        src_hash = get_file_hash(src_path)
        tgt_hash = get_file_hash(target_path)
        
        if src_hash == tgt_hash and src_hash != "":
            src_path.unlink()
            log(f"[IDEMPOTENT] 湮灭重复文件: {src_path}")
            return
        else:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            target_path = target_dir / f"{src_path.stem}_{timestamp}{src_path.suffix}"

    shutil.move(str(src_path), str(target_path))
    log(f"[ARCHIVE] 转移: {src_path} -> {target_path}")

def atomic_tar_backup(target_dir: Path):
    if not target_dir.is_dir():
        return
        
    tar_path = BACKUP_DIR / f"{target_dir.name}.tar.gz"
    tmp_tar_path = BACKUP_DIR / f"{target_dir.name}.tar.gz.tmp"

    if tar_path.exists():
        log(f"[IDEMPOTENT] 备份已存在，跳过: {tar_path}")
        return

    try:
        with tarfile.open(tmp_tar_path, "w:gz") as tar:
            tar.add(target_dir, arcname=target_dir.name)
        tmp_tar_path.rename(tar_path)
        shutil.rmtree(target_dir)
        log(f"[BACKUP] 打包完成: {target_dir} -> {tar_path}")
    except Exception as e:
        if tmp_tar_path.exists():
            tmp_tar_path.unlink()
        log(f"[ERROR] 打包失败: {target_dir} | {e}")

def main():
    if not ROOT.exists():
        ROOT.mkdir(parents=True, exist_ok=True)
        enforce_ownership(ROOT)

    log("=== 物理拓扑检查启动 ===")
    
    for d in [LOG_DIR, BACKUP_DIR, ARCHIVE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    for ext in ["*.bak", "*~"]:
        for f in ROOT.rglob(ext):
            if f.is_file():
                idempotent_archive(f, "tmp_graveyard")

    for item in BACKUP_DIR.iterdir():
        if item.is_dir():
            atomic_tar_backup(item)

    for center in ["intelligence", "mind", "task", "engineering"]:
        center_dir = ROOT / "centers" / center
        if not center_dir.exists():
            continue
        for pattern in ["evolve_*", "deploy_*", "enhance_*"]:
            for f in center_dir.glob(pattern):
                if f.is_file():
                    idempotent_archive(f, "script_graveyard")

    for f in ROOT.rglob("*"):
        if f.is_symlink() and not f.exists():
            f.unlink()
            log(f"[CLEANUP] 湮灭死链: {f}")

    enforce_ownership(ROOT)
    log("=== 物理拓扑检查完成 ===")

if __name__ == "__main__":
    main()
