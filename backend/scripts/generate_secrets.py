#!/usr/bin/env python3
"""
生成安全密钥用于 PayDay 配置

使用方法:
    python scripts/generate_secrets.py

这将生成三个密钥：
1. JWT_SECRET_KEY - JWT token 签名密钥
2. ENCRYPTION_SECRET_KEY - 薪资数据加密密钥
3. VITE_TOKEN_ENCRYPTION_KEY - Admin Web token 加密密钥

将生成的密钥添加到对应的 .env 文件中
"""
import secrets


def generate_jwt_secret() -> str:
    """生成 JWT 密钥（至少 32 字节）"""
    return secrets.token_urlsafe(43)  # ~43 字符 = ~32 字节


def generate_encryption_secret() -> str:
    """生成加密密钥（32 字节 URL-safe base64）"""
    return secrets.token_urlsafe(43)  # ~43 字符 = ~32 字节


def generate_admin_token_key() -> str:
    """生成 Admin Web token 加密密钥"""
    return secrets.token_urlsafe(32)  # ~32 字符 = ~24 字节


def main():
    print("=" * 70)
    print("PayDay 安全密钥生成器")
    print("=" * 70)
    print()

    print("请将以下密钥添加到对应的 .env 文件中：")
    print()

    # Backend .env
    print("# backend/.env")
    jwt_secret = generate_jwt_secret()
    enc_secret = generate_encryption_secret()
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"ENCRYPTION_SECRET_KEY={enc_secret}")
    print()

    # Admin Web .env
    print("# admin-web/.env")
    admin_key = generate_admin_token_key()
    print(f"VITE_TOKEN_ENCRYPTION_KEY={admin_key}")
    print()

    print("=" * 70)
    print("重要提醒：")
    print("=" * 70)
    print("1. 请妥善保管这些密钥，不要提交到代码仓库")
    print("2. 生产环境应该使用不同的密钥")
    print("3. 如果密钥泄露，立即重新生成")
    print()


if __name__ == "__main__":
    main()
