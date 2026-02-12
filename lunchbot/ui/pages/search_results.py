"""검색 결과 페이지"""

import streamlit as st

from bot_core.search import Restaurant
from ui.components import render_restaurant_card
from bot_utils.date_helper import format_date_korean


def render_search_results(
    restaurants: list[Restaurant],
    input_data: dict,
) -> Restaurant | None:
    """
    검색 결과를 표시하고 사용자가 선택한 식당을 반환합니다.
    """
    cuisine = input_data["cuisine"]
    radius = input_data["radius"]
    radius_text = f"{radius}m" if radius < 1000 else f"{radius / 1000:.0f}km"
    budget = input_data.get("budget", "상관없음")
    party = input_data["party_size"]
    date_str = format_date_korean(input_data["date"])
    time_str = input_data["time"]

    st.subheader(f"🔍 검색 결과")
    st.caption(
        f"🍽️ {cuisine} · 💰 {budget} · 👥 {party}명 · "
        f"📅 {date_str} {time_str} · 📍 반경 {radius_text}"
    )

    if not restaurants:
        st.warning("검색 결과가 없습니다. 반경을 넓히거나 다른 조건을 선택해보세요.")
        if st.button("🔄 다시 검색하기"):
            st.session_state["search_results"] = None
            if "random_picks" in st.session_state:
                del st.session_state["random_picks"]
            st.rerun()
        return None

    st.info(f"총 {len(restaurants)}개 식당을 찾았습니다.")

    # ── 랜덤 추천 버튼 ──────────────────────────────────
    if st.button("🎲 보기가 너무 많아요! 랜덤으로 3개만 보여주세요"):
        import random
        if len(restaurants) > 3:
            st.session_state["random_picks"] = random.sample(restaurants, 3)
            st.rerun()
        else:
            st.toast("식당이 3개 이하라서 랜덤 추천이 불필요합니다.", icon="😅")

    # 랜덤 추천 상태가 있으면 그 목록만 사용, 아니면 전체 사용
    display_restaurants = st.session_state.get("random_picks", restaurants)
    
    # 만약 원본 검색결과가 바뀌었거나(재검색 등) 리셋이 필요하면 체크해야 하지만, 
    # 여기서는 "다시 검색하기" 버튼이 state를 날리므로 괜찮음.
    # 다만 '전체 보기' 버튼도 있으면 좋음.
    if "random_picks" in st.session_state:
        st.success(f"🎲 랜덤으로 뽑은 {len(display_restaurants)}개 식당입니다.")
        if st.button("🔄 전체 목록 다시 보기"):
             del st.session_state["random_picks"]
             st.rerun()
    # ──────────────────────────────────────────────────

    # 식당 목록 표시
    selected_idx = None
    for i, restaurant in enumerate(display_restaurants, 1):
        render_restaurant_card(restaurant, i)

    # 식당 선택
    st.markdown("---")
    restaurant_names = [f"{i}. {r.name}" for i, r in enumerate(display_restaurants, 1)]
    chosen = st.selectbox("✅ 예약할 식당을 선택하세요", options=restaurant_names)

    if chosen:
        selected_idx = int(chosen.split(".")[0]) - 1
        selected = display_restaurants[selected_idx]

        # 선택한 식당 정보 요약
        date_str = format_date_korean(input_data["date"])
        time_str = input_data["time"]
        party = input_data["party_size"]

        st.success(
            f"**{selected.name}** | {date_str} {time_str} | {party}명"
        )

        # ── DB 액션 버튼 (즐겨찾기 / 제외) ────────────────
        from bot_core.db import db

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
                    if "random_picks" in st.session_state:
                        # 랜덤 추천 중 제외했으면 갱신 필요하지만 복잡해지므로 일단 리셋
                        del st.session_state["random_picks"]
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

        st.caption("📋 공유용 텍스트 (우측 상단 복사 버튼 사용)")
        st.code(info_text, language="text")

        if selected.link:
            st.link_button(
                "🔗 네이버에서 예약/상세보기",
                selected.link,
                type="primary",
                use_container_width=True,
            )

        return selected

    return None
