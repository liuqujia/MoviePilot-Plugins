"""
搜索处理器
负责聚影资源搜索逻辑
"""
from typing import Optional, List, Dict, Any

from app.log import logger

from ..clients import JuyingClient


class SearchHandler:
    """聚影搜索处理器"""

    def __init__(self, juying_client: Optional[JuyingClient] = None):
        self._client = juying_client

    def set_client(self, client: JuyingClient):
        """设置聚影客户端"""
        self._client = client

    def search(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        搜索电影/剧集
        :return: 搜索结果 dict
        """
        if not self._client:
            return {"success": False, "message": "聚影客户端未初始化"}

        try:
            result = self._client.search_movies(keyword=keyword, page=page, page_size=page_size)
            if result is None:
                return {"success": False, "message": f"搜索 '{keyword}' 失败，API 请求异常"}

            return {
                "success": True,
                "message": f"搜索 '{keyword}' 完成",
                "data": result,
            }
        except Exception as e:
            logger.error(f"聚影搜索异常: {e}")
            return {"success": False, "message": f"搜索异常: {e}"}

    def get_detail(self, movie_id: int) -> Dict[str, Any]:
        """
        获取电影详情
        """
        if not self._client:
            return {"success": False, "message": "聚影客户端未初始化"}

        try:
            result = self._client.get_movie_detail(movie_id=movie_id)
            if result is None:
                return {"success": False, "message": f"获取电影 {movie_id} 详情失败"}

            return {
                "success": True,
                "message": "获取详情成功",
                "data": result,
            }
        except Exception as e:
            logger.error(f"获取电影详情异常: {e}")
            return {"success": False, "message": f"获取详情异常: {e}"}

    def get_resources(self, movie_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取电影资源列表
        """
        if not self._client:
            return {"success": False, "message": "聚影客户端未初始化"}

        try:
            result = self._client.get_movie_resources(movie_id=movie_id, page=page, page_size=page_size)
            if result is None:
                return {"success": False, "message": f"获取电影 {movie_id} 资源失败"}

            return {
                "success": True,
                "message": "获取资源列表成功",
                "data": result,
            }
        except Exception as e:
            logger.error(f"获取电影资源异常: {e}")
            return {"success": False, "message": f"获取资源异常: {e}"}

    def list_requests(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取求片列表
        """
        if not self._client:
            return {"success": False, "message": "聚影客户端未初始化"}

        try:
            result = self._client.list_requests(page=page, page_size=page_size)
            if result is None:
                return {"success": False, "message": "获取求片列表失败"}

            return {
                "success": True,
                "message": "获取求片列表成功",
                "data": result,
            }
        except Exception as e:
            logger.error(f"获取求片列表异常: {e}")
            return {"success": False, "message": f"获取求片列表异常: {e}"}

    def create_request(self, title: str, description: str = "", request_type: str = "movie") -> Dict[str, Any]:
        """
        创建求片请求
        """
        if not self._client:
            return {"success": False, "message": "聚影客户端未初始化"}

        try:
            result = self._client.create_request(
                title=title,
                description=description,
                request_type=request_type,
            )
            if result is None:
                return {"success": False, "message": f"创建求片 '{title}' 失败"}

            return {
                "success": True,
                "message": f"求片 '{title}' 创建成功",
                "data": result,
            }
        except Exception as e:
            logger.error(f"创建求片异常: {e}")
            return {"success": False, "message": f"创建求片异常: {e}"}
