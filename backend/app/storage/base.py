from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def load(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict:
        raise NotImplementedError
