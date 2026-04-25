"""
API 处理器
负责插件对外 API 端点的业务逻辑
"""
from typing import Optional, Callable

from app.log import logger

from ..clients import JuyingClient


class ApiHandler:
    """聚影 API 处理器"""

    def __init__(
        self,
        juying_client: Optional[JuyingClient] = None,
        get_data_func: Optional[Callable] = None,
        save_data_func: Optional[Callable] = None,
    ):
        self._client = juying_client
        self._get_data = get_data_func
        self._save_data = save_data_func

    def set_client(self, client: JuyingClient):
        self._client = client

    def search(self, keyword: str, apikey: str) -> dict:
        """搜索电影"""
        if not self._client:
            return {"code": 1, "msg": "聚影客户端未初始化"}

        try:
            result = self._client.search_movies(keyword=keyword)
            if result is None:
                return {"code": 1, "msg": "搜索失败"}
            return {"code": 0, "msg": "ok", "data": result}
        except Exception as e:
            logger.error(f"API 搜索异常: {e}")
            return {"code": 1, "msg": str(e)}

    def get_detail(self, movie_id: int, apikey: str) -> dict:
        """获取电影详情"""
        if not self._client:
            return {"code": 1, "msg": "聚影客户端未初始化"}

        try:
            result = self._client.get_movie_detail(movie_id=movie_id)
            if result is None:
                return {"code": 1, "msg": "获取详情失败"}
            return {"code": 0, "msg": "ok", "data": result}
        except Exception as e:
            logger.error(f"API 获取详情异常: {e}")
            return {"code": 1, "msg": str(e)}

    def get_resources(self, movie_id: int, apikey: str) -> dict:
        """获取电影资源"""
        if not self._client:
            return {"code": 1, "msg": "聚影客户端未初始化"}

        try:
            result = self._client.get_movie_resources(movie_id=movie_id)
            if result is None:
                return {"code": 1, "msg": "获取资源失败"}
            return {"code": 0, "msg": "ok", "data": result}
        except Exception as e:
            logger.error(f"API 获取资源异常: {e}")
            return {"code": 1, "msg": str(e)}

    def list_requests(self, apikey: str) -> dict:
        """获取求片列表"""
        if not self._client:
            return {"code": 1, "msg": "聚影客户端未初始化"}

        try:
            result = self._client.list_requests()
            if result is None:
                return {"code": 1, "msg": "获取求片列表失败"}
            return {"code": 0, "msg": "ok", "data": result}
        except Exception as e:
            logger.error(f"API 获取求片列表异常: {e}")
            return {"code": 1, "msg": str(e)}

    def create_request(self, title: str, description: str, request_type: str, apikey: str) -> dict:
        """创建求片"""
        if not self._client:
            return {"code": 1, "msg": "聚影客户端未初始化"}

        try:
            result = self._client.create_request(
                title=title,
                description=description,
                request_type=request_type,
            )
            if result is None:
                return {"code": 1, "msg": "创建求片失败"}
            return {"code": 0, "msg": "ok", "data": result}
        except Exception as e:
            logger.error(f"API 创建求片异常: {e}")
            return {"code": 1, "msg": str(e)}

    def check_connection(self, apikey: str) -> dict:
        """检查 API 连接"""
        if not self._client:
            return {"code": 1, "msg": "聚影客户端未初始化"}

        try:
            ok = self._client.check_connection()
            return {"code": 0 if ok else 1, "msg": "连接正常" if ok else "连接失败"}
        except Exception as e:
            return {"code": 1, "msg": str(e)}
