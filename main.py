import json

from astrbot import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.filter.permission import PermissionType

try:
    from astrbot.core.utils.auth_password import (
        hash_dashboard_password,
        hash_md5_dashboard_password,
        validate_dashboard_password,
    )
except ImportError:
    # 兼容低版本
    import hashlib
    import re

    def hash_dashboard_password(raw: str) -> str | None:
        return None

    def hash_md5_dashboard_password(raw: str) -> str:
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def validate_dashboard_password(raw: str) -> None:
        if len(raw) < 4:
            raise ValueError("密码长度至少为4位")
        if not re.match(r"^[A-Za-z0-9!@#$%^&*(),.?\":{}|<>]+$", raw):
            raise ValueError("密码只能包含大小写字母、数字和特殊字符")


CMD_CONFIG_PATH = "data/cmd_config.json"


class PasswordPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    def _load_json_data(self) -> dict:
        """加载并解析 JSON 文件，去除 BOM"""
        with open(CMD_CONFIG_PATH, encoding="utf-8") as file:
            content = file.read()
            if content.startswith("\ufeff"):
                content = content[1:]  # 去除 BOM
            data = json.loads(content)
        return data

    def _save_json_data(self, data: dict):
        """将数据保存到 JSON 文件"""
        with open(CMD_CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("修改用户名")
    async def change_username(
        self, event: AstrMessageEvent, input_username: int | str | None = None
    ):
        """/修改用户名 xxx"""
        if not input_username:
            yield event.plain_result("未输入新用户名")
            return
        new_username = str(input_username).strip()
        if not new_username:
            yield event.plain_result("用户名不能为空")
            return

        data = self._load_json_data()
        if "dashboard" not in data:
            data["dashboard"] = {}
        data["dashboard"]["username"] = new_username
        self._save_json_data(data)

        yield event.plain_result(
            f"Astrbot的面板用户名已更新为: {new_username}\n重启bot后生效"
        )
        logger.info(f"Astrbot的面板用户名已更新为 {new_username}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("修改密码")
    async def change_password(
        self, event: AstrMessageEvent, input_password: int | str | None = None
    ):
        """/修改密码 xxx"""
        if not input_password:
            yield event.plain_result("未输入新密码")
            return

        new_password = str(input_password).strip()

        # 校验密码复杂度
        try:
            validate_dashboard_password(new_password)
        except ValueError as e:
            yield event.plain_result(f"密码不符合要求: {e}")
            return

        # 更新配置
        data = self._load_json_data()
        if "dashboard" not in data:
            data["dashboard"] = {}

        # 写入 PBKDF2 哈希（Astrbot v4+）与兼容 MD5
        pbkdf2_hash = hash_dashboard_password(new_password)
        if pbkdf2_hash:
            data["dashboard"]["pbkdf2_password"] = pbkdf2_hash
            data["dashboard"]["password_storage_upgraded"] = True
            data["dashboard"]["password_change_required"] = False

        data["dashboard"]["password"] = hash_md5_dashboard_password(new_password)

        self._save_json_data(data)

        masked_password = new_password[0] + "*" * (len(new_password) - 1)
        yield event.plain_result(
            f"Astrbot的面板密码已更新为: {masked_password}\n重启bot后生效"
        )
        logger.info(f"Astrbot的面板登录密码已更新为 {masked_password}")
