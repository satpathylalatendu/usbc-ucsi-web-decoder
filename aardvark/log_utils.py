import logging
import os
import sys
from datetime import datetime, timedelta


def get_log_root_dir():
    """Return the directory where runtime logs should be written."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.getcwd()


def get_log_file_path(prefix='aardvark'):
    """Build a timestamped log file path under the runtime logs directory."""
    log_dir = os.path.join(get_log_root_dir(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return os.path.join(log_dir, filename)


def setup_file_logger(logger_name, prefix='aardvark'):
    """Configure a module logger with a file handler the first time it is needed."""
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.FileHandler(get_log_file_path(prefix), encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


def cleanup_old_logs(days=7, prefix='aardvark'):
    """Remove log files older than the specified number of days."""
    try:
        log_dir = os.path.join(get_log_root_dir(), 'logs')
        if not os.path.exists(log_dir):
            return {'cleaned': 0, 'error': None}
        
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for filename in os.listdir(log_dir):
            if not filename.startswith(prefix):
                continue
            
            filepath = os.path.join(log_dir, filename)
            if not os.path.isfile(filepath):
                continue
            
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_mtime < cutoff_time:
                try:
                    os.remove(filepath)
                    cleaned += 1
                except Exception:
                    pass
        
        return {'cleaned': cleaned, 'error': None}
    except Exception as e:
        return {'cleaned': 0, 'error': str(e)}
