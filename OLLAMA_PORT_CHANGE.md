# Ollama 端口变更说明

**重要：所有指向 Ollama 服务的地址均已从 `:11434` 改为 `:11435`。**

## 原因
我们部署了一个透明监控代理（`ollama-monitor`），用于实时捕获所有流式响应并打印到日志，方便调试和观察模型输出。该代理监听 11435 端口，并将请求转发到真正的 Ollama 服务（11434）。

## 对开发的影响
- 所有代码、配置文件中原本写死的 `localhost:11434` 或 `127.0.0.1:11434` 均已被自动替换为 `:11435`。
- 如果未来需要直接调用原生 Ollama（绕过监控），请手动将端口改回 11434，并停止监控代理（`sudo systemctl stop ollama-monitor`）。
- 监控代理的日志位于 `/var/log/ollama-monitor.log`，可用 `tail -f` 实时查看。

## 如何验证
运行以下命令，如果看到模型流式输出，则一切正常：
```bash
curl -N http://localhost:11435/api/chat -d '{"model":"llama2","messages":[{"role":"user","content":"hi"}],"stream":true}'
