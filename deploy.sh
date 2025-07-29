#!/bin/bash
# 阿里云服务器部署脚本

echo "🚀 开始部署跨境购物助手后端..."

# 更新代码
echo "📥 拉取最新代码..."
git pull origin main

# 检查环境文件
if [ ! -f .env.production ]; then
    echo "❌ 错误：找不到 .env.production 文件"
    echo "请创建 .env.production 文件并配置必要的环境变量"
    exit 1
fi

# 加载环境变量
export $(cat .env.production | grep -v '^#' | xargs)

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查 SSL 证书
if [ ! -f ./ssl/fullchain.pem ] || [ ! -f ./ssl/privkey.pem ]; then
    echo "⚠️ SSL 证书未找到，将使用 Certbot 获取..."
    sudo certbot certonly --standalone -d api.guishkakrasiviy.com
    sudo cp /etc/letsencrypt/live/api.guishkakrasiviy.com/fullchain.pem ./ssl/
    sudo cp /etc/letsencrypt/live/api.guishkakrasiviy.com/privkey.pem ./ssl/
    sudo chown $USER:$USER ./ssl/*
fi

# 构建和启动服务
echo "🔨 构建 Docker 镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose down
docker-compose up -d

# 检查服务状态
echo "🔍 检查服务状态..."
sleep 5
if curl -f http://localhost:8000/health; then
    echo "✅ 服务启动成功！"
    echo "🌐 API 地址: https://api.guishkakrasiviy.com"
else
    echo "❌ 服务启动失败，查看日志："
    docker-compose logs api
    exit 1
fi

echo "✨ 部署完成！"