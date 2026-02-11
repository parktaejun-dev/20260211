"""네이버 로그인 자동화

네이버 보안 키패드 우회를 위해 JavaScript injection 방식으로 ID/PW를 입력합니다.
CAPTCHA 또는 2차 인증 발생 시 사용자에게 수동 처리를 요청합니다.
"""

import time
from dataclasses import dataclass

from playwright.sync_api import Page, BrowserContext

from config.settings import NAVER_LOGIN_URL
from config.constants import SELECTORS
from utils.screenshot import generate_screenshot_path


@dataclass
class LoginResult:
    success: bool
    message: str
    requires_captcha: bool = False
    requires_2fa: bool = False
    captcha_screenshot: str | None = None


class NaverAuth:
    """네이버 로그인 처리 클래스."""

    def login(self, page: Page, naver_id: str, naver_pw: str) -> LoginResult:
        """
        네이버 로그인을 수행합니다.

        Args:
            page: Playwright Page 객체
            naver_id: 네이버 ID
            naver_pw: 네이버 비밀번호

        Returns:
            LoginResult 객체
        """
        try:
            # 1. 로그인 페이지 접속
            page.goto(NAVER_LOGIN_URL, wait_until="networkidle")
            time.sleep(1)

            # 2. JavaScript injection으로 ID/PW 입력
            # 네이버는 직접 타이핑을 차단하므로 JS로 값 설정 후 이벤트 발생
            self._inject_credentials(page, naver_id, naver_pw)
            time.sleep(0.5)

            # 3. 로그인 버튼 클릭
            page.click(SELECTORS["login_button"])
            time.sleep(2)

            # 4. 결과 확인
            return self._check_login_result(page)

        except Exception as e:
            return LoginResult(success=False, message=f"로그인 중 오류 발생: {str(e)}")

    def _inject_credentials(self, page: Page, naver_id: str, naver_pw: str) -> None:
        """JavaScript를 사용하여 로그인 폼에 자격 증명을 입력합니다."""
        # ID 입력 필드에 값 설정
        page.evaluate(
            """(id) => {
                const el = document.querySelector('#id');
                if (el) {
                    el.focus();
                    el.value = id;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""",
            naver_id,
        )
        time.sleep(0.3)

        # PW 입력 필드에 값 설정
        page.evaluate(
            """(pw) => {
                const el = document.querySelector('#pw');
                if (el) {
                    el.focus();
                    el.value = pw;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""",
            naver_pw,
        )

    def _check_login_result(self, page: Page) -> LoginResult:
        """로그인 결과를 확인합니다."""
        current_url = page.url

        # CAPTCHA 확인
        if "captcha" in current_url.lower() or page.query_selector(".captcha"):
            screenshot_path = generate_screenshot_path("captcha")
            page.screenshot(path=screenshot_path)
            return LoginResult(
                success=False,
                message="CAPTCHA 인증이 필요합니다. 아래 이미지를 확인해주세요.",
                requires_captcha=True,
                captcha_screenshot=screenshot_path,
            )

        # 2차 인증 확인
        if "2step" in current_url or page.query_selector(".otp_input"):
            return LoginResult(
                success=False,
                message="2차 인증(OTP)이 필요합니다.",
                requires_2fa=True,
            )

        # 에러 메시지 확인
        error_el = page.query_selector(SELECTORS["login_error"])
        if error_el:
            error_text = error_el.inner_text()
            return LoginResult(
                success=False,
                message=f"로그인 실패: {error_text}",
            )

        # 로그인 성공 확인 (메인 페이지로 이동했는지)
        if "nid.naver.com" not in current_url:
            return LoginResult(success=True, message="로그인 성공!")

        return LoginResult(
            success=False,
            message="로그인 상태를 확인할 수 없습니다. 다시 시도해주세요.",
        )

    def check_login_status(self, page: Page) -> bool:
        """현재 페이지에서 네이버 로그인 상태를 확인합니다."""
        try:
            page.goto("https://www.naver.com", wait_until="networkidle")
            # 로그인 상태면 로그아웃 버튼이 존재
            logout_btn = page.query_selector("a[href*='nidlogin.logout']")
            return logout_btn is not None
        except Exception:
            return False

    def save_cookies(self, context: BrowserContext, path: str = "data/cookies.json") -> None:
        """브라우저 쿠키를 파일로 저장합니다."""
        import json
        from pathlib import Path

        cookies = context.cookies()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(cookies, f)

    def load_cookies(self, context: BrowserContext, path: str = "data/cookies.json") -> bool:
        """저장된 쿠키를 브라우저에 로드합니다."""
        import json
        from pathlib import Path

        cookie_file = Path(path)
        if not cookie_file.exists():
            return False

        try:
            with open(path) as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            return True
        except (json.JSONDecodeError, Exception):
            return False
