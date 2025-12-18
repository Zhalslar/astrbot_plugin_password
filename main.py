import hashlib
import json
import re

from astrbot import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.filter.permission import PermissionType

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

    def _is_valid(self, password: str) -> bool:
        """验证字符是否符合要求"""
        # 密码长度至少为4位
        if len(password) < 4:
            return False
        # 密码只能包含大小写字母、数字和特殊字符
        if not re.match(r"^[A-Za-z0-9!@#$%^&*(),.?\":{}|<>]+$", password):
            return False
        return True

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("修改用户名")
    async def change_username(
        self, event: AstrMessageEvent, input_username:int|str|None=None):
        """/修改用户名 xxx"""
        if not input_username:
            yield event.plain_result("未输入新用户名")
            return
        # 兼容int和str
        new_username = str(input_username)

        # 更新 JSON 数据中的用户名 (同时确保键存在)
        data = self._load_json_data()
        if "dashboard" not in data:
            data["dashboard"] = {}
        data["dashboard"]["username"] = new_username
        self._save_json_data(data)

        yield event.plain_result(
            f"Astrbot的面板用户名已更新为{new_username}\n重启bot后生效"
        )
        logger.info(f"Astrbot的面板用户名已更新为{new_username}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("修改密码")
    async def change_password(self, event: AstrMessageEvent, input_password:int|str|None=None):
        """/修改密码 xxx"""
        if not input_password:
            yield event.plain_result("未输入新密码")
            return
        # 兼容int和str
        new_password = str(input_password)

        # 验证新密码是否符合要求
        if not self._is_valid(new_password):
            yield event.plain_result(
                "密码不符合要求，请确保密码仅包含大小写字母、数字和特殊字符，且长度至少为4位"
            )
            return

        # 将新密码转换为 MD5 哈希值
        md5_hash = hashlib.md5(new_password.encode("utf-8")).hexdigest()

        # 更新 JSON 数据中的密码 (同时确保键存在)
        data = self._load_json_data()
        if "dashboard" not in data:
            data["dashboard"] = {}
        data["dashboard"]["password"] = md5_hash
        self._save_json_data(data)

        masked_password = str(new_password)[0] + "*" * (len(str(new_password)) - 1)
        yield event.plain_result(
            f"Astrbot的面板密码已更新为{masked_password}\n重启bot后生效"
        )
        logger.info(f"Astrbot的面板登录密码已更新为{new_password}")
