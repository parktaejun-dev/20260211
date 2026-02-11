"""Streamlit UI 공통 컴포넌트"""

import streamlit as st

from core.search import Restaurant
from core.reservation import ReservationResult
from config.constants import (
    RESERVATION_STATUS_SUCCESS,
    STEP_INPUT,
    STEP_SEARCH,
    STEP_RESERVE,
    STEP_RESULT,
)


def render_header():
    """앱 헤더를 렌더링합니다."""
    st.markdown(
        '<div class="app-header">'
        "<h1>부서점심 자동예약</h1>"
        "<p>음식 종류, 날짜, 인원, 시간만 선택하면 자동으로 예약!</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_step_indicator(current_step: str):
    """현재 단계를 표시합니다."""
    steps = [
        (STEP_INPUT, "입력"),
        (STEP_SEARCH, "검색"),
        (STEP_RESERVE, "예약"),
        (STEP_RESULT, "결과"),
    ]

    cols = st.columns(len(steps))
    for i, (step_key, step_name) in enumerate(steps):
        with cols[i]:
            if step_key == current_step:
                st.markdown(f"**:blue[{i+1}. {step_name}]**")
            else:
                st.markdown(f":gray[{i+1}. {step_name}]")


def render_restaurant_card(restaurant: Restaurant, index: int) -> bool:
    """식당 정보를 카드 형태로 표시하고 선택 체크박스를 반환합니다."""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            # 식당 이름 + 평점
            rating_stars = "⭐" * int(restaurant.rating) if restaurant.rating else ""
            st.markdown(f"**{index}. {restaurant.name}** {rating_stars}")

            if restaurant.rating:
                review_text = f"리뷰 {restaurant.review_count}" if restaurant.review_count else ""
                st.caption(f"평점 {restaurant.rating} {review_text}")

            if restaurant.address:
                distance_info = ""
                if restaurant.walking_time:
                    distance_info = f" | {restaurant.walking_time}"
                st.caption(f"📍 {restaurant.address}{distance_info}")

            if restaurant.price_range:
                st.caption(f"💰 {restaurant.price_range}")

        with col2:
            if restaurant.is_bookable:
                st.markdown(
                    '<span class="badge-bookable">네이버예약 가능</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="badge-unavailable">예약 불가</span>',
                    unsafe_allow_html=True,
                )

        selected = st.checkbox(
            "선택",
            key=f"restaurant_{index}",
            disabled=not restaurant.is_bookable,
        )
        st.divider()
        return selected


def render_reservation_result(result: ReservationResult):
    """예약 결과를 표시합니다."""
    if result.status == RESERVATION_STATUS_SUCCESS:
        st.success("예약 완료!")
        st.balloons()

        st.markdown("---")
        st.markdown(f"**🏪 {result.restaurant_name}**")
        st.markdown(f"📅 {result.reservation_date} {result.reservation_time}")
        st.markdown(f"👥 {result.party_size}명")

        if result.reservation_number:
            st.markdown(f"🔖 예약번호: `{result.reservation_number}`")

        if result.screenshot_path:
            st.markdown("---")
            try:
                st.image(result.screenshot_path, caption="예약 확인 스크린샷")
            except Exception:
                st.info(f"스크린샷 경로: {result.screenshot_path}")

    else:
        st.error(f"예약 실패: {result.message}")

        if result.alternative_times:
            st.info("**대안 시간:**")
            for t in result.alternative_times:
                st.write(f"  - {t}")

        if result.screenshot_path:
            try:
                st.image(result.screenshot_path, caption="예약 시도 스크린샷")
            except Exception:
                pass


def render_reservation_info_copy(result: ReservationResult):
    """예약 정보를 복사할 수 있는 텍스트로 표시합니다."""
    if result.status != RESERVATION_STATUS_SUCCESS:
        return

    info_text = (
        f"[부서점심 예약 안내]\n"
        f"🏪 식당: {result.restaurant_name}\n"
        f"📅 날짜: {result.reservation_date}\n"
        f"🕐 시간: {result.reservation_time}\n"
        f"👥 인원: {result.party_size}명\n"
    )
    if result.reservation_number:
        info_text += f"🔖 예약번호: {result.reservation_number}\n"

    st.text_area("📋 예약 정보 (복사용)", value=info_text, height=200)
