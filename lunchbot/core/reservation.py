"""네이버 예약 자동화

선택한 식당의 네이버 예약을 자동으로 진행합니다.
날짜/시간/인원 선택 → 예약 확정 → 결과 확인의 플로우를 자동화합니다.
"""

import time
from dataclasses import dataclass
from datetime import date

from playwright.sync_api import Page

from config.settings import MAX_RETRIES, RETRY_DELAY_SECONDS
from config.constants import (
    RESERVATION_STATUS_SUCCESS,
    RESERVATION_STATUS_FAILED,
    RESERVATION_STATUS_FULL,
    RESERVATION_STATUS_UNAVAILABLE,
)
from core.search import Restaurant
from utils.screenshot import generate_screenshot_path
from utils.date_helper import format_date_korean


@dataclass
class ReservationResult:
    """예약 결과 데이터."""

    status: str
    message: str
    restaurant_name: str = ""
    reservation_date: str = ""
    reservation_time: str = ""
    party_size: int = 0
    reservation_number: str = ""
    screenshot_path: str = ""
    alternative_times: list[str] | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "restaurant_name": self.restaurant_name,
            "reservation_date": self.reservation_date,
            "reservation_time": self.reservation_time,
            "party_size": self.party_size,
            "reservation_number": self.reservation_number,
            "screenshot_path": self.screenshot_path,
            "alternative_times": self.alternative_times,
        }


