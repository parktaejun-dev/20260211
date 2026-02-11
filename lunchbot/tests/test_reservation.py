"""이력 모듈 테스트"""

import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# 테스트용 DB 경로 설정
import app_config.settings as settings

TEST_DB = "/tmp/test_lunchbot_history.db"
settings.HISTORY_DB_PATH = TEST_DB

from ui.pages.history import init_history_db, save_search_result, get_search_history


def _reset_db():
    """테스트 DB를 완전 초기화."""
    db_path = Path(TEST_DB)
    if db_path.exists():
        db_path.unlink()
    init_history_db()


def test_init_history_db():
    """DB 초기화 테스트."""
    _reset_db()
    assert Path(TEST_DB).exists()


def test_empty_history():
    """빈 이력 조회 테스트."""
    _reset_db()
    history = get_search_history()
    assert history == []


def test_save_and_get_history():
    """이력 저장 및 조회 테스트."""
    _reset_db()
    save_search_result(
        restaurant_name="테스트식당",
        address="서울 종로구",
        cuisine_type="한식",
        area="광화문",
        reservation_date="2026년 2월 16일 (월)",
        reservation_time="12:00",
        party_size=12,
    )

    history = get_search_history()
    assert len(history) == 1
    assert history[0]["restaurant_name"] == "테스트식당"
    assert history[0]["party_size"] == 12
