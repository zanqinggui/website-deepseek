from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv
import json

from backend.services.deepseek_api import (
    call_deepseek_api,
    call_deepseek_api_stream,
    call_deepseek_brand_prompt,
    call_deepseek_brand_prompt_stream,
    call_deepseek_brand_with_context_prompt,
    call_deepseek_brand_with_context_prompt_stream,
    call_deepseek_product_prompt,
    call_deepseek_product_prompt_stream,
    call_deepseek_product_with_context_prompt,
    call_deepseek_product_with_context_prompt_stream,
    generate_search_keyword
)

# 加载环境变量
load_dotenv()

app = FastAPI()

# 获取认证密钥和允许的域名
API_AUTH_KEY = os.getenv("API_AUTH_KEY", "default-key-change-this")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")


# 创建限流器 - 修复编码问题
def get_real_ip(request: Request):
    return request.client.host


# 配置限流 - 每个IP每小时60次请求
limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["60 per hour", "2 per second"],  # 每小时60次，每秒最多2次
    storage_uri="memory://"  # 使用内存存储（也可以使用Redis）
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置CORS - 只允许特定域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 只允许特定域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
# 添加受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "127.0.0.1",
        "localhost",
        "*.ngrok-free.app",
        "*.ngrok.io",
        "guishkakrasiviy.com",
        "www.guishkakrasiviy.com",
        "api.guishkakrasiviy.com"  # 为将来的API子域名预留
    ]
)

