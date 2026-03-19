#!/usr/bin/env python3
"""
图书馆种子生成器（增强版）
功能：扫描 Windows 图书馆，将书籍分块生成种子文件
支持格式：PDF, EPUB, MOBI, AZW3, TXT, MD, DOCX, DOC, HTML, RTF, RAR, ZIP
增强特性：
- 更健壮的文件读取，多种方法回退
- 支持压缩包内文件
- 智能分块（基于段落，保持语义完整性）
- 错误捕获和日志记录
"""
import os
import re
import json
import sqlite3
import hashlib
import argparse
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from collections import deque

# 配置
LIBRARY_ROOT = Path("/mnt/library")
SEEDS_DIR = Path(__file__).parent / "seeds" / "library"
DB_PATH = Path(__file__).parent / "library_index.db"
LOG_PATH = Path(__file__).parent / "library_seed.log"
MAX_TOKENS = 2048  # 每块最大 token 数（约 8000 字符）
SUPPORTED_EXTS = {'.pdf', '.epub', '.mobi', '.azw3', '.txt', '.md', 
                  '.docx', '.doc', '.html', '.htm', '.rtf', '.zip', '.rar'}

# 设置日志
logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 尝试导入各种库，失败则记录
LIB_STATUS = {}
try:
    import pdfplumber
    LIB_STATUS['pdfplumber'] = True
except:
    LIB_STATUS['pdfplumber'] = False

try:
    import ebooklib
    from ebooklib import epub
    LIB_STATUS['ebooklib'] = True
except:
    LIB_STATUS['ebooklib'] = False

try:
    from bs4 import BeautifulSoup
    LIB_STATUS['bs4'] = True
except:
    LIB_STATUS['bs4'] = False

try:
    import docx
    LIB_STATUS['docx'] = True
except:
    LIB_STATUS['docx'] = False

try:
    import rarfile
    LIB_STATUS['rarfile'] = True
except:
    LIB_STATUS['rarfile'] = False

try:
    import zipfile
    LIB_STATUS['zipfile'] = True
except:
    LIB_STATUS['zipfile'] = False

try:
    import chardet
    LIB_STATUS['chardet'] = True
except:
    LIB_STATUS['chardet'] = False

def log_lib_status():
    logging.info("库状态: " + json.dumps(LIB_STATUS))

log_lib_status()

