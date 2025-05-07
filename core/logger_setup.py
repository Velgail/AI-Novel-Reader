import logging
import sys
from logging.handlers import RotatingFileHandler
import os

LOG_FILE_PATH = "data/app.log" # ログファイルパス (dataフォルダは.gitignore対象)
MAX_BYTES = 1024 * 1024 * 5  # 5MB
BACKUP_COUNT = 5

# setup_logger 関数内、file_handler の設定前に追加
log_dir = os.path.dirname(LOG_FILE_PATH)
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except OSError as e:
        # logger がまだ完全に設定されていない可能性があるため、基本的なprintで警告
        print(f"Warning: Failed to create log directory {log_dir}: {e}")
        print("Warning: File logging may be disabled.")

def setup_logger(log_level=logging.INFO):
    logger = logging.getLogger(__name__.split('.')[0]) # プロジェクトルートのロガー名
    if logger.hasHandlers(): # 既にハンドラが設定されていれば何もしない (重複防止)
        return logger

    logger.setLevel(log_level)

    # フォーマッタ
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ (ローテーティング)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to set up file handler: {e}")
        logger.warning("File logging will be disabled.")


    logger.info("Logger setup complete.")
    return logger

# グローバルロガーインスタンス (必要に応じてアプリケーション全体で共有)
# logger = setup_logger()
