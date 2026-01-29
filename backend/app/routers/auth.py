from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import jwt, JWTError
from ..config import settings
from ..schemas import LoginRequest, TokenResponse, MessageResponse

router = APIRouter()
security = HTTPBearer()


def create_access_token(data: dict):
    """创建JWT令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证JWT令牌的依赖函数"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        # 检查token类型
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token类型",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(login_data: LoginRequest):
    """
    用户登录接口
    
    - **password**: 登录密码（默认: 123456）
    
    返回JWT令牌，用于后续API调用的身份验证
    """
    # 简单的密码验证（支持多个密码）
    if login_data.password not in settings.allowed_passwords:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建令牌
    access_token = create_access_token(
        data={"sub": "user", "type": "access"}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/verify", response_model=MessageResponse, summary="验证令牌")
async def verify_token_endpoint(payload = Depends(verify_token)):
    """
    验证当前令牌是否有效
    
    需要在请求头中携带 Authorization: Bearer <token>
    """
    return MessageResponse(message="令牌有效")


@router.get("/info", summary="获取认证信息")
async def get_auth_info():
    """
    获取认证相关信息
    """
    return {
        "login_required": True,
        "allowed_passwords": settings.allowed_passwords,
        "default_password": settings.default_password,
        "token_expire_minutes": settings.access_token_expire_minutes,
        "algorithm": settings.algorithm
    } 