"""Streamlit UI 공통 컴포넌트"""

from pathlib import Path

import streamlit as st

from bot_core.search import Restaurant

# 로고 절대 경로 (Streamlit Cloud 호환)
_APP_DIR = Path(__file__).resolve().parent.parent
_LOGO_PATH = _APP_DIR / "assets" / "kobaco_logo.png"


import base64

def render_header():
    """KOBACO 로고와 앱 헤더를 렌더링합니다."""
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        if _LOGO_PATH.exists():
            # 이미지를 Base64로 인코딩하여 클릭 가능한 HTML 링크로 렌더링
            with open(_LOGO_PATH, "rb") as f:
                img_data = f.read()
                img_b64 = base64.b64encode(img_data).decode()
            
            # target="_self"로 현재 탭에서 리로드 (홈으로 이동 효과)
            st.markdown(
                f'<a href="/" target="_self"><img src="data:image/png;base64,{img_b64}" width="80"></a>',
                unsafe_allow_html=True
            )
    with col_title:
        st.markdown("## 무교동미슐랭")
        st.caption("여러분의 즐겨찾기 추가와, 제외로 좀 더 나은 결과가 나올 것입니다.")


def render_restaurant_card(restaurant: Restaurant, index: int):
    """식당 정보를 카드 형태로 표시합니다."""
    with st.container(border=True):
        col1, col2 = st.columns([2.5, 1.5])

        with col1:
            st.markdown(f"**{index}. {restaurant.name}**")

            if restaurant.category:
                st.caption(f"🏷️ {restaurant.category}")

            address = restaurant.road_address or restaurant.address
            if address:
                distance_info = ""
                if restaurant.walking_time:
                    distance_info = f" | {restaurant.distance_text} ({restaurant.walking_time})"
                elif restaurant.distance_text:
                    distance_info = f" | {restaurant.distance_text}"
                st.caption(f"📍 {address}{distance_info}")

            if restaurant.price:
                st.caption(f"💰 예상 가격: {restaurant.price}")

            if restaurant.phone:
                st.caption(f"📞 {restaurant.phone}")

            if restaurant.blog_reviews:
                st.caption("📝 블로그 리뷰")
                for review in restaurant.blog_reviews[:3]:
                    if review.link:
                        st.markdown(f"- [{review.title}]({review.link})")

        with col2:
            # 1. 네이버 지도 버튼 (항상 표시)
            # API에서 준 링크가 네이버 지도라면 그걸 사용, 아니면 검색어 기반 링크 사용
            map_target_url = restaurant.map_url
            homepage_url = ""
            
            if restaurant.link:
                if "naver.com" in restaurant.link:
                    # API 링크가 네이버 지도 관련이면, 더 정확한 이 링크를 지도 버튼에 사용
                    map_target_url = restaurant.link
                else:
                    # API 링크가 외부 사이트(인스타 등)면 홈페이지 버튼용설정
                    homepage_url = restaurant.link
            
            st.link_button("🗺️ 네이버 지도", map_target_url, use_container_width=True)
            
            # 2. 홈페이지 버튼 (별도 표시)
            if homepage_url:
                st.link_button("🏠 홈페이지", homepage_url, use_container_width=True)
            
            from bot_core.db import db
            address_for_db = restaurant.road_address or restaurant.address
            
            # 2. 즐겨찾기 버튼
            if db.is_favorite(restaurant.name, address_for_db):
                st.button("⭐ 저장됨", disabled=True, key=f"fav_disabled_{index}", use_container_width=True)
            else:
                if st.button("⭐ 즐겨찾기", key=f"add_fav_{index}", use_container_width=True):
                    db.add_favorite(restaurant.name, address_for_db, restaurant.category)
                    st.toast(f"⭐ {restaurant.name} 즐겨찾기 추가 완료!")
                    st.rerun()

            # 3. 제외 버튼
            if st.button("🚫 영구 제외", key=f"exclude_{index}", use_container_width=True):
                db.add_exclusion(restaurant.name, address_for_db, "검색 결과에서 제외됨")
                if "search_results" in st.session_state and st.session_state["search_results"]:
                    st.session_state["search_results"] = [
                        r for r in st.session_state["search_results"] 
                        if not (r.name == restaurant.name and (r.road_address or r.address) == address_for_db)
                    ]
                st.toast(f"🚫 {restaurant.name} 제외 처리되었습니다.")
                st.rerun()
