"""
聚影搜索插件
集成聚影 API (share.huamucang.top)，搜索网盘资源
"""
import datetime
from typing import Optional, Any, List, Dict, Tuple

import pytz
from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType

from .clients import JuyingClient
from .handlers import SearchHandler, ApiHandler
from .ui import UIConfig


class JuyingSearch(_PluginBase):
    """聚影搜索插件"""

    # 插件元数据
    plugin_name = "聚影搜索"
    plugin_desc = "集成聚影API，搜索网盘资源，支持求片功能。"
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/icons/cloud.png"
    plugin_version = "1.0.0"
    plugin_author = "kirito"
    author_url = "https://github.com/kirito"
    plugin_config_prefix = "juying_"
    plugin_order = 30
    auth_level = 1

    # 配置属性
    _enabled: bool = False
    _notify: bool = False
    _base_url: str = "https://share.huamucang.top"
    _app_id: str = ""
    _app_key: str = ""
    _proxy: str = ""

    # 运行时对象
    _juying_client: Optional[JuyingClient] = None
    _search_handler: Optional[SearchHandler] = None
    _api_handler: Optional[ApiHandler] = None

    # ==================== init_plugin ====================

    def init_plugin(self, config: dict = None):
        self.stop_service()

        if config:
            self._enabled = config.get("enabled", False)
            self._notify = config.get("notify", False)
            self._base_url = config.get("base_url", "https://share.huamucang.top") or "https://share.huamucang.top"
            self._app_id = config.get("app_id", "")
            self._app_key = config.get("app_key", "")
            self._proxy = config.get("proxy", "")

        # 初始化客户端和处理器
        self._init_clients()
        self._init_handlers()

        if self._enabled:
            logger.info("聚影搜索插件已启用")
            if self._juying_client and self._juying_client.check_connection():
                logger.info("聚影 API 连接正常")
            else:
                logger.warning("聚影 API 连接失败，请检查 App ID 和 App Key 配置")

    def _init_clients(self):
        """初始化客户端"""
        if self._app_id and self._app_key:
            proxy = self._proxy or settings.PROXY or None
            self._juying_client = JuyingClient(
                base_url=self._base_url,
                app_id=self._app_id,
                app_key=self._app_key,
                proxy=proxy,
            )
            logger.info("聚影客户端初始化成功")
        else:
            self._juying_client = None
            if self._enabled:
                logger.warning("聚影 App ID 或 App Key 未配置，插件无法正常工作")

    def _init_handlers(self):
        """初始化处理器"""
        self._search_handler = SearchHandler(juying_client=self._juying_client)
        self._api_handler = ApiHandler(
            juying_client=self._juying_client,
            get_data_func=self.get_data,
            save_data_func=self.save_data,
        )

    # ==================== 配置写回 ====================

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "base_url": self._base_url,
            "app_id": self._app_id,
            "app_key": self._app_key,
            "proxy": self._proxy,
        })

    # ==================== 必备方法 ====================

    def get_state(self) -> bool:
        return self._enabled

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return UIConfig.get_form()

    def get_page(self) -> Optional[List[dict]]:
        history = self.get_data("history") or []
        return UIConfig.get_page(history)

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/search",
                "endpoint": self.api_search,
                "methods": ["GET"],
                "summary": "搜索电影资源",
            },
            {
                "path": "/detail",
                "endpoint": self.api_detail,
                "methods": ["GET"],
                "summary": "获取电影详情",
            },
            {
                "path": "/resources",
                "endpoint": self.api_resources,
                "methods": ["GET"],
                "summary": "获取电影资源列表",
            },
            {
                "path": "/requests",
                "endpoint": self.api_requests,
                "methods": ["GET"],
                "summary": "获取求片列表",
            },
            {
                "path": "/create_request",
                "endpoint": self.api_create_request,
                "methods": ["POST"],
                "summary": "创建求片请求",
            },
            {
                "path": "/check_connection",
                "endpoint": self.api_check_connection,
                "methods": ["GET"],
                "summary": "检查 API 连接",
            },
        ]

    def get_service(self) -> List[Dict[str, Any]]:
        """聚影搜索插件无定时任务"""
        return []

    def stop_service(self):
        """停止服务"""
        if self._juying_client:
            self._juying_client.close()
            self._juying_client = None

    # ==================== API 端点实现 ====================

    def api_search(self, keyword: str, page: int = 1, page_size: int = 20, apikey: str = "") -> dict:
        """搜索电影 API 端点"""
        result = self._search_handler.search(keyword=keyword, page=page, page_size=page_size)

        # 记录搜索历史
        if result.get("success"):
            self._append_history(keyword, result.get("data", {}))

        return result

    def api_detail(self, movie_id: int, apikey: str = "") -> dict:
        """获取电影详情 API 端点"""
        return self._search_handler.get_detail(movie_id=movie_id)

    def api_resources(self, movie_id: int, page: int = 1, page_size: int = 20, apikey: str = "") -> dict:
        """获取电影资源 API 端点"""
        return self._search_handler.get_resources(movie_id=movie_id, page=page, page_size=page_size)

    def api_requests(self, page: int = 1, page_size: int = 20, apikey: str = "") -> dict:
        """获取求片列表 API 端点"""
        return self._search_handler.list_requests(page=page, page_size=page_size)

    def api_create_request(self, title: str, description: str = "", request_type: str = "movie", apikey: str = "") -> dict:
        """创建求片 API 端点"""
        result = self._search_handler.create_request(
            title=title,
            description=description,
            request_type=request_type,
        )

        # 发送通知
        if result.get("success") and self._notify:
            self.post_message(
                mtype=NotificationType.Plugin,
                title="【聚影搜索】求片创建成功",
                text=f"已创建求片请求：{title}",
            )

        return result

    def api_check_connection(self, apikey: str = "") -> dict:
        """检查连接 API 端点"""
        return self._api_handler.check_connection(apikey=apikey)

    # ==================== 辅助方法 ====================

    def _append_history(self, keyword: str, data: dict):
        """追加搜索历史"""
        try:
            history: List[dict] = self.get_data("history") or []

            # 统计结果数
            count = 0
            if isinstance(data, dict):
                results = data.get("results") or data.get("data") or []
                count = len(results) if isinstance(results, list) else 0

            tz = pytz.timezone(settings.TZ)
            history.append({
                "time": datetime.datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S"),
                "keyword": keyword,
                "count": count,
            })

            # 最多保留 200 条
            if len(history) > 200:
                history = history[-200:]

            self.save_data("history", history)
        except Exception as e:
            logger.error(f"保存搜索历史失败: {e}")

    # ==================== 远程命令 ====================

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """定义远程控制命令"""
        return [
            {
                "cmd": "/juying_search",
                "event": EventType.PluginAction,
                "desc": "聚影搜索",
                "category": "搜索",
                "data": {"action": "juying_search"},
            }
        ]

    def remote_search(self, event):
        """远程搜索处理"""
        from app.core.event import Event

        if not event or not event.event_data:
            return
        if event.event_data.get("action") != "juying_search":
            return

        keyword = event.event_data.get("keyword", "")
        if not keyword:
            self.post_message(
                mtype=NotificationType.Plugin,
                channel=event.event_data.get("channel"),
                title="【聚影搜索】参数错误",
                text="请提供搜索关键词，格式：/juying_search keyword=关键词",
                userid=event.event_data.get("user"),
            )
            return

        result = self._search_handler.search(keyword=keyword)
        status = "✅ 成功" if result.get("success") else "❌ 失败"
        self.post_message(
            mtype=NotificationType.Plugin,
            channel=event.event_data.get("channel"),
            title=f"【聚影搜索】{status}",
            text=result.get("message", "未知结果"),
            userid=event.event_data.get("user"),
        )
