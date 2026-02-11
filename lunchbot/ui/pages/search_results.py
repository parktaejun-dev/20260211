"""검색 결과 페이지"""

import streamlit as st

from core.search import Restaurant
from ui.components import render_restaurant_card
from utils.date_helper import format_date_korean


def render_search_results(
    restaurants: list[Restaurant],
    input_data: dict,
) -> Restaurant | None:
    """
    검색 결과를 표시하고 사용자가 선택한 식당을 반환합니다.
    """
    cuisine = input_data["cuisine"]
    area = input_data["area"]
    radius = input_data["radius"]
    radius_text = f"{radius}m" if radius < 1000 else f"{radius / 1000:.0f}km"

    st.subheader(f"🔍 검색 결과 ({cuisine} / {area} {radius_text})")

    if not restaurants:
        st.warning("검색 결과가 없습니다. 반경을 넓히거나 다른 조건을 선택해보세요.")
        if st.button("🔄 다시 검색하기"):
            st.session_state["search_results"] = None
            st.rerun()
        return None

    st.info(f"총 {len(restaurants)}개 식당을 찾았습니다.")

    # 식당 목록 표시
    selected_idx = None
    for i, restaurant in enumerate(restaurants, 1):
        render_restaurant_card(restaurant, i)

    # 식당 선택
    st.markdown("---")
    restaurant_names = [f"{i}. {r.name}" for i, r in enumerate(restaurants, 1)]
    chosen = st.selectbox("✅ 예약할 식당을 선택하세요", options=restaurant_names)

    if chosen:
        selected_idx = int(chosen.split(".")[0]) - 1
        selected = restaurants[selected_idx]

        # 선택한 식당 정보 요약
        date_str = format_date_korean(input_data["date"])
        time_str = input_data["time"]
        party = input_data["party_size"]

        st.success(
            f"**{selected.name}** | {date_str} {time_str} | {party}명"
        )

        # ── DB 액션 버튼 (즐겨찾기 / 제외) ────────────────
        from core.db import db

        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            if db.is_favorite(selected.name, selected.address):
                if st.button("❌ 즐겨찾기 해제", key=f"fav_del_{selected.name}"):
                    db.remove_favorite(selected.name, selected.address)
                    st.rerun()
            else:
                if st.button("⭐ 즐겨찾기 추가", key=f"fav_add_{selected.name}"):
                    if db.add_favorite(selected.name, selected.address):
                        st.toast("즐겨찾기에 추가되었습니다!", icon="⭐")
                        st.rerun()

        with col_act2:
            if st.button("🚫 이 식당 제외하기", key=f"excl_{selected.name}"):
                if db.add_exclusion(selected.name, selected.address, reason="사용자 선택"):
                    st.warning("제외 목록에 추가되었습니다. 앞으로 검색되지 않습니다.")
                    st.session_state["search_results"] = None  # 결과 초기화
                    st.rerun()
        # ────────────────────────────────────────────────

        info_text = (
            f"[부서점심 안내]\n"
            f"🏪 식당: {selected.name}\n"
            f"📍 주소: {selected.road_address or selected.address}\n"
            f"📅 날짜: {date_str} {time_str}\n"
            f"👥 인원: {party}명\n"
        )
        if selected.phone:
            info_text += f"📞 전화: {selected.phone}\n"

        st.text_area("📋 공유용 텍스트 (복사하세요)", value=info_text, height=180)

        if selected.link:
            st.link_button(
                "🔗 네이버에서 예약/상세보기",
                selected.link,
                type="primary",
                use_container_width=True,
            )

        return selected

    return None
