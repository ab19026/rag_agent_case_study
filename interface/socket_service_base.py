from abc import ABC, abstractmethod

class SocketServiceBase(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass