"""데이터베이스 및 설정 테스트"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_config.settings import DEFAULT_PARTY_SIZE, AREA_CENTER
from core.db import DatabaseManager


def test_default_settings():
    """기본 설정값 변경 확인"""
    assert DEFAULT_PARTY_SIZE == 6, "기본 인원수가 6명이어야 합니다."
    assert AREA_CENTER["name"] == "한국프레스센터", "기준점이 한국프레스센터여야 합니다."


def test_db_operations(tmp_path):
    """DB 동작 테스트"""
    # 임시 DB 파일 사용
    db_path = tmp_path / "test_history.db"
    db = DatabaseManager(str(db_path))

    # 1. 즐겨찾기 추가/조회/삭제
    db.add_favorite("맛있는식당", "서울시 중구", "메모")
    assert db.is_favorite("맛있는식당", "서울시 중구")
    
    favorites = db.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["restaurant_name"] == "맛있는식당"

    db.remove_favorite("맛있는식당", "서울시 중구")
    assert not db.is_favorite("맛있는식당", "서울시 중구")

    # 2. 제외 목록 추가/조회
    db.add_exclusion("맛없는식당", "서울시 중구", "맛없음")
    assert db.is_excluded("맛없는식당", "서울시 중구")
    
    exclusions = db.get_exclusions()
    assert len(exclusions) == 1
    assert exclusions[0]["restaurant_name"] == "맛없는식당"

    # 3. 검색 이력 저장/조회
    db.save_search_result(
        restaurant_name="테스트식당",
        address="서울시",
        party_size=4
    )
    history = db.get_search_history()
    assert len(history) == 1
    assert history[0]["restaurant_name"] == "테스트식당"

if __name__ == "__main__":
    # 간단한 실행 확인
    try:
        test_default_settings()
        print("✅ Default settings test passed")
        
        # 임시 경로 대신 로컬 테스트용 파일 생성
        test_db = Path("test_db.sqlite")
        if test_db.exists():
            test_db.unlink()
            
        test_db_operations(Path("."))
        print("✅ DB operations test passed")
        
        if test_db.exists():
            test_db.unlink()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
