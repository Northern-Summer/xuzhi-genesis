def add_log(level: str, msg: str):
def get_acai_headers(token: str = None):
async def fetch_models_from_remote() -> List[Dict[str, Any]]:
async def update_models_periodically():
async def ping_model(model_id: str):
async def run_all_pings():
    async def sem_ping(mid):
async def auto_ping_loop():
async def lifespan(app: FastAPI):
async def get_status():
async def get_logs():
async def v1_models():
async def health():
async def metrics():
async def usage():
async def chat_proxy(request: Request):
    async def event_generator():
async def dashboard():
def add_log(msg: str) -> None:
def load_waf_cookie() -> str:
def save_waf_cookie(cookie: str) -> None:
def load_usage() -> Dict[str, Any]:
def save_usage(data: Dict[str, Any]) -> None:
async def fetch_user_plan() -> Dict[str, Any]:
async def get_best_models() -> Dict[str, Any]:
        def quality_score(m: dict) -> int:
async def chat_proxy(request: Request):
async def draw_proxy(request: Request):
async def models():
async def usage_endpoint():
async def metrics_endpoint():
async def health():
async def root():
async def dashboard():
def add_log(msg: str) -> None:
def load_waf_cookie() -> str:
def save_waf_cookie(cookie: str) -> None:
def load_usage() -> Dict[str, Any]:
def save_usage(data: Dict[str, Any]) -> None:
async def fetch_user_plan() -> Dict[str, Any]:
async def get_best_models() -> Dict[str, Any]:
        def quality_score(m: Dict[str, Any]) -> int:
async def chat_proxy(request: Request):
async def draw_proxy(request: Request):
async def models():
async def usage_endpoint():
async def dashboard():
async def health():
async def metrics_endpoint():
