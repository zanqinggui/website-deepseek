# 跨境购物助手 / Cross-border Shopping Assistant

🛍️ 面向俄罗斯市场的中国品牌智能购物助手

## 🌟 项目特点

- 🤖 基于 DeepSeek AI 的智能推荐
- 🌐 支持中文、英文、俄文三语切换
- 🛒 直连俄罗斯主流电商平台
- 💬 流式输出，用户体验流畅
- 🔒 安全的 API 密钥管理

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/zanqinggui/website-deepseek.git
cd website-deepseek
```

### 2. 配置环境

创建并配置必要的文件：

```bash
# 复制环境变量示例
cp .env.example .env

# 复制前端配置示例
cp frontend/config.js.example frontend/config.js
```

编辑 `.env` 文件，填入你的 DeepSeek API 密钥：
```
API_KEY=your_deepseek_api_key_here
API_AUTH_KEY=your_secure_auth_key_here
```

### 3. 添加 Prompt 文档

将以下文档放入 `key/` 文件夹（该文件夹不会上传到 GitHub）：
- `deepseek_prompt.docx`
- `deepseek_brand_prompt.docx`
- `deepseek_product_prompt.docx`

### 4. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 5. 运行项目

```bash
uvicorn server:app --reload
```

访问 http://127.0.0.1:8000

## 📁 项目结构

```
website-deepseek/
├── backend/              # 后端服务
│   ├── data/            # 品牌和类别映射数据
│   └── services/        # API 服务
├── frontend/            # 前端文件
│   ├── video/          # 背景视频
│   └── config.js       # 前端配置（需自行创建）
├── key/                # Prompt 文档（不上传）
├── server.py           # FastAPI 主程序
└── vercel.json         # Vercel 部署配置
```

## 🌍 部署

### Vercel 部署（前端）
1. Fork 本项目
2. 在 Vercel 导入项目
3. 设置环境变量
4. 部署

### 阿里云部署（后端）
```bash
docker-compose up -d
```

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issues 和 Pull Requests！

---

Made with ❤️ for Russian customers