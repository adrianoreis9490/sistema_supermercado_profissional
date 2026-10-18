"""Funções simples para armazenar senhas com hash PBKDF2."""
import hashlib
import hmac
import os

def gerar_hash(senha):
    salt = os.urandom(16)
    chave = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 200_000)
    return salt.hex() + ":" + chave.hex()

def verificar_senha(senha, valor_salvo):
    try:
        salt_hex, hash_hex = valor_salvo.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(hash_hex)
        atual = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 200_000)
        return hmac.compare_digest(atual, esperado)
    except (ValueError, TypeError):
        return False
