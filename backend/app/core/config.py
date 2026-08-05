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

    # LLM Vision API — 支持 Anthropic Claude（原生）、OpenAI 兼容提供商、MiniMax（文本）
    # 提供商自动检测：base_url 含 "anthropic.com" → Anthropic SDK，否则 → OpenAI SDK
    # ⚠️ 使用 VISION_ 前缀避免与 Claude Code 注入的 ANTHROPIC_* 环境变量冲突
    # ⚠️ MiniMax（api.MiniMax.chat）仅提供文本模型（abab 系列），不支持图片输入；
    #    视觉识别请使用 qwen-vl-max（默认）或 Claude；MiniMax 用于文本任务（如报告润色）。
    VISION_API_KEY: str = ""
    VISION_MODEL: str = "qwen-vl-max"
    VISION_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    VISION_MAX_TOKENS: int = 2048  # 减少输出 token 以加速 AI 识别响应
    VISION_CACHE_ENABLED: bool = True
    VISION_TIMEOUT_SECONDS: int = 60  # API 调用超时
    # 显式指定视觉提供商：留空则按 VISION_BASE_URL 自动检测（含 anthropic.com/claude → anthropic，否则 openai 兼容）
    # 可选值：offline | anthropic | openai_compatible | minimax
    #   - "offline" 走离线模式：从 OFFLINE_RESULTS_DIR 按图片哈希读取预存识别结果，零 API 依赖
    #   - "minimax" 走 MiniMax 官方 API（api.MiniMax.chat），仅文本能力；图片识别会明确报错
    VISION_PROVIDER: str = ""
    OFFLINE_RESULTS_DIR: str = "./tests/images/golden"  # offline provider 读取预存识别结果的目录

    # ── MiniMax 官方服务（多模态，M3 支持图像输入） ────────────────────────
    # MiniMax 官方端点：https://api.MiniMax.chat/v1/text/chatcompletion_v2
    # 鉴权：HTTP Header "Authorization: Bearer <MINIMAX_API_KEY>"
    # 模型：
    #   - MiniMax-M3    多模态（文本 + 图像输入），视觉识别用这个
    #   - abab6.5s-chat 纯文本
    MINIMAX_API_KEY: str = ""
    MINIMAX_BASE_URL: str = "https://api.MiniMax.chat"
    MINIMAX_MODEL: str = "MiniMax-M3"
    MINIMAX_MAX_TOKENS: int = 2048
    MINIMAX_TIMEOUT_SECONDS: int = 60

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

    # 正式教师账号（通过环境变量配置，生产环境可用）
    # 与内置 demo 账号不同：demo 账号在生产环境被禁用，此账号始终可用。
    # 三项都留空时不创建该账号。
    TEACHER_EMAIL: str = ""
    TEACHER_PASSWORD: str = ""
    TEACHER_NAME: str = "老师"

    # 微信云托管对象存储（教师拍照上传中转，与 cloudbaserc.json 的 envId 配套）
    # 存储桶名可从云托管控制台「对象存储」页或 tcb storage url 命令获得。
    CLOUD_STORAGE_BUCKET: str = ""
    CLOUD_STORAGE_REGION: str = "ap-shanghai"

    # SQLite 持久化备份（对象存储兜底，仅 DATABASE_URL 为 sqlite 时生效）
    # 需要云托管「开放接口服务」开启 + 微信令牌白名单放行 /_/cos/getauth、/_/cos/metaid/encode
    DB_BACKUP_ENABLED: bool = True
    DB_BACKUP_INTERVAL_SECONDS: int = 180
    DB_BACKUP_KEY: str = "backup/mathsprout.db"

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
