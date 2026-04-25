"""
聚影 API 客户端
对接 share.huamucang.top 开发者 API
"""
import re
from typing import Optional, List, Dict, Any

from app.log import logger


class JuyingClient:
    """聚影 API 客户端"""

    def __init__(self, base_url: str, app_id: str, app_key: str, proxy: str = None):
        self._base_url = base_url.rstrip("/")
        self._app_id = app_id
        self._app_key = app_key
        self._proxy = proxy
        self._session = None

    def _get_session(self):
        """获取 HTTP session"""
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                self._session.headers.update({
                    "X-App-Id": self._app_id,
                    "X-App-Key": self._app_key,
                    "Content-Type": "application/json",
                    "User-Agent": "MoviePilot-JuyingPlugin/1.0",
                })
                if self._proxy:
                    self._session.proxies.update({
                        "http": self._proxy,
                        "https": self._proxy,
                    })
            except ImportError:
                logger.error("requests 库未安装")
                return None
        return self._session

    def _request(self, method: str, path: str, **kwargs) -> Optional[Dict[str, Any]]:
        """发送 HTTP 请求"""
        session = self._get_session()
        if not session:
            return None

        url = f"{self._base_url}{path}"
        try:
            resp = session.request(method, url, timeout=30, **kwargs)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"聚影 API 请求失败: {method} {url} → {resp.status_code} {resp.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"聚影 API 请求异常: {method} {url} → {e}")
            return None

    # ==================== 电影相关 ====================

    def search_movies(self, keyword: str, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
        """
        搜索电影
        :param keyword: 搜索关键词
        :param page: 页码
        :param page_size: 每页数量
        """
        return self._request("GET", "/api/dev/movies/", params={
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
        })

    def get_movie_detail(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        获取电影详情
        :param movie_id: 电影 ID
        """
        return self._request("GET", f"/api/dev/movie/{movie_id}/detail/")

    def get_movie_resources(self, movie_id: int, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
        """
        获取电影资源列表（网盘链接）
        :param movie_id: 电影 ID
        :param page: 页码
        :param page_size: 每页数量
        """
        return self._request("GET", f"/api/dev/movie/{movie_id}/resources/", params={
            "page": page,
            "page_size": page_size,
        })

    # ==================== 求片相关 ====================

    def list_requests(self, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
        """
        获取求片列表
        """
        return self._request("GET", "/api/dev/requests/", params={
            "page": page,
            "page_size": page_size,
        })

    def get_request_detail(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        获取求片详情
        """
        return self._request("GET", f"/api/dev/request/{request_id}/detail/")

    def create_request(self, title: str, description: str = "", request_type: str = "movie") -> Optional[Dict[str, Any]]:
        """
        创建求片请求
        :param title: 片名
        :param description: 描述
        :param request_type: 类型 movie/tv
        """
        return self._request("POST", "/api/dev/request/create/", json={
            "title": title,
            "description": description,
            "type": request_type,
        })

    # ==================== 辅助方法 ====================

    def check_connection(self) -> bool:
        """检查 API 连接是否正常"""
        try:
            result = self.search_movies(keyword="test", page=1, page_size=1)
            return result is not None
        except Exception:
            return False

    def close(self):
        """关闭 session"""
        if self._session:
            try:
                self._session.close()
            except Exception:
                pass
            self._session = None
