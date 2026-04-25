"""
UI 配置模块
包含插件配置表单和详情页面定义
"""
from typing import Any, Dict, List, Optional


class UIConfig:
    """聚影插件 UI 配置"""

    @staticmethod
    def get_form() -> tuple:
        """
        返回配置页面 JSON 和默认模型
        格式: ([组件列表], {默认值字典})
        """
        # 配置页面组件
        form_components = [
            # ========== 基础设置 ==========
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VSwitch",
                                "props": {
                                    "model": "enabled",
                                    "label": "启用插件",
                                    "hint": "开启后可使用聚影搜索功能",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VSwitch",
                                "props": {
                                    "model": "notify",
                                    "label": "发送通知",
                                    "hint": "搜索完成时发送通知",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                ],
            },
            # ========== API 配置 ==========
            {
                "component": "VRow",
                "props": {"class": "mt-2"},
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "base_url",
                                    "label": "API 地址",
                                    "placeholder": "https://share.huamucang.top",
                                    "hint": "聚影 API 基础地址，默认 https://share.huamucang.top",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "app_id",
                                    "label": "App ID",
                                    "placeholder": "在聚影开发者页面申请",
                                    "hint": "X-App-Id 认证凭证",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "app_key",
                                    "label": "App Key",
                                    "placeholder": "在聚影开发者页面申请",
                                    "hint": "X-App-Key 认证凭证",
                                    "persistent-hint": True,
                                    "type": "password",
                                    "append-icon": "mdi-eye",
                                },
                            }
                        ],
                    },
                ],
            },
            # ========== 代理设置 ==========
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "proxy",
                                    "label": "代理地址",
                                    "placeholder": "留空使用系统代理",
                                    "hint": "可选，HTTP 代理地址（如 http://127.0.0.1:7890）",
                                    "persistent-hint": True,
                                    "clearable": True,
                                },
                            }
                        ],
                    },
                ],
            },
            # ========== 连接测试 ==========
            {
                "component": "VRow",
                "props": {"class": "mt-2"},
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VBtn",
                                "props": {
                                    "color": "primary",
                                    "size": "small",
                                },
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {"icon": "mdi-connection", "size": "small"},
                                    },
                                    " 测试连接",
                                ],
                                "events": {
                                    "click": {
                                        "action": "fetch",
                                        "url": "/api/v1/plugin/JuyingSearch/check_connection?apikey={{ apikey }}",
                                        "method": "GET",
                                        "success": "连接成功！",
                                        "error": "连接失败：{msg}",
                                    },
                                },
                            }
                        ],
                    },
                ],
            },
        ]

        # 默认配置值
        default_model = {
            "enabled": False,
            "notify": False,
            "base_url": "https://share.huamucang.top",
            "app_id": "",
            "app_key": "",
            "proxy": "",
        }

        return form_components, default_model

    @staticmethod
    def get_page(history: list = None) -> Optional[List[dict]]:
        """
        返回详情页面 JSON
        展示搜索历史和统计信息
        """
        if history is None:
            history = []

        # 统计数据
        total_searches = len(history)

        page_components = [
            # 标题
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VCard",
                                "props": {"variant": "tonal"},
                                "content": [
                                    {
                                        "component": "VCardTitle",
                                        "props": {"class": "text-h6"},
                                        "content": ["聚影搜索统计"],
                                    },
                                    {
                                        "component": "VCardText",
                                        "content": [
                                            {
                                                "component": "VRow",
                                                "content": [
                                                    {
                                                        "component": "VCol",
                                                        "props": {"cols": 4},
                                                        "content": [
                                                            {
                                                                "component": "div",
                                                                "props": {"class": "text-h4 text-center"},
                                                                "content": [str(total_searches)],
                                                            },
                                                            {
                                                                "component": "div",
                                                                "props": {"class": "text-center text-grey"},
                                                                "content": ["搜索次数"],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
            # 搜索历史
            {
                "component": "VRow",
                "props": {"class": "mt-2"},
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VCard",
                                "content": [
                                    {
                                        "component": "VCardTitle",
                                        "props": {"class": "text-h6"},
                                        "content": ["搜索历史"],
                                    },
                                    {
                                        "component": "VDataTable",
                                        "props": {
                                            "items": history[-50:],  # 最近 50 条
                                            "headers": [
                                                {"title": "时间", "key": "time", "sortable": True},
                                                {"title": "关键词", "key": "keyword"},
                                                {"title": "结果数", "key": "count"},
                                            ],
                                            "density": "compact",
                                            "hover": True,
                                        },
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
        ]

        return page_components
