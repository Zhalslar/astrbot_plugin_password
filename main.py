import json
import os

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.filter.permission import PermissionType
from astrbot.core.utils.auth_password import (
    hash_dashboard_password,
    hash_md5_dashboard_password,
    validate_dashboard_password,
)

CMD_CONFIG_PATH = "data/cmd_config.json"


class PasswordPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    def _load_json_data(self) -> dict:
        """加载并解析 JSON 文件，去除 BOM，并加入容错"""
        if not os.path.exists(CMD_CONFIG_PATH):
            raise FileNotFoundError(f"配置文件不存在: {CMD_CONFIG_PATH}")
        try:
            with open(CMD_CONFIG_PATH, encoding="utf-8") as file:
                content = file.read()
                if content.startswith("\ufeff"):
                    content = content[1:]
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError("配置文件内容格式错误，非有效字典")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件 JSON 损坏无法解析: {e}")

    def _save_json_data(self, data: dict):
        """将数据安全保存到 JSON 文件"""
        temp_path = f"{CMD_CONFIG_PATH}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        os.replace(temp_path, CMD_CONFIG_PATH)

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

        try:
            data = self._load_json_data()
        except Exception as e:
            yield event.plain_result(f"读取配置文件失败: {e}")
            logger.error(f"读取 {CMD_CONFIG_PATH} 失败: {e}")
            return

        if "dashboard" not in data or not isinstance(data["dashboard"], dict):
            data["dashboard"] = {}
        data["dashboard"]["username"] = new_username

        try:
            self._save_json_data(data)
        except Exception as e:
            yield event.plain_result(f"保存配置文件失败: {e}")
            logger.error(f"保存 {CMD_CONFIG_PATH} 失败: {e}")
            return

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

        try:
            validate_dashboard_password(new_password)
        except ValueError as e:
            yield event.plain_result(f"密码不符合要求: {e}")
            return

        try:
            data = self._load_json_data()
        except Exception as e:
            yield event.plain_result(f"读取配置文件失败: {e}")
            logger.error(f"读取 {CMD_CONFIG_PATH} 失败: {e}")
            return

        if "dashboard" not in data or not isinstance(data["dashboard"], dict):
            data["dashboard"] = {}

        pbkdf2_hash = hash_dashboard_password(new_password)
        if pbkdf2_hash:
            data["dashboard"]["pbkdf2_password"] = pbkdf2_hash
            data["dashboard"]["password_storage_upgraded"] = True
            data["dashboard"]["password_change_required"] = False

        data["dashboard"]["password"] = hash_md5_dashboard_password(new_password)

        try:
            self._save_json_data(data)
        except Exception as e:
            yield event.plain_result(f"保存配置文件失败: {e}")
            logger.error(f"保存 {CMD_CONFIG_PATH} 失败: {e}")
            return

        masked_password = new_password[0] + "*" * (len(new_password) - 1)
        yield event.plain_result(
            f"Astrbot的面板密码已更新为: {masked_password}\n重启bot后生效"
        )
        logger.info(f"Astrbot的面板登录密码已更新为 {masked_password}")
