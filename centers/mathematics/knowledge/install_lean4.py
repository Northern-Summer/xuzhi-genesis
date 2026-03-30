#!/usr/bin/env python3
"""
Lean 4 安装脚本 - 绕过 WSL2 DNS 污染
"""

import urllib.request
import urllib.error
import ssl
import os
import sys
import tarfile
import json
import subprocess

# 忽略 SSL 验证
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

GITHUB_IP = "20.205.243.166"
API_GITHUB_IP = "140.82.121.6"

def get_latest_version():
    """获取最新版本"""
    req = urllib.request.Request(
        f"https://{API_GITHUB_IP}/repos/leanprover/lean4/releases/latest",
        headers={"Host": "api.github.com", "User-Agent": "Python"}
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as resp:
            data = json.loads(resp.read())
            version = data.get('tag_name', '')
            print(f"Latest version: {version}")
            return version
    except Exception as e:
        print(f"Failed: {e}")
        return "v4.29.0"

def download_lean(version):
    """下载 Lean 4"""
    # 正确的文件名格式: lean-4.29.0-linux.tar.zst
    ver_num = version[1:]  # 去掉 'v' 前缀
    filename = f"lean-{ver_num}-linux.tar.zst"
    url_path = f"/leanprover/lean4/releases/download/{version}/{filename}"
    
    req = urllib.request.Request(
        f"https://{GITHUB_IP}{url_path}",
        headers={"Host": "github.com", "User-Agent": "Python"}
    )
    
    output_file = f"/tmp/{filename}"
    
    print(f"\nDownloading {filename}...")
    print(f"From: github.com{url_path}")
    
    try:
        # 使用 opener 处理重定向
        opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler()
        )
        
        with opener.open(req, timeout=180) as resp:
            final_url = resp.geturl()
            if final_url != req.full_url:
                print(f"Redirected to: {final_url[:80]}...")
            
            total_size = int(resp.headers.get('Content-Length', 0))
            if total_size > 0:
                print(f"Size: {total_size / 1024 / 1024:.1f} MB")
            
            data = resp.read()
            print(f"Downloaded: {len(data)} bytes")
            
            if len(data) < 10000:
                print(f"ERROR: Too small ({len(data)} bytes)")
                return None
            
            with open(output_file, 'wb') as f:
                f.write(data)
            
            print(f"Saved: {output_file}")
            return output_file
            
    except Exception as e:
        print(f"Download error: {e}")
        return None

def extract_lean(tar_file):
    """解压 tar.zst 文件"""
    extract_dir = os.path.expanduser("~/.local/share/lean4")
    os.makedirs(extract_dir, exist_ok=True)
    
    print(f"\nExtracting to {extract_dir}...")
    
    # 检查是否有 zstd
    if subprocess.run(["which", "zstd"], capture_output=True).returncode != 0:
        print("zstd not found, installing...")
        subprocess.run(["sudo", "apt-get", "install", "-y", "zstd"], check=False)
    
    try:
        # 先用 zstd 解压成 tar
        tar_path = tar_file.replace('.zst', '')
        subprocess.run(["zstd", "-d", "-f", tar_file, "-o", tar_path], check=True)
        
        # 然后解压 tar
        with tarfile.open(tar_path, "r:") as tar:
            tar.extractall(extract_dir)
        
        print("Extracted successfully")
        return extract_dir
    except Exception as e:
        print(f"Extract error: {e}")
        return None

def setup_path(extract_dir):
    """设置 PATH"""
    # 找到 lean 二进制
    bin_dir = None
    for root, dirs, files in os.walk(extract_dir):
        if 'lean' in files:
            bin_dir = root
            break
    
    if not bin_dir:
        bin_dir = os.path.join(extract_dir, "bin")
    
    print(f"\nLean binary at: {bin_dir}")
    print(f"Add to PATH:")
    print(f'  export PATH="{bin_dir}:$PATH"')
    
    # 添加到 .bashrc
    bashrc = os.path.expanduser("~/.bashrc")
    with open(bashrc, 'a') as f:
        f.write(f'\n# Lean 4\nexport PATH="{bin_dir}:$PATH"\n')
    print(f"Added to {bashrc}")

if __name__ == "__main__":
    print("=" * 60)
    print("Lean 4 安装脚本")
    print("=" * 60)
    
    version = get_latest_version()
    tar_file = download_lean(version)
    
    if tar_file:
        extract_dir = extract_lean(tar_file)
        if extract_dir:
            setup_path(extract_dir)
            print("\n✓ 安装完成")
            print("运行: source ~/.bashrc")
        else:
            print("\n✗ 解压失败")
            sys.exit(1)
    else:
        print("\n✗ 下载失败")
        sys.exit(1)
