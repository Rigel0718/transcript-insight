import logging, os, time
from logging.handlers import RotatingFileHandler
from typing import Optional
from typing import TYPE_CHECKING
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

    @staticmethod
    def _abs(*paths: str) -> str:
        return os.path.abspath(os.path.join(*paths))


    def _setup_handlers(self, root_logger: logging.Logger, run_id: str, logs_dir: str):
        """같은 run_id면 재설정 생략. 다르면 핸들러 교체."""
        if self._configured_for == run_id and root_logger.handlers:
            return
        
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)
        root_logger.setLevel(self.level)
        root_logger.propagate = False

        os.makedirs(logs_dir, exist_ok=True)
        self.log_path = self._abs(logs_dir, f"{run_id}.log")

        formatter = logging.Formatter(self._FMT_WITH_NODE_NAME, datefmt=self._DATEFMT)
        node_filter = _NodeNameFilter("-")

        fh = RotatingFileHandler(
            self.log_path,
            maxBytes=self._MAX_BYTES,
            backupCount=self._BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setFormatter(formatter)
        fh.addFilter(node_filter)
        root_logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.addFilter(node_filter)
        root_logger.addHandler(ch)

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
