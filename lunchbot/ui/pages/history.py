"""검색 이력 페이지"""

import streamlit as st
from core.db import db


def render_history_tab():
    """검색 이력 탭 렌더링"""
    _render_search_history()


def _render_search_history():
    st.subheader("최근 검색 이력")
    history = db.get_search_history()

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

            # 즐겨찾기 여부 표시
            if db.is_favorite(name, record["address"]):
                st.caption("⭐ 즐겨찾기 등록됨")
