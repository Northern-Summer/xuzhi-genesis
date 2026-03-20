#!/bin/bash
set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认配置
MONITOR_PORT=11435
OLLAMA_PORT=11434
SERVICE_NAME="ollama-monitor"
INSTALL_PATH="/usr/local/bin/ollama-monitor"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
LOG_FILE="/var/log/ollama-monitor.log"

echo -e "${BLUE}=== Ollama 监控代理系统服务安装 ===${NC}"

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}部分操作需要 root 权限，请输入密码...${NC}"
    exec sudo bash "$0" "$@"
    exit
fi

# 确认继续
read -p "此操作将安装监控代理为系统服务，是否继续？(y/n) " -n 1 -r; echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# 停止当前可能运行的监控代理
if pgrep -f "ollama-monitor" >/dev/null; then
    echo -e "${YELLOW}停止当前运行的监控代理...${NC}"
    pkill -f "ollama-monitor" || true
fi

# 删除旧的 PID 文件
rm -f /tmp/ollama_monitor.pid

# 创建监控代理脚本
echo -e "${BLUE}创建监控代理脚本: $INSTALL_PATH${NC}"
cat > /tmp/ollama-monitor << 'EOF'
#!/usr/bin/env python3
import sys
import socket
import threading
import json
import os
import signal
import time

def handle_client(client_sock, target_host='localhost', target_port=11434):
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((target_host, target_port))
    except Exception as e:
        print(f"[错误] 无法连接到 Ollama: {e}", file=sys.stderr)
        client_sock.close()
        return

    def forward(src, dst, is_response=False):
        buffer = b''
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                if is_response:
                    buffer += data
                    lines = buffer.split(b'\n')
                    for line in lines[:-1]:
                        if line.strip():
                            try:
                                obj = json.loads(line)
                                if 'message' in obj and 'content' in obj['message']:
                                    print(obj['message']['content'], end='', flush=True)
                                elif 'response' in obj:
                                    print(obj['response'], end='', flush=True)
                            except:
                                pass
                    buffer = lines[-1]
                dst.sendall(data)
        except:
            pass
        finally:
            src.close()
            dst.close()

    threading.Thread(target=forward, args=(client_sock, server_sock, False)).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, True)).start()

def main():
    listen_port = int(sys.argv[1]) if len(sys.argv) > 1 else 11435
    target_port = int(sys.argv[2]) if len(sys.argv) > 2 else 11434

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', listen_port))
    server.listen(5)
    print(f"[监控代理] 监听 {listen_port} -> Ollama {target_port}", file=sys.stderr)

    # 忽略 SIGINT，让 systemd 管理
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        while True:
            client, addr = server.accept()
            threading.Thread(target=handle_client, args=(client, 'localhost', target_port)).start()
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
EOF

# 安装到系统目录
chmod +x /tmp/ollama-monitor
mv /tmp/ollama-monitor "$INSTALL_PATH"
echo -e "${GREEN}✓ 已安装到 $INSTALL_PATH${NC}"

# 创建 systemd 服务文件
echo -e "${BLUE}创建 systemd 服务: $SERVICE_FILE${NC}"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Ollama Monitor Proxy
After=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=$INSTALL_PATH $MONITOR_PORT $OLLAMA_PORT
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 创建日志文件并设置权限
touch "$LOG_FILE"
chown nobody:nogroup "$LOG_FILE" 2>/dev/null || chown nobody: "$LOG_FILE" 2>/dev/null || true
chmod 644 "$LOG_FILE"

# 重新加载 systemd
systemctl daemon-reload

# 启用并启动服务
echo -e "${BLUE}启用并启动服务...${NC}"
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# 等待服务启动
sleep 2

# 检查服务状态
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ 监控代理服务已启动并运行${NC}"
    echo -e "监听端口: $MONITOR_PORT -> $OLLAMA_PORT"
    echo -e "日志文件: $LOG_FILE"
else
    echo -e "${RED}❌ 服务启动失败，请检查: systemctl status $SERVICE_NAME${NC}"
    exit 1
fi

# 验证功能
echo -e "\n${BLUE}=== 验证监控代理 ===${NC}"
echo -e "请确保 Ollama 服务正在运行 (端口 $OLLAMA_PORT)。"
read -p "是否现在测试代理是否正常工作？(y/n) " -n 1 -r; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}将发送测试请求到代理端口 $MONITOR_PORT...${NC}"
    echo -e "如果看到模型输出，则监控成功。"
    echo -e "----------------------------------------"
    # 使用 curl 发送流式请求
    curl -N -s "http://localhost:$MONITOR_PORT/api/chat" -d '{
        "model": "llama2",
        "messages": [{"role": "user", "content": "你好，请简单介绍一下自己"}],
        "stream": true
    }' | tee /tmp/ollama_test_output.txt
    echo -e "\n----------------------------------------"
    if grep -q "助手" /tmp/ollama_test_output.txt 2>/dev/null; then
        echo -e "${GREEN}✅ 监控代理工作正常！输出已显示。${NC}"
    else
        echo -e "${YELLOW}⚠️ 未能确认输出，请检查日志: tail -f $LOG_FILE${NC}"
    fi
    rm -f /tmp/ollama_test_output.txt
fi

echo -e "\n${GREEN}=== 安装完成 ===${NC}"
echo "常用命令："
echo "  sudo systemctl status $SERVICE_NAME    # 查看服务状态"
echo "  sudo journalctl -u $SERVICE_NAME -f    # 查看实时日志（如果使用 journal）"
echo "  tail -f $LOG_FILE                       # 查看代理日志（实时模型输出）"
echo "  sudo systemctl stop $SERVICE_NAME       # 停止服务"
echo "  sudo systemctl disable $SERVICE_NAME    # 禁用开机自启"
echo
echo -e "${YELLOW}重要提示：${NC}"
echo "1. 确保您的应用程序/脚本已将 Ollama API 地址改为 localhost:$MONITOR_PORT"
echo "2. 您可以通过 'tail -f $LOG_FILE' 实时查看所有流式输出"
echo "3. 如果不需要监控，可以随时卸载服务：sudo systemctl disable --now $SERVICE_NAME && sudo rm $SERVICE_FILE $INSTALL_PATH"

