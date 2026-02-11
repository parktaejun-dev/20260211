"""Streamlit UI 공통 컴포넌트"""

from pathlib import Path

import streamlit as st

from core.search import Restaurant

# 로고 절대 경로 (Streamlit Cloud 호환)
_APP_DIR = Path(__file__).resolve().parent.parent
_LOGO_PATH = _APP_DIR / "assets" / "kobaco_logo.png"


def render_header():
    """KOBACO 로고와 앱 헤더를 렌더링합니다."""
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        if _LOGO_PATH.exists():
            st.image(str(_LOGO_PATH), width=80)
    with col_title:
        st.markdown("## 부서점심 자동예약")
        st.caption("음식 종류 / 지역 / 예산 / 인원만 선택하면 맛집을 찾아드립니다!")


def render_restaurant_card(restaurant: Restaurant, index: int):
    """식당 정보를 카드 형태로 표시합니다."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{index}. {restaurant.name}**")

            if restaurant.category:
                st.caption(f"🏷️ {restaurant.category}")

            address = restaurant.road_address or restaurant.address
            if address:
                distance_info = ""
                if restaurant.walking_time:
                    distance_info = f" | {restaurant.distance_text} ({restaurant.walking_time})"
                st.caption(f"📍 {address}{distance_info}")

            if restaurant.phone:
                st.caption(f"📞 {restaurant.phone}")

            if restaurant.blog_reviews:
                st.caption("📝 블로그 리뷰")
                for review in restaurant.blog_reviews[:3]:
                    if review.link:
                        st.markdown(f"- [{review.title}]({review.link})")

        with col2:
            if restaurant.link:
                st.link_button("🔗 상세보기", restaurant.link, use_container_width=True)
            if restaurant.map_url:
                st.link_button("🗺️ 지도", restaurant.map_url, use_container_width=True)
