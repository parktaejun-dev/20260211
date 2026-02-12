"""데이터베이스 관리 모듈

검색 이력, 즐겨찾기, 제외 목록을 관리하는 중앙 DB 모듈입니다.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from app_config.settings import HISTORY_DB_PATH


@dataclass
class SearchRecord:
    id: int
    created_at: str
    restaurant_name: str
    address: str
    phone: str
    cuisine_type: str
    area: str
    reservation_date: str
    reservation_time: str
    party_size: int
    link: str


class DatabaseManager:
    def __init__(self, db_path: str = HISTORY_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """DB 테이블을 초기화합니다."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 검색 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    restaurant_name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    cuisine_type TEXT,
                    area TEXT,
                    reservation_date TEXT,
                    reservation_time TEXT,
                    party_size INTEGER,
                    link TEXT
                )
            """)

            # 즐겨찾기 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    restaurant_name TEXT NOT NULL,
                    address TEXT,
                    memo TEXT
                )
            """)
            # 식당 이름 + 주소 복합 유니크 제약
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_favorites_name_addr 
                ON favorites (restaurant_name, address)
            """)

            # 제외 목록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exclusions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    restaurant_name TEXT NOT NULL,
                    address TEXT,
                    reason TEXT
                )
            """)
            # 식당 이름 + 주소 복합 유니크 제약
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_exclusions_name_addr 
                ON exclusions (restaurant_name, address)
            """)

            conn.commit()

    # ─── 검색 이력 ──────────────────────────────────────────────
    def save_search_result(
        self,
        restaurant_name: str,
        address: str = "",
        phone: str = "",
        cuisine_type: str = "",
        area: str = "",
        reservation_date: str = "",
        reservation_time: str = "",
        party_size: int = 0,
        link: str = "",
    ):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO search_history
                    (restaurant_name, address, phone, cuisine_type, area,
                     reservation_date, reservation_time, party_size, link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    restaurant_name,
                    address,
                    phone,
                    cuisine_type,
                    area,
                    reservation_date,
                    reservation_time,
                    party_size,
                    link,
                ),
            )
            conn.commit()

    def get_search_history(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM search_history ORDER BY created_at DESC, id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ─── 즐겨찾기 ────────────────────────────────────────────────
    def add_favorite(self, name: str, address: str, memo: str = ""):
        """즐겨찾기에 추가합니다. 이미 존재하면 무시합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO favorites (restaurant_name, address, memo) VALUES (?, ?, ?)",
                    (name, address, memo),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_favorite(self, name: str, address: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM favorites WHERE restaurant_name = ? AND address = ?",
                (name, address),
            )
            conn.commit()

    def is_favorite(self, name: str, address: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM favorites WHERE restaurant_name = ? AND address = ?",
                (name, address),
            )
            return cursor.fetchone() is not None

    def get_favorites(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM favorites ORDER BY created_at DESC, id DESC")
            return [dict(row) for row in cursor.fetchall()]

    # ─── 제외 목록 ──────────────────────────────────────────────
    def add_exclusion(self, name: str, address: str, reason: str = ""):
        """제외 목록에 추가합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO exclusions (restaurant_name, address, reason) VALUES (?, ?, ?)",
                    (name, address, reason),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_exclusion(self, name: str, address: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM exclusions WHERE restaurant_name = ? AND address = ?",
                (name, address),
            )
            conn.commit()

    def is_excluded(self, name: str, address: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM exclusions WHERE restaurant_name = ? AND address = ?",
                (name, address),
            )
            return cursor.fetchone() is not None

    def get_exclusions(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exclusions ORDER BY created_at DESC, id DESC")
            return [dict(row) for row in cursor.fetchall()]


    def search_favorites(self, query: str) -> list[dict]:
        """즐겨찾기에서 검색합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            pattern = f"%{query}%"
            cursor.execute(
                "SELECT * FROM favorites WHERE restaurant_name LIKE ? OR address LIKE ? OR memo LIKE ? ORDER BY created_at DESC, id DESC",
                (pattern, pattern, pattern),
            )
            return [dict(row) for row in cursor.fetchall()]
            
    def import_favorites(self, data: list[dict]) -> int:
        """
        딕셔너리 리스트를 즐겨찾기에 일괄 추가합니다.
        data example: [{'name': '..', 'address': '..', 'memo': '..'}]
        Return: 추가된 개수
        """
        count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for item in data:
                try:
                    cursor.execute(
                        "INSERT INTO favorites (restaurant_name, address, memo) VALUES (?, ?, ?)",
                        (item.get("name"), item.get("address", ""), item.get("memo", "")),
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    continue # 중복 무시
            conn.commit()
        return count


# 전역 인스턴스
db = DatabaseManager()
