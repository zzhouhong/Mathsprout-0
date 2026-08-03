from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "萌芽数学 Mathsprout"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mathsprout"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/mathsprout"

    # LLM Vision API — 支持 Anthropic Claude（原生）和 OpenAI 兼容提供商
    # 提供商自动检测：base_url 含 "anthropic.com" → Anthropic SDK，否则 → OpenAI SDK
    # ⚠️ 使用 VISION_ 前缀避免与 Claude Code 注入的 ANTHROPIC_* 环境变量冲突
    VISION_API_KEY: str = ""
    VISION_MODEL: str = "qwen-vl-max"
    VISION_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    VISION_MAX_TOKENS: int = 2048  # 减少输出 token 以加速 AI 识别响应
    VISION_CACHE_ENABLED: bool = True
    VISION_TIMEOUT_SECONDS: int = 60  # API 调用超时
    # 显式指定视觉提供商：留空则按 VISION_BASE_URL 自动检测（含 anthropic.com/claude → anthropic，否则 openai 兼容）
    # 设为 "offline" 时走离线模式：从 OFFLINE_RESULTS_DIR 按图片哈希读取预存识别结果，零 API 依赖
    VISION_PROVIDER: str = ""
    OFFLINE_RESULTS_DIR: str = "./tests/images/golden"  # offline provider 读取预存识别结果的目录

    # Image Processing
    IMAGE_MAX_SIZE_PX: int = 2048
    IMAGE_TARGET_SIZE_PX: int = 1080  # 1080px 平衡速度与识别精度（fast=720, balanced=1080, accurate=1440）
    IMAGE_QUALITY: int = 85
    VISION_IMAGE_SIZE: str = "balanced"  # fast | balanced | accurate

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    REPORT_DIR: str = "./reports"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Rate Limiting
    RATE_LIMIT_AI_PER_MIN: int = 10     # AI endpoints (analysis/worksheets)
    RATE_LIMIT_AI_BURST: int = 10
    RATE_LIMIT_AUTH_PER_MIN: int = 10   # Auth endpoints
    RATE_LIMIT_AUTH_BURST: int = 10
    RATE_LIMIT_DEFAULT_PER_MIN: int = 120  # General endpoints
    RATE_LIMIT_DEFAULT_BURST: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
