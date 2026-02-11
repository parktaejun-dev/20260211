"""
부서점심 자동예약 (LunchBot)
============================

음식 종류, 날짜, 인원, 시간만 선택하면
광화문/시청/무교동 인근 맛집을 네이버 예약으로 자동 잡아주는 Streamlit 앱

실행: streamlit run app.py
"""

import subprocess
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st


# Playwright Chromium 자동 설치 (Streamlit Cloud 배포 대응)
@st.cache_resource
def _install_playwright_browser():
    """최초 1회만 Chromium을 설치합니다."""
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [sys.executable, "-m", "playwright", "install-deps", "chromium"],
        capture_output=True,
    )


try:
    _install_playwright_browser()
except Exception as e:
    st.error(f"Chromium 설치 실패: {e}")
    st.info("수동으로 터미널에서 `playwright install chromium`을 실행해주세요.")
    st.stop()

from playwright.sync_api import sync_playwright

from config.constants import (
    SESSION_KEY_STEP,
    SESSION_KEY_SEARCH_RESULTS,
    SESSION_KEY_SELECTED_RESTAURANT,
    SESSION_KEY_RESERVATION_RESULT,
    SESSION_KEY_LOGGED_IN,
    STEP_INPUT,
    STEP_SEARCH,
    STEP_RESERVE,
    STEP_RESULT,
    RESERVATION_STATUS_SUCCESS,
)
from core.auth import NaverAuth
from core.search import RestaurantSearcher
from core.reservation import NaverReservation
from core.notification import SlackNotifier
from ui.styles import CUSTOM_CSS
from ui.components import render_header, render_step_indicator
from ui.pages.home import render_input_form, render_login_sidebar
from ui.pages.search_results import render_search_results
from ui.pages.reservation import (
    render_reservation_progress,
    update_progress,
    render_reservation_complete,
)
from ui.pages.history import render_history_page, save_reservation


# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="부서점심 자동예약",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 적용
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── 세션 상태 초기화 ──────────────────────────────────────
def init_session_state():
    """세션 상태를 초기화합니다."""
    defaults = {
        SESSION_KEY_STEP: STEP_INPUT,
        SESSION_KEY_SEARCH_RESULTS: None,
        SESSION_KEY_SELECTED_RESTAURANT: None,
        SESSION_KEY_RESERVATION_RESULT: None,
        SESSION_KEY_LOGGED_IN: False,
        "show_history": False,
        "expand_radius": False,
        "input_data": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ── 사이드바: 로그인 정보 ────────────────────────────────
login_info = render_login_sidebar()


# ── 메인 영역 ────────────────────────────────────────────
render_header()

# 이력 보기 모드
if st.session_state.get("show_history"):
    render_history_page()
    if st.button("← 돌아가기"):
        st.session_state["show_history"] = False
        st.rerun()
    st.stop()

# 단계 표시
current_step = st.session_state[SESSION_KEY_STEP]
render_step_indicator(current_step)


# ── Step 1: 입력 ─────────────────────────────────────────
if current_step == STEP_INPUT:
    form_data = render_input_form()

    if form_data:
        # 로그인 정보 검증
        if not login_info["naver_id"] or not login_info["naver_pw"]:
            st.error("⚠️ 사이드바에서 네이버 로그인 정보를 입력해주세요.")
            st.stop()

        st.session_state["input_data"] = form_data
        st.session_state[SESSION_KEY_STEP] = STEP_SEARCH
        st.rerun()


# ── Step 2: 검색 ─────────────────────────────────────────
elif current_step == STEP_SEARCH:
    input_data = st.session_state.get("input_data")
    if not input_data:
        st.session_state[SESSION_KEY_STEP] = STEP_INPUT
        st.rerun()

    # 검색 실행 (캐시된 결과가 없을 때만)
    if st.session_state[SESSION_KEY_SEARCH_RESULTS] is None:
        with st.spinner("🔍 맛집을 검색하고 있습니다..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()

                    searcher = RestaurantSearcher()
                    radius = input_data["radius"]

                    if st.session_state.get("expand_radius"):
                        results, radius = searcher.search_with_expanded_radius(
                            page,
                            input_data["cuisine"],
                            input_data["cuisine_keyword"],
                            input_data["radius"],
                        )
                        st.session_state["expand_radius"] = False
                    else:
                        results = searcher.search(
                            page,
                            input_data["cuisine"],
                            input_data["cuisine_keyword"],
                            radius,
                        )

                    st.session_state[SESSION_KEY_SEARCH_RESULTS] = results
                    browser.close()

            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
                if st.button("🔄 다시 시도"):
                    st.rerun()
                st.stop()

    # 검색 결과 표시
    results = st.session_state[SESSION_KEY_SEARCH_RESULTS]
    selected = render_search_results(
        results, input_data["cuisine"], input_data["radius"]
    )

    if selected:
        st.session_state[SESSION_KEY_SELECTED_RESTAURANT] = selected
        st.session_state[SESSION_KEY_STEP] = STEP_RESERVE
        st.rerun()

    # 뒤로가기
    if st.button("← 입력으로 돌아가기"):
        st.session_state[SESSION_KEY_STEP] = STEP_INPUT
        st.session_state[SESSION_KEY_SEARCH_RESULTS] = None
        st.rerun()


# ── Step 3: 예약 ─────────────────────────────────────────
elif current_step == STEP_RESERVE:
    restaurant = st.session_state.get(SESSION_KEY_SELECTED_RESTAURANT)
    input_data = st.session_state.get("input_data")

    if not restaurant or not input_data:
        st.session_state[SESSION_KEY_STEP] = STEP_INPUT
        st.rerun()

    progress_bar, status_text = render_reservation_progress(restaurant)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            auth = NaverAuth()
            reserver = NaverReservation()

            # Step 1: 로그인
            update_progress(progress_bar, status_text, 1, "네이버 로그인 중...")

            # 저장된 쿠키로 먼저 시도
            cookie_loaded = auth.load_cookies(context)
            if not cookie_loaded:
                login_result = auth.login(
                    page, login_info["naver_id"], login_info["naver_pw"]
                )

                if not login_result.success:
                    if login_result.requires_captcha and login_result.captcha_screenshot:
                        st.error(login_result.message)
                        st.image(login_result.captcha_screenshot)
                        captcha_input = st.text_input("CAPTCHA 입력:")
                        if captcha_input:
                            page.fill("#captcha", captcha_input)
                            page.click(login_result.message)
                    elif login_result.requires_2fa:
                        st.warning(login_result.message)
                        otp_input = st.text_input("OTP 코드 입력:")
                        if otp_input:
                            page.fill(".otp_input", otp_input)
                    else:
                        st.error(login_result.message)
                        browser.close()
                        st.stop()

                # 로그인 성공 시 쿠키 저장
                auth.save_cookies(context)

            # Step 2-5: 예약 진행
            update_progress(progress_bar, status_text, 2, "예약 페이지로 이동 중...")

            update_progress(progress_bar, status_text, 3, "예약 정보 입력 중...")

            result = reserver.reserve(
                page,
                restaurant,
                input_data["date"],
                input_data["time"],
                input_data["party_size"],
                input_data.get("request_note", ""),
            )

            update_progress(progress_bar, status_text, 5, "결과 확인 중...")

            # 결과 저장
            save_reservation(result, input_data["cuisine"])
            st.session_state[SESSION_KEY_RESERVATION_RESULT] = result

            # Slack 알림 전송
            slack_url = login_info.get("slack_webhook")
            if slack_url and result.status == RESERVATION_STATUS_SUCCESS:
                notifier = SlackNotifier(slack_url)
                notifier.send_reservation_result(result)

            browser.close()

    except Exception as e:
        st.error(f"예약 진행 중 오류가 발생했습니다: {str(e)}")
        if st.button("🔄 다시 시도"):
            st.rerun()
        st.stop()

    st.session_state[SESSION_KEY_STEP] = STEP_RESULT
    st.rerun()


# ── Step 4: 결과 ─────────────────────────────────────────
elif current_step == STEP_RESULT:
    result = st.session_state.get(SESSION_KEY_RESERVATION_RESULT)
    if result:
        render_reservation_complete(result)
    else:
        st.warning("예약 결과를 찾을 수 없습니다.")
        if st.button("🔄 처음으로"):
            st.session_state[SESSION_KEY_STEP] = STEP_INPUT
            st.rerun()


# ── 하단 이력 탭 ─────────────────────────────────────────
st.markdown("---")
with st.expander("📜 예약 이력 보기"):
    render_history_page()
