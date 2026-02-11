"""예약 진행 페이지"""

import streamlit as st

from core.search import Restaurant
from core.reservation import ReservationResult
from ui.components import render_reservation_result, render_reservation_info_copy
from config.constants import RESERVATION_STATUS_SUCCESS


def render_reservation_progress(restaurant: Restaurant):
    """예약 진행 중 상태를 표시합니다."""
    st.subheader("🚀 예약 진행 중...")

    st.markdown(f"**{restaurant.name}** 예약을 진행하고 있습니다.")

    progress_bar = st.progress(0)
    status_text = st.empty()

    return progress_bar, status_text


def update_progress(progress_bar, status_text, step: int, message: str):
    """예약 진행 상태를 업데이트합니다."""
    steps = {
        1: ("네이버 로그인 중...", 0.2),
        2: ("예약 페이지 이동 중...", 0.4),
        3: ("예약 정보 입력 중...", 0.6),
        4: ("예약 확정 중...", 0.8),
        5: ("결과 확인 중...", 1.0),
    }

    if step in steps:
        default_msg, progress = steps[step]
        status_text.text(message or default_msg)
        progress_bar.progress(progress)


def render_reservation_complete(result: ReservationResult):
    """예약 완료 화면을 렌더링합니다."""
    st.subheader(
        "✅ 예약 결과" if result.status == RESERVATION_STATUS_SUCCESS else "❌ 예약 결과"
    )

    render_reservation_result(result)

    st.markdown("---")
    render_reservation_info_copy(result)

    # 액션 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 예약하기", use_container_width=True):
            # 세션 초기화
            for key in ["search_results", "selected_restaurant", "reservation_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["current_step"] = "input"
            st.rerun()
    with col2:
        if st.button("📜 예약 이력 보기", use_container_width=True):
            st.session_state["show_history"] = True
            st.rerun()
