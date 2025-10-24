import logging, os, time, threading
from logging.handlers import RotatingFileHandler
from typing import Optional, Protocol
from typing import TYPE_CHECKING
from logging import LoggerAdapter
if TYPE_CHECKING:
    from .env_model import Env

class _NodeNameFilter(logging.Filter):
    """%(node_name)s KeyError 방지: 레코드에 node_name 필드 강제 주입"""
    def __init__(self, default_node: str = "-"):
        super().__init__()
        self.default_node = default_node
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "node_name"):
            record.node_name = self.default_node
        return True

class RunLogger:

    _MAX_BYTES = 1_000_000
    _BACKUP_COUNT = 3
    _FMT_WITH_NODE_NAME = "%(asctime)s [%(levelname)s] [%(node_name)s] %(name)s: %(message)s"
    _DATEFMT = None

    def __init__(self, base_name: str = "agent", level: int = logging.DEBUG):
        self.base_name = base_name
        self.level = level
        self._configured_for: Optional[str] = None  # run_id
        self.log_path: Optional[str] = None
        self._lock = threading.Lock()

    @staticmethod
    def _abs(*paths: str) -> str:
        return os.path.abspath(os.path.join(*paths))


    def _setup_handlers(self, root_logger: logging.Logger, run_id: str, logs_dir: str):
        """같은 run_id면 재설정 생략. 다르면 핸들러 교체."""
        with self._lock:
            if self._configured_for == run_id and root_logger.handlers:
                return

            for h in list(root_logger.handlers):
                root_logger.removeHandler(h)
            root_logger.setLevel(self.level)
            root_logger.propagate = False

            os.makedirs(logs_dir, exist_ok=True)
            self.log_path = self._abs(logs_dir, f"{run_id}.log")

            # Include thread name for clarity in concurrent runs
            formatter = logging.Formatter(self._FMT_WITH_NODE_NAME + " [%(threadName)s]", datefmt=self._DATEFMT)
            node_filter = _NodeNameFilter("-")

            file_handler = RotatingFileHandler(
                self.log_path,
                maxBytes=self._MAX_BYTES,
                backupCount=self._BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(node_filter)
            file_handler.setLevel(self.level)
            root_logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.addFilter(node_filter)
            console_handler.setLevel(logging.INFO)
            root_logger.addHandler(console_handler)

            self._configured_for = run_id
        
    def _get_root_logger(self, work_dir: str, user_id: str, run_id: str) -> logging.Logger:
        logs_dir = self._abs(work_dir, "users", user_id, run_id, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        root_name = f"{self.base_name}.{user_id}.{run_id}"
        root_logger = logging.getLogger(root_name)
        self._setup_handlers(root_logger, run_id, logs_dir)
        return root_logger


    def get_logger(self, work_dir: str, user_id: str, run_id: str, node_name: Optional[str] = None) -> logging.LoggerAdapter:
        """노드에서 바로 쓰는 메인 API. 항상 LoggerAdapter 반환."""
        root = self._get_root_logger(work_dir, user_id, run_id)
        name = root.name if node_name is None else f"{root.name}.{node_name}"
        base = logging.getLogger(name)
        return logging.LoggerAdapter(base, {"node_name": node_name or "-"})

class RunLoggerLike(Protocol):
    def get_logger(self, work_dir: str, user_id: str, run_id: str, node_name: Optional[str] = None) -> LoggerAdapter:
        ...

class NoopLoggerAdapter(LoggerAdapter):
    def __init__(self):
        super().__init__(logging.getLogger("noop"), {})
        self.logger.disabled = True  # 어떤 레벨도 출력 안 함
    def process(self, msg, kwargs):
        return msg, kwargs

class NoopRunLogger:
    """RunLogger와 동일한 인터페이스로 get_logger만 제공"""
    def get_logger(self, *_, **__) -> LoggerAdapter:
        return NoopLoggerAdapter()
