from pathlib import Path

from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if ".." in key.replace("\\", "/").split("/"):
            raise ValueError("Invalid storage key")
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root)):
            raise ValueError("Invalid storage key")
        return path

    def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def load(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def health(self) -> dict:
        writable = False
        try:
            probe = self.root / ".health"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable = True
        except OSError:
            writable = False
        return {"backend": "local", "writable": writable, "configured": True}
