"""Camoufox browser session management with threading - 支持多会话并发."""

import asyncio
import os
import threading
import time
import tempfile
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from camoufox.addons import DefaultAddons
from playwright import async_api


@dataclass
class SessionData:
    """浏览器会话数据类."""

    # 公开字段
    session_id: str
    profile_name: str
    status: str  # 'starting', 'running', 'stopping'
    started_at: str  # ISO 8601 格式

    # 内部字段（以下划线开头，不暴露给 API）
    _stop_flag: threading.Event
    _context: async_api.BrowserContext | None = None
    _temp_profile_dir: str | None = None
    _browser_thread: threading.Thread | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """返回公开字段的字典（排除内部字段）."""
        return {
            "session_id": self.session_id,
            "profile_name": self.profile_name,
            "status": self.status,
            "started_at": self.started_at,
        }


class SessionManager:
    """管理多个并发的 Camoufox 浏览器会话."""

    def __init__(self):
        # 多会话管理：dict[session_id, SessionData]
        # 为将来支持"同一 profile 多实例"预留架构空间
        self.active_sessions: dict[str, SessionData] = {}

    def _generate_session_id(self, profile_name: str) -> str:
        """
        生成唯一的 session_id.

        格式: {profile_name}-{timestamp}

        Args:
            profile_name: Profile 名称

        Returns:
            唯一的 session_id
        """
        timestamp = int(time.time() * 1000)  # 使用毫秒时间戳
        # 简单清理 profile_name 以确保 ID 格式安全
        safe_name = profile_name.replace(" ", "-").lower()
        return f"{safe_name}-{timestamp}"

    def _has_active_session(self, profile_name: str) -> bool:
        """
        检查指定 profile 是否已有活跃会话.

        当前阶段限制：每个 profile 只能启动一个实例。
        将来扩展：移除此检查即可支持同一 profile 多实例。

        Args:
            profile_name: Profile 名称

        Returns:
            True 如果 profile 已有活跃会话
        """
        return any(
            session.profile_name == profile_name
            for session in self.active_sessions.values()
        )

    def start_session(
        self,
        profile: dict[str, Any],
        screen_width: int | None = None,
        screen_height: int | None = None,
    ) -> dict[str, Any]:
        """
        启动新的 Camoufox 浏览器会话.

        当前阶段限制：每个 profile 只能启动一个实例。
        将来扩展：移除 _has_active_session() 检查即可支持同一 profile 多实例。

        Args:
            profile: Profile 配置字典
            screen_width: 全屏模式下的屏幕宽度（可选）
            screen_height: 全屏模式下的屏幕高度（可选）

        Returns:
            包含 session_id 和状态的会话字典

        Raises:
            RuntimeError: 如果该 profile 已有会话运行（当前阶段限制）
        """
        # 当前阶段限制：检查 profile 是否已有活跃会话
        # 将来扩展：移除下面这行检查即可支持同一 profile 多实例
        if self._has_active_session(profile["name"]):
            raise RuntimeError(f"Session already running for '{profile['name']}'")

        # 生成唯一的 session_id
        session_id = self._generate_session_id(profile["name"])

        # 创建会话记录
        session_data = SessionData(
            session_id=session_id,
            profile_name=profile["name"],
            status="starting",
            started_at=datetime.utcnow().isoformat() + "Z",
            _stop_flag=threading.Event(),
        )

        # 存储会话
        self.active_sessions[session_id] = session_data

        # 在后台线程中启动浏览器
        browser_thread = threading.Thread(
            target=self._run_browser,
            args=(session_id, profile, screen_width, screen_height),
            daemon=True,
        )
        session_data._browser_thread = browser_thread
        browser_thread.start()

        # 等待浏览器启动
        time.sleep(1)

        # 更新状态
        session_data.status = "running"

        # 返回公开字段
        return session_data.to_public_dict()

    def stop_session(self, session_id: str) -> None:
        """
        停止指定的浏览器会话.

        Args:
            session_id: 要停止的会话 ID

        Raises:
            RuntimeError: 如果指定的会话不存在
        """
        if session_id not in self.active_sessions:
            raise RuntimeError(f"No active session with id '{session_id}'")

        session_data = self.active_sessions[session_id]

        # 发送停止信号
        session_data._stop_flag.set()

        # 更新状态
        session_data.status = "stopping"

        # 等待线程结束（带超时）
        if session_data._browser_thread and session_data._browser_thread.is_alive():
            session_data._browser_thread.join(timeout=5)

        # 清理临时目录
        self._cleanup_temp_profile(session_data)

        # 移除会话
        del self.active_sessions[session_id]

    def get_sessions(self) -> list[dict[str, Any]]:
        """
        获取所有活跃会话的状态，自动清理已终止的会话.

        Returns:
            活跃会话列表（每个会话包含公开字段）
        """
        # 清理已终止的会话
        terminated_sessions = []
        for session_id, session_data in list(self.active_sessions.items()):
            if (
                session_data._browser_thread
                and not session_data._browser_thread.is_alive()
            ):
                terminated_sessions.append(session_id)

        # 移除已终止的会话
        for session_id in terminated_sessions:
            session_data = self.active_sessions[session_id]
            self._cleanup_temp_profile(session_data)
            del self.active_sessions[session_id]
            print(f"[*] Auto-cleaned terminated session: {session_id}")

        # 返回所有活跃会话的公开字段
        return [session.to_public_dict() for session in self.active_sessions.values()]

    def _cleanup_temp_profile(self, session_data: SessionData) -> None:
        """清理会话的临时配置目录."""
        if session_data._temp_profile_dir and os.path.exists(
            session_data._temp_profile_dir
        ):
            try:
                shutil.rmtree(session_data._temp_profile_dir)
                print(
                    f"[*] Cleaned up temporary profile: {session_data._temp_profile_dir}"
                )
            except Exception as e:
                print(f"[!] Failed to clean up temp profile: {e}")

    def _run_browser(
        self,
        session_id: str,
        profile: dict[str, Any],
        screen_width: int | None = None,
        screen_height: int | None = None,
    ) -> None:
        """
        在后台线程中运行 Camoufox 浏览器.

        Args:
            session_id: 会话 ID
            profile: Profile 配置
            screen_width: 全屏模式屏幕宽度（可选）
            screen_height: 全屏模式屏幕高度（可选）
        """
        try:
            asyncio.run(
                self._run_browser_async(
                    session_id, profile, screen_width, screen_height
                )
            )
        except Exception as e:
            print(f"[!] Error in browser session {session_id}: {e}")

    async def _run_browser_async(
        self,
        session_id: str,
        profile: dict[str, Any],
        screen_width: int | None = None,
        screen_height: int | None = None,
    ) -> None:
        """
        异步实现浏览器会话管理.

        Args:
            session_id: 会话 ID
            profile: Profile 配置
            screen_width: 全屏模式屏幕宽度（可选）
            screen_height: 全屏模式屏幕高度（可选）
        """
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            print("[!] Camoufox not installed")
            return

        # 获取会话数据
        if session_id not in self.active_sessions:
            print(f"[!] Session {session_id} not found")
            return

        session_data = self.active_sessions[session_id]

        try:
            # 获取视窗大小 - 全屏模式使用屏幕尺寸
            if profile.get("fullscreen") and screen_width and screen_height:
                width = screen_width
                height = screen_height
            else:
                width = profile.get("viewport_width", 1280)
                height = profile.get("viewport_height", 800)

            # 构建 Camoufox 选项
            opts: dict[str, Any] = {
                "headless": False,
                "window": (width + 2, height + 88),
            }

            # 持久化上下文 - 始终使用以避免 Firefox 窗口关闭问题
            if profile.get("storage_enabled", False) and profile.get("persistent_dir"):
                # 用户启用了存储 - 使用用户指定的目录
                os.makedirs(profile["persistent_dir"], exist_ok=True)
                opts["persistent_context"] = True
                opts["user_data_dir"] = os.path.abspath(profile["persistent_dir"])
            else:
                # 用户禁用了存储 - 使用临时目录（会话结束后自动清理）
                timestamp_ms = int(time.time() * 1000)
                temp_dir = os.path.join(
                    tempfile.gettempdir(), f"tmp_camoufox_profile_{timestamp_ms}"
                )
                os.makedirs(temp_dir, exist_ok=True)
                opts["persistent_context"] = True
                opts["user_data_dir"] = os.path.abspath(temp_dir)
                session_data._temp_profile_dir = temp_dir
                print(f"[*] Using temporary profile: {temp_dir}")

            # 代理配置 - 检查启用标志
            proxy_config = profile.get("proxy", {})
            if (
                proxy_config.get("enabled")
                and proxy_config.get("host")
                and proxy_config.get("port")
            ):
                protocol = proxy_config.get("protocol", "socks5")
                proxy_dict = {
                    "server": f"{protocol}://{proxy_config['host']}:{proxy_config['port']}"
                }
                if proxy_config.get("username"):
                    proxy_dict["username"] = proxy_config["username"]
                if proxy_config.get("password"):
                    proxy_dict["password"] = proxy_config["password"]

                opts["proxy"] = proxy_dict

                # GeoIP（如果启用）
                if profile.get("use_geoip"):
                    opts["geoip"] = True

            # 启动浏览器
            async with AsyncCamoufox(
                **opts,
                i_know_what_im_doing=True,
                config={
                    "disableTheming": True,
                    "showcursor": False,
                },
            ) as context:
                if not isinstance(context, async_api.BrowserContext):
                    print(
                        f"[!] Warning: Expected BrowserContext but got {type(context)} type"
                    )
                    return

                session_data._context = context

                # 获取或创建初始页面
                page: async_api.Page
                if context.pages:
                    page = context.pages[0]
                else:
                    page = await context.new_page()

                # 设置视窗大小
                try:
                    await page.set_viewport_size({"width": width, "height": height})
                except Exception:
                    pass

                # 基于事件的窗口关闭检测
                close_event = asyncio.Event()

                def handle_close(bc: async_api.BrowserContext):
                    print(f"[*] BrowserContext closed for session {session_id}")
                    close_event.set()

                context.on("close", handle_close)

                stop_flag = session_data._stop_flag
                while not stop_flag.is_set():
                    try:
                        # 等待关闭事件，带超时以检查 stop_flag
                        await asyncio.wait_for(close_event.wait(), timeout=0.5)
                        print(f"[*] Browser closed by user for session {session_id}")
                        break
                    except asyncio.TimeoutError:
                        continue  # 超时，继续检查 stop_flag

                print(f"[*] Browser session ending: {session_id}")

        except Exception as e:
            print(f"[!] Error in async browser session {session_id}: {e}")
        finally:
            # 清理由异步上下文管理器处理
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                session_data._context = None
                self._cleanup_temp_profile(session_data)


# 全局会话管理器实例
session_manager = SessionManager()
