import logging, os, time
from logging.handlers import RotatingFileHandler
from typing import Optional

class RunLogger:
    def __init__(self, base_name: str = "agent", level: int = logging.DEBUG):
        self.base_name = base_name
        self.level = level
        self._configured_for: Optional[str] = None  # run_id
        self.log_path: Optional[str] = None

    @staticmethod
    def _abs(*paths: str) -> str:
        return os.path.abspath(os.path.join(*paths))

    def configure_logger(self, state: dict, component: Optional[str] = None) -> logging.Logger:
        artifact_dir = state.get("artifact_dir", "./artifacts")
        run_id = state.get("run_id") or str(int(time.time()))
        state.setdefault("run_id", run_id)

        logs_dir = self._abs(artifact_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        if self._configured_for != run_id:
            self.log_path = self._abs(logs_dir, f"{run_id}.log")
            logger = logging.getLogger(f"{self.base_name}.{run_id}")
            logger.setLevel(self.level)
            logger.handlers.clear()

            formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(component)s] %(name)s: %(message)s")
            file_handler = RotatingFileHandler(self.log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
            file_handler.setFormatter(formatter)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.propagate = False

            self._configured_for = run_id
            state.setdefault("log_file", self.log_path)

        if component:
            return logging.getLogger(f"{self.base_name}.{run_id}.{component}")
        return logging.getLogger(f"{self.base_name}.{run_id}")