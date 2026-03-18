# AI PROJECT CONTEXT
> Generated: Sun Mar 15 05:24:55 CST 2026

## Identity
# Project Identity
> Generated: Sun Mar 15 05:24:38 CST 2026

Total scanned files: 1888
Python files: 4
JS/TS files: 1
Shell files: 3

## Directory
# Directory Map
```text
./.ark/checksum.txt
./.ark/logs/ark-installer-20260314-230228.jsonl
./.bash_history
./.bash_logout
./.bashrc
./.bashrc.bak.20260315044957
./.docker/config.json
./.gitconfig
./.lesshst
./.npm/_cacache/content-v2
./.npm/_cacache/index-v5
./.npmrc
./.ollama/history
./.openclaw-backup-20260314212748/git-config.txt
./.openclaw-backup-20260314212748/http_proxy.txt
./.openclaw-backup-20260314212748/https_proxy.txt
./.openclaw-backup-20260314212748/npm-config.txt
./.openclaw-backup-20260314212904/git-config.txt
./.openclaw-backup-20260314212904/http_proxy.txt
./.openclaw-backup-20260314212904/https_proxy.txt
./.openclaw-backup-20260314212904/npm-config.txt
./.openclaw/agents/conductor
./.openclaw/agents/main
./.openclaw/canvas/index.html
./.openclaw/completions/openclaw.bash
./.openclaw/completions/openclaw.fish
./.openclaw/completions/openclaw.ps1
./.openclaw/completions/openclaw.zsh
./.openclaw/config.json
./.openclaw/cron/jobs.json
./.openclaw/devices/paired.json
./.openclaw/devices/pending.json
./.openclaw/identity/device-auth.json
./.openclaw/identity/device.json
./.openclaw/logs/cache-trace.jsonl
./.openclaw/logs/config-audit.jsonl
./.openclaw/openclaw.json
./.openclaw/openclaw.json.bak.1
./.openclaw/openclaw.json.bak.2
./.openclaw/openclaw.json.bak.3
./.openclaw/openclaw.json.bak.4
./.openclaw/openclaw.json5
./.openclaw/shadow/constitution
./.openclaw/shadow/skills
./.openclaw/update-check.json
./.openclaw/workspace-conductor/.git
./.openclaw/workspace-conductor/.openclaw
./.openclaw/workspace-conductor/AGENTS.md
./.openclaw/workspace-conductor/BOOTSTRAP.md
./.openclaw/workspace-conductor/HEARTBEAT.md
./.openclaw/workspace-conductor/IDENTITY.md
./.openclaw/workspace-conductor/SOUL.md
./.openclaw/workspace-conductor/TOOLS.md
./.openclaw/workspace-conductor/USER.md
./.openclaw/workspace/.git
./.openclaw/workspace/.openclaw
./.openclaw/workspace/AGENTS.md
./.openclaw/workspace/BOOTSTRAP.md
./.openclaw/workspace/HEARTBEAT.md
./.openclaw/workspace/IDENTITY.md
./.openclaw/workspace/SOUL.md
./.openclaw/workspace/TOOLS.md
./.openclaw/workspace/USER.md
./.profile
./.ssh/known_hosts
./.viminfo
./.wget-hsts
./.yarnrc
./acai/.acai_env
./acai/.acai_env.bak.1773511778
./acai/.acai_env.bak.1773512204
./acai/.gateway_usage.json
./acai/.venv/bin
./acai/.venv/pyvenv.cfg
./acai/acai_translator.py
./acai/acai_translator.py.bak.1773511778
./acai/acai_translator.py.bak.1773512204
./acai/acai_translator_ultimate.py
./acai/ai_translator.sh
./acai/main.py
./acai/project_brain.md
./acai/requirements.txt
./acai/start_acai.sh.bak.1773512204
./acai/start_gateway.sh
./acai_translator_ultimate.py
./acai_translator_ultimate.py.bak.20260315040131
./acai_translator_ultimate.py.bak.20260315040434
./ai_translator.sh
./ark-install
./openclaw-workspace/.git/HEAD
./openclaw-workspace/.git/config
./openclaw-workspace/.git/description
./openclaw-workspace/.git/hooks
./openclaw-workspace/.git/info
./openclaw-workspace/.openclaw/workspace-state.json
./openclaw-workspace/AGENTS.md
./openclaw-workspace/BOOTSTRAP.md
./openclaw-workspace/HEARTBEAT.md
./openclaw-workspace/IDENTITY.md
./openclaw-workspace/SOUL.md
./openclaw-workspace/TOOLS.md
./openclaw-workspace/USER.md
./project_brain.md
./snap/firefox/7967
./snap/firefox/common
./venv_acai/bin/Activate.ps1
./venv_acai/bin/activate
./venv_acai/bin/activate.csh
./venv_acai/bin/activate.fish
./venv_acai/bin/fastapi
./venv_acai/bin/httpx
./venv_acai/bin/pip
./venv_acai/bin/pip3
./venv_acai/bin/pip3.12
./venv_acai/bin/uvicorn
./venv_acai/pyvenv.cfg
./虚质_寄居蟹_修复_report.txt
```

