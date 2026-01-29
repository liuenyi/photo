# 小宇相册 API 快速开始

## 🎉 服务已成功启动！

### 访问地址

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

### 快速测试

#### 1. 检查服务状态
```bash
curl http://localhost:8000/
```

#### 2. 获取相册列表
```bash
curl http://localhost:8000/api/albums/
```

#### 3. 用户登录
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"123456"}'
```

#### 4. 获取认证信息
```bash
curl http://localhost:8000/api/auth/info
```

### 启动命令

#### 方式一：使用 Python 脚本
```bash
cd photo-api
python start.py
```

#### 方式二：使用 Shell 脚本
```bash
cd photo-api
chmod +x start.sh
./start.sh
```

#### 方式三：直接使用 uvicorn
```bash
cd photo-api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 默认数据

系统已自动创建了3个示例相册：
- 风景摄影
- 人像写真  
- 城市建筑

### 与小程序对接

修改小程序中的 API 基础地址：
```javascript
const API_BASE = 'http://localhost:8000/api'
```

### 主要功能

✅ **认证系统** - JWT 令牌认证  
✅ **相册管理** - 增删改查操作  
✅ **照片管理** - 上传、查看、删除  
✅ **文件上传** - 支持多种图片格式  
✅ **自动文档** - OpenAPI 3.0 文档  
✅ **数据库** - SQLite 异步操作  
✅ **图片处理** - 自动生成缩略图  

### 技术优势

相比 Node.js 版本：
- 🚀 **开发效率更高** - 自动类型检查和文档生成
- 📝 **代码更清晰** - 完整的类型注解
- 🔧 **调试更容易** - 详细的错误信息
- 📚 **文档更完善** - 自动生成 API 文档
- 🎯 **性能更稳定** - 异步处理优化

### 下一步

1. 访问 http://localhost:8000/docs 查看完整 API 文档
2. 测试文件上传功能
3. 集成到微信小程序中
4. 根据需要调整配置

---

**小宇相册 API (Python + FastAPI) 已就绪！** 🎊 