# 初始化数据库
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            mtime TEXT,
            size INTEGER,
            hash TEXT,
            processed_time TEXT,
            chunk_count INTEGER,
            error TEXT
        )
    ''')
    conn.commit()
    return conn

# 计算文件哈希（用于检测内容变化）
def file_hash(path):
    hasher = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"计算哈希失败 {path}: {e}")
        return None

# 估算 token 数（粗略 4 字符 = 1 token）
def estimate_tokens(text):
    return len(text) // 4

# 智能分块：按段落合并，尽量保持语义完整，不超过 MAX_TOKENS
def chunk_text(text, max_tokens=MAX_TOKENS):
    if not text:
        return []
    # 按双换行分割段落
    paragraphs = text.split('\n\n')
    chunks = []
    current = []
    current_tokens = 0
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_tokens = estimate_tokens(para)
        # 如果单个段落超过最大限制，强制拆分（按句子）
        if para_tokens > max_tokens:
            # 简单按句号分割
            sentences = re.split(r'(?<=[。！？])', para)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                sent_tokens = estimate_tokens(sent)
                if current_tokens + sent_tokens > max_tokens and current:
                    chunks.append('\n\n'.join(current))
                    current = []
                    current_tokens = 0
                current.append(sent)
                current_tokens += sent_tokens
        else:
            if current_tokens + para_tokens > max_tokens and current:
                chunks.append('\n\n'.join(current))
                current = []
                current_tokens = 0
            current.append(para)
            current_tokens += para_tokens
    if current:
        chunks.append('\n\n'.join(current))
    return chunks

# 检测文件编码
def detect_encoding(file_path):
    if LIB_STATUS.get('chardet'):
        try:
            with open(file_path, 'rb') as f:
                raw = f.read(10000)
                result = chardet.detect(raw)
                return result['encoding']
        except:
            pass
    return 'utf-8'

# 提取文本（增强版）
def extract_text(file_path):
    ext = file_path.suffix.lower()
    text = ""
    logging.info(f"开始提取 {file_path}")
    
    # 通用方法：尝试用 pandoc 转换（如果安装）
    try:
        result = subprocess.run(['pandoc', str(file_path), '-t', 'plain'], 
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout:
            text = result.stdout
            logging.info(f"pandoc 提取成功 {file_path}")
    except:
        pass
    
    if text:
        return text
    
    # 格式特定方法
    try:
        if ext == '.txt' or ext == '.md':
            enc = detect_encoding(file_path)
            with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                text = f.read()
        elif ext == '.pdf':
            if LIB_STATUS['pdfplumber']:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages[:50]:  # 限制页数
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
            else:
                # 回退：pdftotext
                try:
                    result = subprocess.run(['pdftotext', '-layout', str(file_path), '-'], 
                                           capture_output=True, text=True, timeout=30)
                    text = result.stdout
                except:
                    pass
        elif ext == '.epub':
            if LIB_STATUS['ebooklib']:
                import ebooklib
                from ebooklib import epub
                book = epub.read_epub(file_path)
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        content = item.get_content().decode('utf-8', errors='ignore')
                        if LIB_STATUS['bs4']:
                            soup = BeautifulSoup(content, 'html.parser')
                            text += soup.get_text() + "\n"
                        else:
                            text += content
        elif ext in ['.mobi', '.azw3']:
            # 使用 pandoc（通常支持）
            try:
                result = subprocess.run(['pandoc', str(file_path), '-t', 'plain'], 
                                       capture_output=True, text=True, timeout=30)
                text = result.stdout
            except:
                pass
        elif ext in ['.docx', '.doc']:
            if LIB_STATUS['docx']:
                import docx
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            else:
                # 回退：pandoc
                try:
                    result = subprocess.run(['pandoc', str(file_path), '-t', 'plain'], 
                                           capture_output=True, text=True, timeout=30)
                    text = result.stdout
                except:
                    pass
        elif ext in ['.html', '.htm']:
            if LIB_STATUS['bs4']:
                with open(file_path, 'r', encoding=detect_encoding(file_path), errors='ignore') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    text = soup.get_text()
            else:
                with open(file_path, 'r', encoding=detect_encoding(file_path), errors='ignore') as f:
                    text = f.read()
        elif ext == '.rtf':
            try:
                result = subprocess.run(['unrtf', '--text', str(file_path)], 
                                       capture_output=True, text=True, timeout=30)
                text = result.stdout
            except:
                pass
        elif ext in ['.zip', '.rar']:
            # 处理压缩包：提取所有文本文件
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                if ext == '.zip' and LIB_STATUS['zipfile']:
                    import zipfile
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        zf.extractall(tmp_path)
                elif ext == '.rar' and LIB_STATUS['rarfile']:
                    import rarfile
                    with rarfile.RarFile(file_path, 'r') as rf:
                        rf.extractall(tmp_path)
                else:
                    return ""
                # 递归提取文本文件
                for root, _, files in os.walk(tmp_path):
                    for f in files:
                        sub_file = Path(root) / f
                        sub_ext = sub_file.suffix.lower()
                        if sub_ext in {'.txt', '.md', '.pdf', '.docx'}:
                            sub_text = extract_text(sub_file)  # 递归调用，但只处理少量
                            if sub_text:
                                text += f"\n--- {sub_file.name} ---\n" + sub_text[:5000] + "\n"
    except Exception as e:
        logging.error(f"提取异常 {file_path}: {e}")
    
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    logging.info(f"提取完成 {file_path}, 长度 {len(text)}")
    return text

# 生成种子文件
def generate_seed(file_path, chunks, file_info):
    rel_path = str(file_path.relative_to(LIBRARY_ROOT))
    base_name = file_path.stem
    for idx, chunk in enumerate(chunks):
        # 创建种子文件名
        seed_name = f"library_{hashlib.md5((rel_path + str(idx)).encode()).hexdigest()[:8]}.md"
        seed_path = SEEDS_DIR / seed_name
        # 种子内容：包含来源元数据和块文本
        content = f"""<!--
source: {rel_path}
chunk: {idx}
total_chunks: {len(chunks)}
modified: {file_info['mtime']}
hash: {file_info['hash']}
-->

{chunk}
"""
        with open(seed_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"生成种子: {seed_name} (块 {idx+1}/{len(chunks)})")

# 获取所有文件，跳过不可访问的路径
def get_all_files():
    all_files = []
    for ext in SUPPORTED_EXTS:
        try:
            # 使用 os.walk 手动遍历以捕获 I/O 错误
            for root, dirs, files in os.walk(str(LIBRARY_ROOT)):
                root_path = Path(root)
                # 过滤目录名（例如跳过以 . 开头的隐藏目录）
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.lower().endswith(ext):
                        all_files.append(root_path / file)
        except OSError as e:
            logging.error(f"遍历路径出错 {LIBRARY_ROOT}: {e}")
            continue
    return all_files

# 扫描并处理新文件
def scan_and_process(limit=None):
    conn = init_db()
    c = conn.cursor()
    
    logging.info("开始扫描")
    all_files = get_all_files()
    logging.info(f"找到 {len(all_files)} 个文件")
    
    processed = 0
    for file_path in all_files:
        if limit and processed >= limit:
            break
        try:
            rel_path = str(file_path.relative_to(LIBRARY_ROOT))
            stat = file_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
            size = stat.st_size
            
            # 计算哈希，如果失败则跳过
            file_hash_val = file_hash(file_path)
            if file_hash_val is None:
                continue
            
            # 检查是否需要处理
            c.execute("SELECT hash FROM files WHERE path=?", (rel_path,))
            row = c.fetchone()
            if row and row[0] == file_hash_val:
                continue  # 无变化
            
            logging.info(f"处理: {rel_path}")
            text = extract_text(file_path)
            if not text:
                # 记录错误
                c.execute('''
                    INSERT OR REPLACE INTO files (path, mtime, size, hash, processed_time, chunk_count, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (rel_path, mtime, size, file_hash_val, datetime.now().isoformat(), 0, "提取文本为空"))
                conn.commit()
                continue
            
            chunks = chunk_text(text)
            if not chunks:
                c.execute('''
                    INSERT OR REPLACE INTO files (path, mtime, size, hash, processed_time, chunk_count, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (rel_path, mtime, size, file_hash_val, datetime.now().isoformat(), 0, "分块为空"))
                conn.commit()
                continue
            
            # 生成种子文件
            generate_seed(file_path, chunks, {'mtime': mtime, 'hash': file_hash_val})
            
            # 记录处理状态
            c.execute('''
                INSERT OR REPLACE INTO files (path, mtime, size, hash, processed_time, chunk_count, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rel_path, mtime, size, file_hash_val, datetime.now().isoformat(), len(chunks), None))
            conn.commit()
            processed += 1
            
        except Exception as e:
            logging.exception(f"处理文件 {file_path} 时发生异常")
            continue
    
    conn.close()
    logging.info(f"本次处理了 {processed} 个文件")
    print(f"本次处理了 {processed} 个文件，详情见日志 {LOG_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='限制处理文件数')
    args = parser.parse_args()
    scan_and_process(limit=args.limit)