# 认证依赖
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证API密钥"""
    token = credentials.credentials
    if token != API_AUTH_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid authentication credentials"
        )
    return token


# 输入输出模型
class SearchRequest(BaseModel):
    query: str
    language: str = "zh"


class BrandRequest(BaseModel):
    brand: str
    language: str = "zh"


class BrandWithContextRequest(BaseModel):
    brand: str
    context: str
    language: str = "zh"


class KeywordRequest(BaseModel):
    brand: str
    series: str
    category: str = ""
    language: str = "zh"


class SearchResponse(BaseModel):
    output: str


class KeywordResponse(BaseModel):
    keyword: str


# 🔍 主搜索接口 - 流式输出
@app.post("/search-stream")
@limiter.limit("20/minute")  # 每分钟最多20次搜索
async def search_stream(request: Request, data: SearchRequest, token: str = Depends(verify_token)):
    print(f"接收到流式搜索请求：{data.query}，语言：{data.language}")

    async def generate():
        # 发送 SSE 格式的数据
        full_content = ""
        for chunk in call_deepseek_api_stream(data.query, data.language):
            full_content += chunk
            # SSE 格式：data: {json}\n\n
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

        # 发送完成信号
        yield f"data: {json.dumps({'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# 🔍 普通搜索接口（保留作为备用）
@app.post("/search", response_model=SearchResponse)
@limiter.limit("20/minute")  # 每分钟最多20次搜索
async def search(request: Request, data: SearchRequest, token: str = Depends(verify_token)):
    print(f"接收到搜索请求：{data.query}，语言：{data.language}")
    result = call_deepseek_api(data.query, data.language)
    return {"output": result}


# 🧠 品牌关键词详情接口 - 流式输出
@app.post("/brand-detail-stream")
@limiter.limit("15/minute")  # 每分钟最多15次品牌查询
async def brand_detail_stream(request: Request, data: BrandRequest, token: str = Depends(verify_token)):
    print(f"接收到流式品牌详情请求：{data.brand}，语言：{data.language}")

    async def generate():
        full_content = ""
        for chunk in call_deepseek_brand_prompt_stream(data.brand, data.language):
            full_content += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# 🧠 品牌关键词详情接口 - 普通输出（保留）
@app.post("/brand-detail", response_model=SearchResponse)
@limiter.limit("15/minute")  # 每分钟最多15次品牌查询
async def brand_detail(request: Request, data: BrandRequest, token: str = Depends(verify_token)):
    print(f"接收到品牌详情请求：{data.brand}，语言：{data.language}")
    result = call_deepseek_brand_prompt(data.brand, data.language)
    return {"output": result}


# 🎯 带商品类型的品牌详情接口 - 流式输出
@app.post("/brand-detail-with-context-stream")
@limiter.limit("20/minute")
async def brand_detail_with_context_stream(request: Request, data: BrandWithContextRequest,
                                           token: str = Depends(verify_token)):
    print(f"接收到流式品牌详情请求：{data.brand}，商品类型：{data.context}，语言：{data.language}")

    async def generate():
        full_content = ""
        for chunk in call_deepseek_brand_with_context_prompt_stream(data.brand, data.context, data.language):
            full_content += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# 🎯 带商品类型的品牌详情接口 - 普通输出（保留）
@app.post("/brand-detail-with-context", response_model=SearchResponse)
@limiter.limit("20/minute")
async def brand_detail_with_context(request: Request, data: BrandWithContextRequest,
                                    token: str = Depends(verify_token)):
    print(f"接收到品牌详情请求：{data.brand}，商品类型：{data.context}，语言：{data.language}")
    result = call_deepseek_brand_with_context_prompt(data.brand, data.context, data.language)
    return {"output": result}


# 📱 产品系列详情接口 - 流式输出
@app.post("/product-detail-stream")
@limiter.limit("20/minute")
async def product_detail_stream(request: Request, data: BrandRequest, token: str = Depends(verify_token)):
    print(f"接收到流式产品系列详情请求：{data.brand}，语言：{data.language}")

    async def generate():
        full_content = ""
        for chunk in call_deepseek_product_prompt_stream(data.brand, data.language):
            full_content += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# 📱 产品系列详情接口 - 普通输出（保留）
@app.post("/product-detail", response_model=SearchResponse)
@limiter.limit("20/minute")
async def product_detail(request: Request, data: BrandRequest, token: str = Depends(verify_token)):
    print(f"接收到产品系列详情请求：{data.brand}，语言：{data.language}")
    result = call_deepseek_product_prompt(data.brand, data.language)
    return {"output": result}


# 📱 带商品类型的产品系列详情接口 - 流式输出
@app.post("/product-detail-with-context-stream")
@limiter.limit("20/minute")
async def product_detail_with_context_stream(request: Request, data: BrandWithContextRequest,
                                              token: str = Depends(verify_token)):
    print(f"接收到流式产品系列详情请求：{data.brand}，商品类型：{data.context}，语言：{data.language}")

    async def generate():
        full_content = ""
        for chunk in call_deepseek_product_with_context_prompt_stream(data.brand, data.context, data.language):
            full_content += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# 📱 带商品类型的产品系列详情接口 - 普通输出（保留）
@app.post("/product-detail-with-context", response_model=SearchResponse)
@limiter.limit("20/minute")
async def product_detail_with_context(request: Request, data: BrandWithContextRequest,
                                      token: str = Depends(verify_token)):
    print(f"接收到产品系列详情请求：{data.brand}，商品类型：{data.context}，语言：{data.language}")
    result = call_deepseek_product_with_context_prompt(data.brand, data.context, data.language)
    return {"output": result}


# 🔤 生成搜索关键词接口 - 添加限流和认证
@app.post("/generate-keyword", response_model=KeywordResponse)
@limiter.limit("30/minute")
async def generate_keyword(request: Request, data: KeywordRequest, token: str = Depends(verify_token)):
    print(f"生成搜索关键词：品牌={data.brand}, 系列={data.series}, 类型={data.category}, 语言={data.language}")
    keyword = generate_search_keyword(data.brand, data.series, data.category, data.language)
    print(f"生成的关键词：{keyword}")
    return {"keyword": keyword}


# 健康检查接口 - 不需要认证
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Cross-Border Shopping Assistant"}


# 静态文件服务 - 必须放在所有路由之后
app.mount("/video", StaticFiles(directory="frontend/video"), name="video")
app.mount("/images", StaticFiles(directory="frontend/images"), name="images")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")