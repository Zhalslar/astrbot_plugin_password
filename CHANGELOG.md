# 更新日志

## v1.1.0

### 修复与适配

- 适配 AstrBot 4.0+ 全新密码存储机制：
  - 接入 `pbkdf2_sha256` 密码哈希生成，同时同步写入 `pbkdf2_password`。
  - 同步设置 `password_storage_upgraded=True` 与 `password_change_required=False`，防止控制台强制要求再次改密。
  - 接入 AstrBot 官方密码复杂度校验逻辑（长度≥8且包含大小写字母和数字）。
  - 保留 MD5 回退逻辑以向下兼容。
