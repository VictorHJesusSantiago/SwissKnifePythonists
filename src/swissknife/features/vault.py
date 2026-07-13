from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from swissknife.core.utils import atomic_write


class SecretVault:
    """Cofre autenticado local; usa AES-GCM quando cryptography está disponível."""

    def __init__(self, path: str | Path, password: str):
        if len(password) < 8:
            raise ValueError("A senha mestra deve ter ao menos 8 caracteres")
        self.path = Path(path)
        self.password = password.encode()

    def _key(self, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", self.password, salt, 600_000, dklen=32)

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        salt, nonce, ciphertext = (
            base64.b64decode(envelope[name]) for name in ("salt", "nonce", "ciphertext")
        )
        key = self._key(salt)
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:
            raise RuntimeError("Instale cryptography para usar o cofre") from exc
        plain = AESGCM(key).decrypt(nonce, ciphertext, b"swissknife-vault-v1")
        return json.loads(plain)

    def _save(self, values: dict[str, str]) -> None:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        salt, nonce = os.urandom(16), os.urandom(12)
        ciphertext = AESGCM(self._key(salt)).encrypt(
            nonce, json.dumps(values).encode(), b"swissknife-vault-v1"
        )
        envelope = {
            "version": 1,
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        atomic_write(self.path, json.dumps(envelope))
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def set(self, name: str, value: str) -> None:
        values = self._load()
        values[name] = value
        self._save(values)

    def get(self, name: str) -> str:
        values = self._load()
        if name not in values:
            raise KeyError(name)
        return values[name]

    def delete(self, name: str) -> bool:
        values = self._load()
        removed = values.pop(name, None) is not None
        if removed:
            self._save(values)
        return removed

    def names(self) -> list[str]:
        return sorted(self._load())