## Entry Points
./acai_translator_ultimate.py:if __name__ == "__main__":
./acai/main.py:if __name__ == "__main__":
./acai/acai_translator.py:if __name__ == "__main__":

## Code Skeleton
# Code Skeleton
## ./snap/firefox/common/.mozilla/firefox/cj5mksle.default/prefs.js
```
# ...(implementation omitted)...
```

## ./acai/main.py
```
import os
import time
import json
import base64
import logging
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import Response, HTMLResponse, JSONResponse
import httpx
def add_log(msg: str) -> None:
def load_waf_cookie() -> str:
def save_waf_cookie(cookie: str) -> None:
def load_usage() -> Dict[str, Any]:
def save_usage(data: Dict[str, Any]) -> None:
async def fetch_user_plan() -> Dict[str, Any]:
async def get_best_models() -> Dict[str, Any]:
async def chat_proxy(request: Request):
async def draw_proxy(request: Request):
async def models():
async def usage_endpoint():
async def metrics_endpoint():
async def health():
async def root():
async def dashboard():
# ...(implementation omitted)...
```

## ./acai/ai_translator.sh
```
# ...(implementation omitted)...
```

## ./acai/acai_translator_ultimate.py
```
# ...(implementation omitted)...
```

## ./acai_translator_ultimate.py
```
import os
import json
import time
import asyncio
import httpx
import base64
import statistics
from collections import deque
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse, StreamingResponse
import uvicorn
def add_log(level: str, msg: str):
def get_acai_headers(token: str = None):
async def fetch_models_from_remote() -> List[Dict[str, Any]]:
async def update_models_periodically():
async def ping_model(model_id: str):
async def run_all_pings():
async def auto_ping_loop():
async def lifespan(app: FastAPI):
async def get_status():
async def get_logs():
async def v1_models():
async def health():
async def metrics():
async def usage():
async def chat_proxy(request: Request):
async def dashboard():
# ...(implementation omitted)...
```

## ./ai_translator.sh
```
# ...(implementation omitted)...
```

## ./acai/start_gateway.sh
```
# ...(implementation omitted)...
```

## ./acai/acai_translator.py
```
import os
import time
import json
import base64
import logging
import statistics
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import Response, HTMLResponse, JSONResponse
import httpx
def add_log(msg: str) -> None:
def load_waf_cookie() -> str:
def save_waf_cookie(cookie: str) -> None:
def load_usage() -> Dict[str, Any]:
def save_usage(data: Dict[str, Any]) -> None:
async def fetch_user_plan() -> Dict[str, Any]:
async def get_best_models() -> Dict[str, Any]:
async def chat_proxy(request: Request):
async def draw_proxy(request: Request):
async def models():
async def usage_endpoint():
async def dashboard():
async def health():
async def metrics_endpoint():
# ...(implementation omitted)...
```


## Dependencies
./acai_translator_ultimate.py:import os
./acai_translator_ultimate.py:import json
./acai_translator_ultimate.py:import time
./acai_translator_ultimate.py:import asyncio
./acai_translator_ultimate.py:import httpx
./acai_translator_ultimate.py:import base64
./acai_translator_ultimate.py:import statistics
./acai_translator_ultimate.py:from collections import deque
./acai_translator_ultimate.py:from datetime import datetime
./acai_translator_ultimate.py:from contextlib import asynccontextmanager
./acai_translator_ultimate.py:from typing import Dict, Any, List, Optional
./acai_translator_ultimate.py:from fastapi import FastAPI, Request
./acai_translator_ultimate.py:from fastapi.responses import HTMLResponse, Response, JSONResponse, StreamingResponse
./acai_translator_ultimate.py:import uvicorn
./acai_translator_ultimate.py:        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
./acai_translator_ultimate.py:    import sys
./acai_translator_ultimate.py:        import traceback
./acai/main.py:import os
./acai/main.py:import time
./acai/main.py:import json
./acai/main.py:import base64
./acai/main.py:import logging
./acai/main.py:import statistics
./acai/main.py:from datetime import datetime
./acai/main.py:from typing import Dict, Any, List, Optional
./acai/main.py:from fastapi import FastAPI, Request
./acai/main.py:from fastapi.responses import Response, HTMLResponse, JSONResponse
./acai/main.py:import httpx
./acai/main.py:                await asyncio.sleep(backoff)  # 注意需要 import asyncio
./acai/main.py:        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700&display=swap');
./acai/main.py:    import uvicorn
./acai/main.py:    import asyncio  # 为 chat_proxy 中的 asyncio.sleep 提供支持
./acai/acai_translator.py:import os
./acai/acai_translator.py:import time
./acai/acai_translator.py:import json
./acai/acai_translator.py:import base64
./acai/acai_translator.py:import logging
./acai/acai_translator.py:import statistics
./acai/acai_translator.py:from datetime import datetime
./acai/acai_translator.py:from typing import Dict, Any, List
./acai/acai_translator.py:from fastapi import FastAPI, Request
./acai/acai_translator.py:from fastapi.responses import Response, HTMLResponse, JSONResponse
./acai/acai_translator.py:import httpx
./acai/acai_translator.py:        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700&display=swap');
./acai/acai_translator.py:    import uvicorn

## Architecture
# Architecture Inference

Python project detected
JavaScript project detected
Shell tooling detected
