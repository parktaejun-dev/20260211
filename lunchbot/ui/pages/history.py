"""검색 이력 페이지"""

import sqlite3
from pathlib import Path

import streamlit as st

from config.settings import HISTORY_DB_PATH


def init_history_db():
    """검색 이력 데이터베이스를 초기화합니다."""
    Path(HISTORY_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()


def save_search_result(
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
    """선택한 식당 정보를 DB에 저장합니다."""
    init_history_db()
    conn = sqlite3.connect(HISTORY_DB_PATH)
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
    conn.close()


def get_search_history(limit: int = 20) -> list[dict]:
    """최근 검색 이력을 조회합니다."""
    init_history_db()
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM search_history ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def render_history_page():
    """검색 이력 페이지를 렌더링합니다."""
    st.subheader("📜 검색 이력")

    history = get_search_history()

    if not history:
        st.info("아직 검색 이력이 없습니다.")
        return

    for record in history:
        date_str = record["reservation_date"] or ""
        time_str = record["reservation_time"] or ""
        cuisine = record["cuisine_type"] or ""
        name = record["restaurant_name"] or ""
        party = record["party_size"] or ""
        area = record["area"] or ""

        with st.container(border=True):
            st.markdown(
                f"**{name}** — {cuisine} | {area}"
            )
            st.caption(
                f"📅 {date_str} {time_str} | 👥 {party}명"
            )
            if record["phone"]:
                st.caption(f"📞 {record['phone']}")