class NaverReservation:
    """네이버 예약 자동화 클래스."""

    def reserve(
        self,
        page: Page,
        restaurant: Restaurant,
        target_date: date,
        target_time: str,
        party_size: int,
        request_note: str = "",
    ) -> ReservationResult:
        """
        네이버 예약을 수행합니다.

        Args:
            page: Playwright Page (로그인 상태)
            restaurant: 예약할 식당 정보
            target_date: 예약 날짜
            target_time: 예약 시간 (예: "12:00")
            party_size: 인원수
            request_note: 요청사항 (선택)

        Returns:
            ReservationResult 객체
        """
        for attempt in range(MAX_RETRIES):
            try:
                result = self._attempt_reservation(
                    page, restaurant, target_date, target_time, party_size, request_note
                )
                if result.status == RESERVATION_STATUS_SUCCESS:
                    return result
                if result.status in (RESERVATION_STATUS_FULL, RESERVATION_STATUS_UNAVAILABLE):
                    return result  # 재시도 불필요
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
                    continue
                return ReservationResult(
                    status=RESERVATION_STATUS_FAILED,
                    message=f"예약 중 오류 발생 (재시도 {MAX_RETRIES}회 실패): {str(e)}",
                    restaurant_name=restaurant.name,
                )

        return ReservationResult(
            status=RESERVATION_STATUS_FAILED,
            message="예약에 실패했습니다. 다시 시도해주세요.",
            restaurant_name=restaurant.name,
        )

    def _attempt_reservation(
        self,
        page: Page,
        restaurant: Restaurant,
        target_date: date,
        target_time: str,
        party_size: int,
        request_note: str,
    ) -> ReservationResult:
        """단일 예약 시도를 수행합니다."""

        # 1. 예약 페이지 접근
        if restaurant.booking_url:
            page.goto(restaurant.booking_url, wait_until="networkidle", timeout=15000)
        elif restaurant.place_url:
            page.goto(restaurant.place_url, wait_until="networkidle", timeout=15000)
            # 예약 버튼 찾기 & 클릭
            booking_btn = page.query_selector(
                "a[href*='booking'], button:has-text('예약'), .reserve_btn"
            )
            if not booking_btn:
                return ReservationResult(
                    status=RESERVATION_STATUS_UNAVAILABLE,
                    message="예약 버튼을 찾을 수 없습니다.",
                    restaurant_name=restaurant.name,
                )
            booking_btn.click()
            page.wait_for_load_state("networkidle")
        else:
            return ReservationResult(
                status=RESERVATION_STATUS_UNAVAILABLE,
                message="예약 페이지 URL이 없습니다.",
                restaurant_name=restaurant.name,
            )

        time.sleep(2)

        # 2. 날짜 선택
        date_ok = self._select_date(page, target_date)
        if not date_ok:
            return ReservationResult(
                status=RESERVATION_STATUS_FULL,
                message=f"{format_date_korean(target_date)} 날짜를 선택할 수 없습니다.",
                restaurant_name=restaurant.name,
            )

        # 3. 시간 선택
        time_ok, alt_times = self._select_time(page, target_time)
        if not time_ok:
            return ReservationResult(
                status=RESERVATION_STATUS_FULL,
                message=f"{target_time} 시간이 만석입니다.",
                restaurant_name=restaurant.name,
                alternative_times=alt_times,
            )

        # 4. 인원수 설정
        self._set_party_size(page, party_size)

        # 5. 요청사항 입력
        if request_note:
            self._set_request_note(page, request_note)

        time.sleep(1)

        # 6. 예약 확정
        confirm_result = self._confirm_reservation(page)
        if not confirm_result:
            return ReservationResult(
                status=RESERVATION_STATUS_FAILED,
                message="예약 확정 버튼 클릭에 실패했습니다.",
                restaurant_name=restaurant.name,
            )

        # 7. 결과 확인 및 스크린샷
        time.sleep(3)
        return self._get_reservation_result(
            page, restaurant.name, target_date, target_time, party_size
        )

    def _select_date(self, page: Page, target_date: date) -> bool:
        """캘린더에서 날짜를 선택합니다."""
        try:
            # 날짜 포맷: YYYY-MM-DD 또는 YYYY.MM.DD
            date_str = target_date.strftime("%Y-%m-%d")
            day = target_date.day

            # 캘린더에서 해당 날짜 클릭 시도
            # 네이버 예약 캘린더의 일반적인 셀렉터들
            selectors = [
                f'td[data-date="{date_str}"]',
                f'button[data-date="{date_str}"]',
                f'a[data-date="{date_str}"]',
                f'.calendar td:has-text("{day}"):not(.disabled)',
                f'button:has-text("{day}"):not([disabled])',
            ]

            for selector in selectors:
                el = page.query_selector(selector)
                if el:
                    el.click()
                    time.sleep(1)
                    return True

            # 월 네비게이션이 필요한 경우
            # 현재 표시된 달과 목표 달 비교 후 이동
            return self._navigate_to_month_and_select(page, target_date)

        except Exception:
            return False

    def _navigate_to_month_and_select(self, page: Page, target_date: date) -> bool:
        """캘린더에서 월을 이동한 후 날짜를 선택합니다."""
        try:
            # 다음 달 버튼
            next_btn = page.query_selector(
                ".next, .btn_next, button:has-text('>')"
            )
            if next_btn:
                for _ in range(6):  # 최대 6개월 앞까지
                    next_btn.click()
                    time.sleep(0.5)

                    day_el = page.query_selector(
                        f'td:has-text("{target_date.day}"):not(.disabled)'
                    )
                    if day_el:
                        day_el.click()
                        time.sleep(1)
                        return True
        except Exception:
            pass
        return False

    def _select_time(self, page: Page, target_time: str) -> tuple[bool, list[str]]:
        """시간 슬롯을 선택합니다. 실패 시 대안 시간 목록을 반환합니다."""
        available_times = []

        try:
            # 시간 선택 영역에서 가용한 시간 슬롯 찾기
            time_slots = page.query_selector_all(
                ".time_slot:not(.disabled), .time_item:not(.sold_out), "
                "button[data-time]:not([disabled])"
            )

            for slot in time_slots:
                slot_text = slot.inner_text().strip()
                slot_time = slot.get_attribute("data-time") or slot_text

                if target_time in slot_text or target_time == slot_time:
                    slot.click()
                    time.sleep(1)
                    return True, []

                available_times.append(slot_text)

            # 직접 시간 텍스트로 검색
            time_el = page.query_selector(f'*:has-text("{target_time}"):not(.disabled)')
            if time_el:
                time_el.click()
                time.sleep(1)
                return True, []

        except Exception:
            pass

        return False, available_times

    def _set_party_size(self, page: Page, size: int) -> None:
        """인원수를 설정합니다."""
        try:
            # 인원수 입력 필드 찾기
            input_el = page.query_selector(
                'input[name*="party"], input[name*="guest"], '
                'input[name*="person"], input[type="number"]'
            )
            if input_el:
                input_el.fill(str(size))
                time.sleep(0.5)
                return

            # 증가/감소 버튼 방식
            # 현재 인원 확인
            count_el = page.query_selector(".count, .party_count, .num")
            if count_el:
                current = int(count_el.inner_text().strip())
                diff = size - current
                btn_selector = (
                    ".btn_plus, .increase, button:has-text('+')"
                    if diff > 0
                    else ".btn_minus, .decrease, button:has-text('-')"
                )
                btn = page.query_selector(btn_selector)
                if btn:
                    for _ in range(abs(diff)):
                        btn.click()
                        time.sleep(0.2)

            # select 방식
            select_el = page.query_selector(
                'select[name*="party"], select[name*="guest"]'
            )
            if select_el:
                select_el.select_option(value=str(size))

        except Exception:
            pass

    def _set_request_note(self, page: Page, note: str) -> None:
        """요청사항을 입력합니다."""
        try:
            textarea = page.query_selector(
                'textarea[name*="request"], textarea[name*="memo"], '
                'textarea[placeholder*="요청"]'
            )
            if textarea:
                textarea.fill(note)
        except Exception:
            pass

    def _confirm_reservation(self, page: Page) -> bool:
        """예약 확정 버튼을 클릭합니다."""
        try:
            confirm_selectors = [
                'button:has-text("예약하기")',
                'button:has-text("예약 확정")',
                'button:has-text("확인")',
                ".btn_confirm",
                ".btn_reserve",
                'input[type="submit"][value*="예약"]',
            ]

            for selector in confirm_selectors:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    time.sleep(2)
                    return True

        except Exception:
            pass
        return False

    def _get_reservation_result(
        self,
        page: Page,
        restaurant_name: str,
        target_date: date,
        target_time: str,
        party_size: int,
    ) -> ReservationResult:
        """예약 결과를 파싱하고 스크린샷을 저장합니다."""
        # 스크린샷 저장
        screenshot_path = generate_screenshot_path("reservation")
        page.screenshot(path=screenshot_path, full_page=True)

        # 예약 번호 파싱 시도
        reservation_number = ""
        try:
            # 일반적인 예약 번호 패턴 검색
            page_text = page.inner_text("body")
            import re

            patterns = [
                r"예약\s*번호\s*[:\s]*([A-Z0-9\-]+)",
                r"NV-\d{8}-\w+",
                r"reservation[_\s]*(?:no|number|id)\s*[:\s]*(\w+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    reservation_number = match.group(0) if not match.groups() else match.group(1)
                    break
        except Exception:
            pass

        # 성공 여부 판단
        success_indicators = ["예약이 완료", "예약 완료", "예약이 확정", "reservation confirmed"]
        page_text_lower = page.inner_text("body").lower() if page else ""
        is_success = any(ind in page_text_lower for ind in success_indicators)

        if is_success:
            return ReservationResult(
                status=RESERVATION_STATUS_SUCCESS,
                message="예약이 완료되었습니다!",
                restaurant_name=restaurant_name,
                reservation_date=format_date_korean(target_date),
                reservation_time=target_time,
                party_size=party_size,
                reservation_number=reservation_number,
                screenshot_path=screenshot_path,
            )

        return ReservationResult(
            status=RESERVATION_STATUS_FAILED,
            message="예약 완료를 확인할 수 없습니다. 스크린샷을 확인해주세요.",
            restaurant_name=restaurant_name,
            reservation_date=format_date_korean(target_date),
            reservation_time=target_time,
            party_size=party_size,
            screenshot_path=screenshot_path,
        )
