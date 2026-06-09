"""
ASSRT 字幕下载插件
整理入库时自动从 ASSRT 搜索并下载字幕
"""
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import quote

from app.core.config import settings
from app.core.context import MediaInfo
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import TransferInfo, FileItem
from app.schemas.types import EventType, MediaType
from app.utils.http import RequestUtils


class AssrtSubtitle(_PluginBase):
    """ASSRT 字幕下载插件"""

    # 插件元信息
    plugin_name = "ASSRT字幕下载"
    plugin_desc = "整理入库时自动从 ASSRT 搜索并下载字幕"
    plugin_icon = "chinesesubfinder.png"
    plugin_version = "1.0.1"
    plugin_author = "Kirito"
    author_url = "https://github.com/liuqujia"
    plugin_config_prefix = "assrt_subtitle_"
    plugin_order = 6
    auth_level = 1

    # API 配置
    ASSRT_API = "https://api.assrt.net/v1"

    # 私有属性
    _enabled: bool = False
    _token: str = ""
    _download_chs: bool = True
    _download_cht: bool = False
    _download_eng: bool = False
    _save_to_video_dir: bool = True
    _overwrite_existing: bool = False

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._token = config.get("token", "")
            self._download_chs = config.get("download_chs", True)
            self._download_cht = config.get("download_cht", False)
            self._download_eng = config.get("download_eng", False)
            self._save_to_video_dir = config.get("save_to_video_dir", True)
            self._overwrite_existing = config.get("overwrite_existing", False)

    def get_state(self) -> bool:
        return self._enabled and bool(self._token)

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'token',
                                            'label': 'ASSRT API Token',
                                            'hint': '在 assrt.net 个人设置中获取',
                                            'persistent-hint': True
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'div',
                                        'props': {
                                            'class': 'text-subtitle-1 mb-2'
                                        },
                                        'content': ['下载字幕语言']
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 4},
                                'content': [
                                    {
                                        'component': 'VCheckbox',
                                        'props': {
                                            'model': 'download_chs',
                                            'label': '简体中文',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 4},
                                'content': [
                                    {
                                        'component': 'VCheckbox',
                                        'props': {
                                            'model': 'download_cht',
                                            'label': '繁体中文',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 4},
                                'content': [
                                    {
                                        'component': 'VCheckbox',
                                        'props': {
                                            'model': 'download_eng',
                                            'label': '英文',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'save_to_video_dir',
                                            'label': '保存到视频目录',
                                            'hint': '关闭则保存到临时目录',
                                            'persistent-hint': True
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'overwrite_existing',
                                            'label': '覆盖已有字幕',
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "token": "",
            "download_chs": True,
            "download_cht": False,
            "download_eng": False,
            "save_to_video_dir": True,
            "overwrite_existing": False
        }

    def get_page(self) -> List[dict]:
        return []

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def stop_service(self):
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        return []

    @eventmanager.register(EventType.TransferComplete)
    def on_transfer_complete(self, event: Event):
        """整理完成后自动下载字幕"""
        if not self._enabled or not self._token:
            return

        event_data = event.event_data
        if not event_data:
            return

        media_info: MediaInfo = event_data.get("mediainfo")
        transfer_info: TransferInfo = event_data.get("transferinfo")

        if not media_info or not transfer_info:
            return

        # 获取文件列表
        file_list = transfer_info.file_list_new
        if not file_list:
            return

        # 处理每个视频文件
        for file_path in file_list:
            if not self._is_video_file(file_path):
                continue

            # 检查是否已有字幕
            if not self._overwrite_existing and self._has_subtitle(file_path):
                logger.info(f"文件已有字幕，跳过: {file_path}")
                continue

            # 下载字幕
            self._download_subtitle(file_path, media_info)

    def _is_video_file(self, file_path: str) -> bool:
        """判断是否为视频文件"""
        video_extensions = {'.mp4', '.mkv', '.avi', '.wmv', '.flv', '.mov', '.m4v', '.rmvb', '.ts'}
        return Path(file_path).suffix.lower() in video_extensions

    def _has_subtitle(self, file_path: str) -> bool:
        """检查是否已有字幕"""
        video_path = Path(file_path)
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.sub']
        for ext in subtitle_extensions:
            for lang_suffix in ['', '.chs', '.cht', '.zh', '.en', '.eng']:
                subtitle_path = video_path.with_suffix(ext + lang_suffix)
                if subtitle_path.exists():
                    return True
        return False

    def _download_subtitle(self, file_path: str, media_info: MediaInfo):
        """下载字幕"""
        video_path = Path(file_path)
        video_name = video_path.stem

        logger.info(f"开始为 {video_name} 搜索字幕")

        # 构建搜索关键词
        query = self._build_search_query(video_name, media_info)

        # 搜索字幕
        subtitle_list = self._search_subtitles(query)
        if not subtitle_list:
            logger.warning(f"未找到字幕: {query}")
            return

        # 筛选合适的字幕
        best_subtitle = self._select_best_subtitle(subtitle_list)
        if not best_subtitle:
            logger.warning(f"没有匹配的字幕: {query}")
            return

        # 下载字幕文件
        self._download_subtitle_file(best_subtitle, video_path)

    def _build_search_query(self, video_name: str, media_info: MediaInfo) -> str:
        """构建搜索关键词"""
        # 优先使用标题
        if media_info.title:
            query = media_info.title
            if media_info.year:
                query += f" {media_info.year}"
            return query

        # 从文件名提取
        # 移除常见后缀
        name = re.sub(r'\[.*?\]', '', video_name)
        name = re.sub(r'\..*$', '', name)
        name = re.sub(r'-\s*[\w]+$', '', name)
        return name.strip()

    def _search_subtitles(self, query: str) -> List[dict]:
        """搜索字幕"""
        try:
            url = f"{self.ASSRT_API}/sub/search"
            headers = {
                "Authorization": f"Bearer {self._token}"
            }
            params = {
                "q": query,
                "no_mux": 1  # 不返回内嵌字幕
            }

            response = RequestUtils(headers=headers, timeout=30).get(url, params=params)

            if not response or response.status_code != 200:
                logger.error(f"搜索字幕失败: {response.status_code if response else 'no response'}")
                return []

            data = response.json()
            subtitles = data.get("sub", {}).get("subs", [])

            logger.info(f"找到 {len(subtitles)} 个字幕")
            return subtitles

        except Exception as e:
            logger.error(f"搜索字幕异常: {str(e)}")
            return []

    def _select_best_subtitle(self, subtitles: List[dict]) -> Optional[dict]:
        """选择最合适的字幕"""
        if not subtitles:
            return None

        # 按语言筛选
        valid_subs = []
        for sub in subtitles:
            lang = sub.get("lang", {}).get("lang", "")
            lang_desc = sub.get("lang", {}).get("desc", "").lower()

            # 检查语言
            is_valid = False
            if self._download_chs and ('简体' in lang_desc or 'chs' in lang_desc or 'gb' in lang_desc):
                is_valid = True
            if self._download_cht and ('繁体' in lang_desc or 'cht' in lang_desc or 'big5' in lang_desc):
                is_valid = True
            if self._download_eng and ('英' in lang_desc or 'en' in lang_desc.lower()):
                is_valid = True

            if is_valid:
                valid_subs.append(sub)

        if not valid_subs:
            # 如果没有匹配语言，返回第一个
            return subtitles[0] if subtitles else None

        # 按下载次数排序，选择最热门的
        valid_subs.sort(key=lambda x: x.get("downloads", 0), reverse=True)
        return valid_subs[0]

    def _download_subtitle_file(self, subtitle: dict, video_path: Path):
        """下载字幕文件"""
        sub_id = subtitle.get("id")
        sub_name = subtitle.get("native_name", subtitle.get("videoname", ""))

        try:
            # 获取下载链接
            url = f"{self.ASSRT_API}/sub/download"
            headers = {
                "Authorization": f"Bearer {self._token}"
            }
            params = {"id": sub_id}

            response = RequestUtils(headers=headers, timeout=60).get(url, params=params)

            if not response or response.status_code != 200:
                logger.error(f"下载字幕失败: {sub_id}")
                return

            data = response.json()
            download_url = data.get("sub", {}).get("url")

            if not download_url:
                logger.error(f"未获取到下载链接: {sub_id}")
                return

            # 下载字幕内容
            sub_response = RequestUtils(timeout=60).get(download_url)
            if not sub_response or sub_response.status_code != 200:
                logger.error(f"下载字幕内容失败: {download_url}")
                return

            sub_content = sub_response.content

            # 确定保存路径
            if self._save_to_video_dir:
                save_dir = video_path.parent
            else:
                save_dir = Path(settings.TEMP_PATH) / "subtitles"
                save_dir.mkdir(parents=True, exist_ok=True)

            # 确定文件名和扩展名
            # 尝试从下载链接获取扩展名
            ext = ".srt"
            content_type = sub_response.headers.get("Content-Type", "")
            if "application/zip" in content_type or download_url.endswith(".zip"):
                # ZIP 包，需要解压
                self._extract_and_save(sub_content, save_dir, video_path.stem)
                logger.info(f"字幕下载成功(ZIP): {video_path.stem}")
                return
            elif download_url.endswith(".ass"):
                ext = ".ass"
            elif download_url.endswith(".ssa"):
                ext = ".ssa"
            elif download_url.endswith(".sub"):
                ext = ".sub"

            # 添加语言后缀
            lang_suffix = self._get_lang_suffix(subtitle)
            subtitle_path = save_dir / f"{video_path.stem}{lang_suffix}{ext}"

            # 保存文件
            with open(subtitle_path, "wb") as f:
                f.write(sub_content)

            logger.info(f"字幕下载成功: {subtitle_path}")

        except Exception as e:
            logger.error(f"下载字幕异常: {str(e)}")

    def _extract_and_save(self, zip_content: bytes, save_dir: Path, video_stem: str):
        """解压 ZIP 并保存字幕"""
        import zipfile
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                for name in zf.namelist():
                    if name.endswith(('.srt', '.ass', '.ssa', '.sub')):
                        content = zf.read(name)
                        ext = Path(name).suffix
                        subtitle_path = save_dir / f"{video_stem}{ext}"
                        with open(subtitle_path, "wb") as f:
                            f.write(content)
                        logger.info(f"解压字幕成功: {subtitle_path}")
                        break
        except Exception as e:
            logger.error(f"解压字幕失败: {str(e)}")

    def _get_lang_suffix(self, subtitle: dict) -> str:
        """获取语言后缀"""
        lang_desc = subtitle.get("lang", {}).get("desc", "").lower()

        if '简体' in lang_desc or 'chs' in lang_desc:
            return ".chs"
        elif '繁体' in lang_desc or 'cht' in lang_desc:
            return ".cht"
        elif '英' in lang_desc or 'en' in lang_desc:
            return ".en"
        elif '双' in lang_desc:
            return ".zh"
        return ""
