"""스크린샷 관리 유틸리티"""

import os
from datetime import datetime
from pathlib import Path

from config.settings import SCREENSHOT_DIR


def get_screenshot_dir() -> Path:
    """스크린샷 저장 디렉토리를 반환. 없으면 생성."""
    path = Path(SCREENSHOT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_screenshot_path(prefix: str = "reservation") -> str:
    """타임스탬프 기반 스크린샷 파일 경로 생성."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    return str(get_screenshot_dir() / filename)


def cleanup_old_screenshots(max_days: int = 30) -> int:
    """오래된 스크린샷 파일 정리. 삭제된 파일 수를 반환."""
    screenshot_dir = get_screenshot_dir()
    cutoff = datetime.now().timestamp() - (max_days * 86400)
    deleted = 0

    for f in screenshot_dir.glob("*.png"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            deleted += 1

    return deleted
