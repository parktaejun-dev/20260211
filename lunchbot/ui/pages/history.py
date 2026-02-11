"""검색 이력 페이지"""

import streamlit as st

from core.db import db


def render_history_page():
    """DB 관리 페이지 (이력/즐겨찾기/제외목록)"""
    st.title("🗂️ 내 데이터 관리")

    tab1, tab2, tab3 = st.tabs(["📜 검색 이력", "⭐ 즐겨찾기", "🚫 제외 식당"])

    with tab1:
        _render_search_history()

    with tab2:
        _render_favorites()

    with tab3:
        _render_exclusions()


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


def _render_favorites():
    st.subheader("즐겨찾기 목록")
    favorites = db.get_favorites()

    if not favorites:
        st.info("즐겨찾기한 식당이 없습니다.")
        return

    for item in favorites:
        name = item["restaurant_name"]
        address = item["address"] or ""
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{name}**")
            if address:
                st.caption(f"📍 {address}")
        
        with col2:
            if st.button("삭제", key=f"del_fav_{item['id']}"):
                db.remove_favorite(name, address)
                st.toast(f"{name} 즐겨찾기 삭제 완료")
                st.rerun()
        st.divider()


def _render_exclusions():
    st.subheader("제외된 식당 목록")
    st.caption("이 목록에 있는 식당은 검색 결과에 나타나지 않습니다.")
    
    exclusions = db.get_exclusions()

    if not exclusions:
        st.info("제외된 식당이 없습니다.")
        return

    for item in exclusions:
        name = item["restaurant_name"]
        address = item["address"] or ""
        reason = item["reason"] or ""
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{name}**")
            if address:
                st.caption(f"📍 {address}")
            if reason:
                st.caption(f"📝 사유: {reason}")
        
        with col2:
            if st.button("복구", key=f"restore_excl_{item['id']}"):
                db.remove_exclusion(name, address)
                st.toast(f"{name} 복구 완료 (다시 검색됨)")
                st.rerun()
        st.divider()
