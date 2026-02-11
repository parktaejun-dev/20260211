"""검색 결과 페이지"""

import streamlit as st

from core.search import Restaurant
from ui.components import render_restaurant_card


def render_search_results(
    restaurants: list[Restaurant],
    cuisine: str,
    radius: int,
) -> Restaurant | None:
    """
    검색 결과를 표시하고 사용자가 선택한 식당을 반환합니다.

    Returns:
        선택된 Restaurant 또는 None
    """
    radius_text = f"{radius}m" if radius < 1000 else f"{radius/1000:.0f}km"
    st.subheader(f"🔍 검색 결과 ({cuisine} / 광화문 {radius_text})")

    if not restaurants:
        st.warning("검색 결과가 없습니다. 반경을 넓히거나 다른 음식 종류를 선택해보세요.")
        if st.button("🔄 반경 넓혀서 다시 검색"):
            st.session_state["expand_radius"] = True
            st.rerun()
        return None

    bookable = [r for r in restaurants if r.is_bookable]
    not_bookable = [r for r in restaurants if not r.is_bookable]

    st.info(
        f"총 {len(restaurants)}개 식당 발견 "
        f"(네이버 예약 가능: {len(bookable)}개)"
    )

    # 예약 가능 식당 먼저 표시
    selected_restaurant = None

    if bookable:
        st.markdown("#### ✅ 네이버 예약 가능")
        for i, restaurant in enumerate(bookable, 1):
            if render_restaurant_card(restaurant, i):
                selected_restaurant = restaurant

    if not_bookable:
        with st.expander(f"📞 전화 예약 필요 ({len(not_bookable)}개)", expanded=False):
            for i, restaurant in enumerate(not_bookable, len(bookable) + 1):
                render_restaurant_card(restaurant, i)

    # 선택 확인 버튼
    if selected_restaurant:
        st.markdown("---")
        if st.button("✅ 선택한 식당으로 예약 진행", type="primary", use_container_width=True):
            return selected_restaurant

    return None
