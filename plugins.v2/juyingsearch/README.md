# 聚影搜索

MoviePilot V2 插件，集成 [聚影](https://share.huamucang.top) API，搜索网盘资源。

## 功能

- 🔍 **搜索电影/剧集** — 通过关键词搜索聚影数据库中的资源
- 📋 **查看详情** — 获取电影详细信息
- 📎 **资源列表** — 查看电影的网盘资源链接
- 🙏 **求片功能** — 创建求片请求
- 🔗 **API 接口** — 提供完整的 RESTful API
- 📡 **远程命令** — 支持通过 `/juying_search` 远程搜索

## 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 启用插件 | 开启/关闭插件 | 关闭 |
| 发送通知 | 搜索完成时发送通知 | 关闭 |
| API 地址 | 聚影 API 基础地址 | https://share.huamucang.top |
| App ID | 开发者认证 ID | - |
| App Key | 开发者认证 Key | - |
| 代理地址 | HTTP 代理（可选） | - |

## 获取 API 密钥

1. 注册 [聚影](https://share.huamucang.top) 账号
2. 访问开发者页面申请开发者权限
3. 获取 App ID 和 App Key

## API 端点

插件注册以下 API 端点（路径前缀 `/api/v1/plugin/JuyingSearch`）：

- `GET /search?keyword=xxx` — 搜索电影
- `GET /detail?movie_id=xxx` — 获取电影详情
- `GET /resources?movie_id=xxx` — 获取电影资源
- `GET /requests` — 获取求片列表
- `POST /create_request` — 创建求片
- `GET /check_connection` — 检查 API 连接

## 远程命令

- `/juying_search keyword=关键词` — 远程搜索

## 版本历史

### v1.0.0
- 首个版本
- 集成聚影 API 搜索功能
- 支持求片功能
- 支持搜索历史记录
