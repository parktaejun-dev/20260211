"""네이버 인증 모듈 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auth import NaverAuth, LoginResult


def test_login_result_dataclass():
    """LoginResult 데이터클래스 생성 테스트."""
    result = LoginResult(success=True, message="로그인 성공!")
    assert result.success is True
    assert result.message == "로그인 성공!"
    assert result.requires_captcha is False
    assert result.requires_2fa is False
    assert result.captcha_screenshot is None


def test_login_result_captcha():
    """CAPTCHA 필요 시 LoginResult 테스트."""
    result = LoginResult(
        success=False,
        message="CAPTCHA 필요",
        requires_captcha=True,
        captcha_screenshot="/path/to/captcha.png",
    )
    assert result.success is False
    assert result.requires_captcha is True
    assert result.captcha_screenshot == "/path/to/captcha.png"


def test_naver_auth_init():
    """NaverAuth 인스턴스 생성 테스트."""
    auth = NaverAuth()
    assert auth is not None


def test_load_cookies_missing_file():
    """쿠키 파일이 없을 때 load_cookies 테스트."""
    from unittest.mock import MagicMock

    auth = NaverAuth()
    mock_context = MagicMock()
    result = auth.load_cookies(mock_context, "/nonexistent/cookies.json")
    assert result is False
