# 视觉识别提供商（Vision Provider）配置

萌芽数学的视觉识别管线支持三种提供商，按需切换。**默认开箱即用 `offline` 离线模式，无需任何 API Key。**

---

## 三种提供商对比

| 提供商 | `VISION_PROVIDER` | 需要 Key | 适用场景 |
|--------|-------------------|----------|----------|
| **offline** | `offline` | ❌ 不需要 | 开发、演示、CI、无 API Key 时（默认） |
| **qwen** | `qwen` | ✅ 阿里云百炼 | 国内生产环境（推荐，成本低） |
| **claude** | `claude` | ✅ Anthropic | 需要 Claude Vision 时 |

> 留空（不设 `VISION_PROVIDER`）时，按 `VISION_BASE_URL` 自动检测：含 `anthropic.com` 或 `claude` 走 Claude，否则走 OpenAI 兼容（qwen）。

---

## 1. offline（离线模式）—— 默认，零配置

从本地目录读取**预存的识别结果**，完全脱离任何 API。适合本地开发、功能演示、自动化测试。

### 工作原理
1. 上传图片 → 经 `ImageProcessor` 预处理 → 计算 SHA-256 哈希
2. 在 `OFFLINE_RESULTS_DIR`（默认 `./tests/images/golden`）下，按哈希匹配预存结果
3. 命中 → 直接返回预存的识别 JSON；未命中 → 抛出明确错误

### 配置（`.env`）
```ini
VISION_PROVIDER=offline
OFFLINE_RESULTS_DIR=./tests/images/golden
```

### 预存结果的目录结构
```
tests/images/golden/
├── shapes-triangle/
│   ├── image.png                    # 原图（参考用）
│   ├── image_hash.txt               # 预处理后图片的 SHA-256（首行）
│   └── recognition_result.json      # 预存的识别结果（recognizer.analyze() 输出格式）
├── answer-row-1/
│   ├── ...
```

### 如何扩充离线结果库（识别新图）
offline 模式只能识别**已预存**的图。要加入新图，需先用真实 API（qwen/claude）或 ZCode 视觉能力识别一次，再保存结果：

```bash
cd backend
# 1. 用真实 provider 识别新图，保存结果
.\venv\Scripts\python.exe vision_eval.py --image path/to/new.png --provider qwen --format json > result.json

# 2. 算出预处理后的哈希（与 recognizer 内部一致）
.\venv\Scripts\python.exe -c "
import hashlib, asyncio
from app.services.image_processor import ImageProcessor
async def main():
    proc = ImageProcessor(target_size_px=1080, max_size_px=2576, quality=85)
    processed, _ = await proc.process(open('path/to/new.png','rb').read(), 'new.png', 'image/png')
    print(hashlib.sha256(processed).hexdigest())
asyncio.run(main())
"

# 3. 在 OFFLINE_RESULTS_DIR 下新建目录，放入 image_hash.txt + recognition_result.json
```

---

## 2. qwen（阿里云百炼 Qwen-VL）—— 生产推荐

国内推荐方案，延迟低、成本低。

### 配置（`.env`）
```ini
VISION_PROVIDER=qwen
VISION_API_KEY=sk-你的阿里云百炼Key
VISION_MODEL=qwen-vl-max
VISION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 获取 Key
1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 模型广场 → 开通 Qwen-VL 系列
3. 创建 API Key

---

## 3. claude（Anthropic Claude Vision）

### 配置（`.env`）
```ini
VISION_PROVIDER=claude
VISION_API_KEY=sk-ant-你的AnthropicKey
VISION_MODEL=claude-sonnet-4-6
VISION_BASE_URL=https://api.anthropic.com
```

> 也可用环境变量 `ANTHROPIC_API_KEY`（`vision_eval.py --provider claude` 会自动读取）。

---

## 命令行快速验证

```bash
cd backend
# offline（无需 Key）
.\venv\Scripts\python.exe vision_eval.py --image tests/images/golden/shapes-triangle/image.png --provider offline

# qwen / claude（需配置 Key）
.\venv\Scripts\python.exe vision_eval.py --image tests/images/golden/shapes-triangle/image.png --provider qwen
```

---

## 排错

| 现象 | 原因与解决 |
|------|-----------|
| `离线模式：该图片未预存识别结果` | 该图未在离线库中，用上述「扩充离线结果库」流程添加，或切换到 qwen/claude |
| `离线模式：结果目录不存在` | `OFFLINE_RESULTS_DIR` 路径错误，检查 `.env` |
| API 调用 401 | `VISION_API_KEY` 无效或未填写 |
| 走错 provider | 显式设置 `VISION_PROVIDER`，不要依赖自动检测 |
