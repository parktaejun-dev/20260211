"""예약 이력 페이지"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

from config.settings import HISTORY_DB_PATH
from core.reservation import ReservationResult
from config.constants import RESERVATION_STATUS_SUCCESS


def init_history_db():
    """예약 이력 데이터베이스를 초기화합니다."""
    Path(HISTORY_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            restaurant_name TEXT NOT NULL,
            reservation_date TEXT,
            reservation_time TEXT,
            party_size INTEGER,
            reservation_number TEXT,
            cuisine_type TEXT,
            screenshot_path TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_reservation(result: ReservationResult, cuisine_type: str = ""):
    """예약 결과를 DB에 저장합니다."""
    init_history_db()
    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reservations
            (status, restaurant_name, reservation_date, reservation_time,
             party_size, reservation_number, cuisine_type, screenshot_path, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.status,
            result.restaurant_name,
            result.reservation_date,
            result.reservation_time,
            result.party_size,
            result.reservation_number,
            cuisine_type,
            result.screenshot_path,
            result.message,
        ),
    )
    conn.commit()
    conn.close()


def get_reservation_history(limit: int = 20) -> list[dict]:
    """최근 예약 이력을 조회합니다."""
    init_history_db()
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM reservations
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def render_history_page():
    """예약 이력 페이지를 렌더링합니다."""
    st.subheader("⏰ 예약 이력")

    history = get_reservation_history()

    if not history:
        st.info("아직 예약 이력이 없습니다.")
        return

    for record in history:
        status_emoji = "✅" if record["status"] == RESERVATION_STATUS_SUCCESS else "❌"
        date_str = record["reservation_date"] or ""
        cuisine = record["cuisine_type"] or ""
        name = record["restaurant_name"] or ""
        party = record["party_size"] or ""

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"{status_emoji} **{date_str}** {cuisine} "
                f"{name} {party}명"
            )
        with col2:
            if record["reservation_number"]:
                st.caption(f"#{record['reservation_number']}")

        st.caption(f"  └ {record['message']}")
        st.divider()
