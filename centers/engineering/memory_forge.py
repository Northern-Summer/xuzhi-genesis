import json
import os
import datetime

# --- 配置物理坐标 ---
CLAW_ROOT = "/home/summer/.openclaw"
BACKUP_FILE = f"{CLAW_ROOT}/agents/main/sessions/sessions.json.bak"
ARCHIVE_DIR = f"{CLAW_ROOT}/agents/main/workspace/archives"
INDEX_FILE = f"{CLAW_ROOT}/agents/main/workspace/MEMORY_INDEX.md"

def forge_memories():
    print("🧠 [虚质记忆引擎] 正在启动记忆降维与归档序列...")
    
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ 找不到备份文件: {BACKUP_FILE}")
        return

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    try:
        with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 解析 JSON 失败: {e}")
        return

    # 提取对话或系统日志 (根据具体 JSON 结构适配，这里假设是一个列表或包含 messages 的结构)
    # OpenClaw 的 session 结构可能嵌套，我们采取宽泛提取策略
    extracted_texts = []
    
    # 将整个 JSON 转换为格式化的字符串，按固定字符数切片（粗略模拟分块提取）
    raw_str = json.dumps(data, ensure_ascii=False, indent=2)
    chunk_size = 5000 # 每个档案大约 5000 个字符
    chunks = [raw_str[i:i+chunk_size] for i in range(0, len(raw_str), chunk_size)]
    
    index_content = "# 虚质系统 (Xuzhi) 核心记忆索引\n\n> 提示：以下是系统历史心血的压缩切片。如有必要，请使用你的 `read_file` 工具读取对应路径的详细档案。\n\n"
    
    for idx, chunk in enumerate(chunks):
        archive_name = f"memory_fragment_{idx:03d}.md"
        archive_path = os.path.join(ARCHIVE_DIR, archive_name)
        
        # 写入详细档案
        with open(archive_path, 'w', encoding='utf-8') as af:
            af.write(f"--- 历史记忆碎片 {idx:03d} ---\n\n")
            af.write(chunk)
            
        # 提取前 50 个字符作为摘要放入索引
        summary = chunk[:50].replace('\n', ' ').strip() + "..."
        index_content += f"- **[档案 {idx:03d}]**: `{archive_path}`\n  - *摘要*: {summary}\n\n"

    # 写入顶层索引
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(index_content)
        
    print(f"✅ 记忆降维完成！共生成 {len(chunks)} 个高密度档案。")
    print(f"✅ 抽象索引已生成于: {INDEX_FILE}")

if __name__ == "__main__":
    forge_memories()

