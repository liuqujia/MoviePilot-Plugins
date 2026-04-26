"""
JuYing (聚影) API Client
网盘资源收集者 - share.huamucang.top

Search client for MoviePilot plugin, replacing NullbrClient.
Searches JuYing for movie/TV resources and returns 115 share links.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


class JuyingClient:
    """
    JuYing API Client for searching 115 share resources.

    API Base URL: https://share.huamucang.top
    Auth: X-App-Id + X-App-Key headers

    Endpoints:
        GET  /api/dev/movies/?search=keyword&ordering=-created&page=1
        GET  /api/dev/movie/<id>/detail/
        GET  /api/dev/movie/<id>/resources/
        GET  /api/dev/requests/
        POST /api/dev/request/create/

    Returns results in unified format compatible with p115strgmsub:
        [{"url": "share_115_url", "title": "resource_title", "update_time": "..."}]
    """

    BASE_URL = "https://share.huamucang.top"

    def __init__(self, app_id: str, api_key: str, proxy: Optional[str] = None):
        """
        Initialize JuYing client.

        Args:
            app_id: X-App-Id header value for authentication.
            api_key: X-API-KEY header value for authentication.
            proxy: Proxy URL or dict (compatible with requests).
                   - str: proxy URL like "http://127.0.0.1:7890"
                   - dict: {"http": "...", "https": "..."} or {"all": "..."}
        """
        self.app_id = app_id
        self.api_key = api_key
        self._api_call_count = 0

        # Build proxies dict from various input formats
        self.proxies: Optional[Dict[str, str]] = None
        if proxy:
            if isinstance(proxy, str):
                self.proxies = {"http": proxy, "https": proxy}
            elif isinstance(proxy, dict):
                self.proxies = proxy

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "X-App-Id": self.app_id,
            "X-API-KEY": self.api_key,
        })

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_movie_resources_by_tmdb(self, tmdb_id: int) -> List[Dict[str, Any]]:
        """
        Search resources by TMDB ID.

        Note: JuYing API does not natively support TMDB ID search.
        This method searches by TMDB ID as a keyword fallback.
        For best results, use search_movies() with a text keyword
        and then call get_movie_resources(movie_id).

        Args:
            tmdb_id: TMDB ID to search for.

        Returns:
            List of 115 resource dicts in unified format.
        """
        return self.search_115_resources(str(tmdb_id))

    def search_movies(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search movies by keyword.

        Args:
            keyword: Search keyword (movie title, etc.).

        Returns:
            List of movie dicts with keys: id, title, year, tmdb_id, etc.
        """
        try:
            url = f"{self.BASE_URL}/api/dev/movies/"
            params = {
                "search": keyword,
                "ordering": "-created",
                "page": 1,
            }
            response = self._request("GET", url, params=params)
            response.raise_for_status()
            data = response.json()

            # Handle various response formats
            if isinstance(data, dict):
                # Could be {"results": [...]} or {"data": [...]} or flat list
                if "results" in data:
                    return data["results"]
                if "data" in data:
                    return data["data"]
                # Single object returned
                if "id" in data:
                    return [data]
                return [data] if data else []
            if isinstance(data, list):
                return data
            return []

        except Exception as e:
            logger.warning(f"[JuyingClient] search_movies error: {e}")
            return []

    def get_movie_resources(self, movie_id: int) -> List[Dict[str, Any]]:
        """
        Get 115 share links for a specific movie.

        Args:
            movie_id: JuYing internal movie ID.

        Returns:
            List of resource dicts with url, title, cloud_type, update_time etc.
            Filtered to only include 115-type resources.
        """
        try:
            url = f"{self.BASE_URL}/api/dev/movie/{movie_id}/resources/"
            response = self._request("GET", url)
            response.raise_for_status()
            data = response.json()

            resources: List[Dict[str, Any]] = []
            items = data if isinstance(data, list) else data.get("results", data.get("data", []))

            for item in items:
                cloud_type = str(item.get("cloud_type", "")).lower()
                share_url = str(item.get("share_url", "")).lower()
                # Filter for 115 cloud type or URL
                if "115" in cloud_type or "115" in share_url:
                    resources.append({
                        "url": item.get("share_url", ""),
                        "title": item.get("title", ""),
                        "update_time": item.get("update_time", "")
                                        or item.get("created", ""),
                        "cloud_type": item.get("cloud_type", ""),
                        "movie_id": movie_id,
                    })

            # Sort by update_time descending
            resources.sort(
                key=lambda x: x.get("update_time", ""),
                reverse=True
            )
            return resources

        except Exception as e:
            logger.warning(f"[JuyingClient] get_movie_resources({movie_id}) error: {e}")
            return []

    def search_115_resources(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Combined search: find movie by keyword, then fetch its 115 resources.

        This is the main entry point called by SearchHandler.
        Returns results in the unified format expected by p115strgmsub:
            [{"url": "share_url", "title": "resource_title", "update_time": "..."}]

        Args:
            keyword: Search keyword (movie title, TMDB ID, etc.).

        Returns:
            List of 115 resource dicts sorted by update_time descending.
        """
        try:
            # Step 1: search for movies matching the keyword
            movies = self.search_movies(keyword)
            if not movies:
                logger.info(f"[JuyingClient] No movies found for keyword: {keyword}")
                return []

            all_resources: List[Dict[str, Any]] = []

            # Step 2: get resources for each matched movie (up to 3 to avoid over-fetching)
            for movie in movies[:3]:
                movie_id = movie.get("id")
                if not movie_id:
                    continue

                movie_title = movie.get("title", "")
                resources = self.get_movie_resources(movie_id)

                for r in resources:
                    # Add movie context for debugging
                    r["movie_title"] = movie_title
                    r["movie_id"] = movie_id
                    all_resources.append(r)

            # Deduplicate by URL
            seen: set = set()
            unique_resources: List[Dict[str, Any]] = []
            for r in all_resources:
                url = r.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    unique_resources.append(r)

            # Sort by update_time descending
            unique_resources.sort(
                key=lambda x: x.get("update_time", ""),
                reverse=True
            )

            logger.info(
                f"[JuyingClient] search_115_resources('{keyword}') "
                f"-> {len(unique_resources)} resources from {len(movies[:3])} movies"
            )
            return unique_resources

        except Exception as e:
            logger.error(f"[JuyingClient] search_115_resources error: {e}")
            return []

    def create_request(self, title: str, description: str = "") -> Optional[Dict[str, Any]]:
        """
        Submit a resource request.

        Args:
            title: Movie/resource title being requested.
            description: Optional description or notes.

        Returns:
            Created request dict or None on failure.
        """
        try:
            url = f"{self.BASE_URL}/api/dev/request/create/"
            payload: Dict[str, Any] = {"title": title}
            if description:
                payload["description"] = description

            response = self._request("POST", url, json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.warning(f"[JuyingClient] create_request error: {e}")
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Perform an HTTP request with proxy support and call counting.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Full request URL.
            params: Query string parameters.
            json: JSON body payload.

        Returns:
            requests.Response object.

        Raises:
            requests.RequestException: On network/HTTP errors.
        """
        self._api_call_count += 1
        return self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            proxies=self.proxies,
            timeout=15,
        )

    @property
    def api_call_count(self) -> int:
        """Number of API calls made so far."""
        return self._api_call_count

    def reset_call_count(self) -> None:
        """Reset the API call counter."""
        self._api_call_count = 0

    def close(self) -> None:
        """Close the underlying session."""
        self.session.close()
