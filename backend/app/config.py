from __future__ import annotations

import os
from dataclasses import dataclass
from ipaddress import ip_address
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_local_app_data = os.getenv("LOCALAPPDATA")
LOCAL_STORAGE_ROOT = (
    (Path(_local_app_data).expanduser() / "iBuddy").resolve() if _local_app_data else PROJECT_ROOT
)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        parsed = default
    return max(minimum, min(maximum, parsed))


def _as_float(value: str | None, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value) if value is not None else default
    except ValueError:
        parsed = default
    return max(minimum, min(maximum, parsed))


def _as_choice(value: str | None, default: str, allowed: set[str]) -> str:
    parsed = (value or default).strip().lower()
    return parsed if parsed in allowed else default


def _path_from_env(value: str | None, default: Path) -> Path:
    path = Path(os.path.expandvars(value)).expanduser() if value else default
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _loopback_host(value: str | None) -> str:
    host = (value or "127.0.0.1").strip().lower()
    if host == "localhost":
        return host
    try:
        if ip_address(host).is_loopback:
            return host
    except ValueError:
        pass
    raise ValueError("LLAMA_CPP_HOST must resolve explicitly to a loopback address")


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Sovereign AI iBuddy"
    environment: str = "development"
    database_path: Path = LOCAL_STORAGE_ROOT / "data" / "ibuddy.db"
    frontend_dist: Path = PROJECT_ROOT / "frontend" / "dist"
    model_backend: str = "llama_cpp"
    offline_mode: bool = True
    llama_cpp_model_path: Path = LOCAL_STORAGE_ROOT / "models" / "Qwen3-8B-Q5_K_M.gguf"
    llama_cpp_server_path: Path = LOCAL_STORAGE_ROOT / "runtime" / "llama.cpp" / "llama-server.exe"
    llama_cpp_host: str = "127.0.0.1"
    llama_cpp_port: int = 18_080
    llama_cpp_context_size: int = 8192
    llama_cpp_threads: int = 8
    llama_cpp_gpu_layers: int = 0
    llama_cpp_startup_timeout_seconds: float = 180.0
    llama_cpp_enable_thinking: bool = False
    hf_token: str | None = None
    hf_model: str = "Qwen/Qwen2.5-7B-Instruct-1M"
    hf_provider: str = "auto"
    hf_base_url: str | None = None
    model_timeout_seconds: float = 120.0
    max_new_tokens: int = 1200
    temperature: float = 0.25
    search_provider: str = "auto"
    search_safesearch: str = "moderate"
    brave_search_api_key: str | None = None
    tavily_api_key: str | None = None
    search_timeout_seconds: float = 6.0
    search_result_count: int = 4
    history_message_limit: int = 24
    max_user_chars: int = 12_000
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "testserver")
    debug: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "llama_cpp_host", _loopback_host(self.llama_cpp_host))

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        origins = tuple(
            item.strip()
            for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if item.strip()
        )
        allowed_hosts = tuple(
            item.strip()
            for item in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
            if item.strip()
        )
        return cls(
            environment=os.getenv("IBUDDY_ENV", "development").strip().lower(),
            database_path=_path_from_env(
                os.getenv("IBUDDY_DATABASE_PATH"), LOCAL_STORAGE_ROOT / "data" / "ibuddy.db"
            ),
            frontend_dist=_path_from_env(
                os.getenv("IBUDDY_FRONTEND_DIST"), PROJECT_ROOT / "frontend" / "dist"
            ),
            model_backend=os.getenv("IBUDDY_MODEL_BACKEND", "llama_cpp").strip().lower(),
            offline_mode=_as_bool(os.getenv("IBUDDY_OFFLINE"), default=True),
            llama_cpp_model_path=_path_from_env(
                os.getenv("LLAMA_CPP_MODEL_PATH"),
                LOCAL_STORAGE_ROOT / "models" / "Qwen3-8B-Q5_K_M.gguf",
            ),
            llama_cpp_server_path=_path_from_env(
                os.getenv("LLAMA_CPP_SERVER_PATH"),
                LOCAL_STORAGE_ROOT / "runtime" / "llama.cpp" / "llama-server.exe",
            ),
            llama_cpp_host=_loopback_host(os.getenv("LLAMA_CPP_HOST")),
            llama_cpp_port=_as_int(os.getenv("LLAMA_CPP_PORT"), 18_080, 1024, 65_535),
            llama_cpp_context_size=_as_int(os.getenv("LLAMA_CPP_CONTEXT_SIZE"), 8192, 512, 131_072),
            llama_cpp_threads=_as_int(os.getenv("LLAMA_CPP_THREADS"), 8, 1, 256),
            llama_cpp_gpu_layers=_as_int(os.getenv("LLAMA_CPP_GPU_LAYERS"), 0, 0, 999),
            llama_cpp_startup_timeout_seconds=_as_float(
                os.getenv("LLAMA_CPP_STARTUP_TIMEOUT_SECONDS"), 180.0, 1.0, 600.0
            ),
            llama_cpp_enable_thinking=_as_bool(os.getenv("LLAMA_CPP_ENABLE_THINKING")),
            hf_token=(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN") or None),
            hf_model=os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct-1M").strip(),
            hf_provider=os.getenv("HF_PROVIDER", "auto").strip(),
            hf_base_url=os.getenv("HF_BASE_URL") or None,
            model_timeout_seconds=_as_float(os.getenv("MODEL_TIMEOUT_SECONDS"), 120.0, 5.0, 600.0),
            max_new_tokens=_as_int(os.getenv("MAX_NEW_TOKENS"), 1200, 64, 8192),
            temperature=_as_float(os.getenv("MODEL_TEMPERATURE"), 0.25, 0.0, 2.0),
            search_provider=os.getenv("SEARCH_PROVIDER", "auto").strip().lower(),
            search_safesearch=_as_choice(
                os.getenv("SEARCH_SAFESEARCH"),
                "moderate",
                {"off", "moderate", "strict"},
            ),
            brave_search_api_key=os.getenv("BRAVE_SEARCH_API_KEY") or None,
            tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
            search_timeout_seconds=_as_float(os.getenv("SEARCH_TIMEOUT_SECONDS"), 6.0, 2.0, 60.0),
            search_result_count=_as_int(os.getenv("SEARCH_RESULT_COUNT"), 4, 1, 10),
            history_message_limit=_as_int(os.getenv("HISTORY_MESSAGE_LIMIT"), 24, 2, 100),
            max_user_chars=_as_int(os.getenv("MAX_USER_CHARS"), 12_000, 256, 50_000),
            cors_origins=origins,
            allowed_hosts=allowed_hosts,
            debug=_as_bool(os.getenv("IBUDDY_DEBUG")),
        )

    @property
    def model_ready(self) -> bool:
        if self.model_backend == "llama_cpp":
            return self.llama_cpp_model_path.is_file() and self.llama_cpp_server_path.is_file()
        if self.model_backend == "local":
            return True
        return bool(self.hf_token or self.hf_base_url)
