"""알림 모듈 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.notification import SlackNotifier


def test_slack_notifier_init():
    """SlackNotifier 인스턴스 생성 테스트."""
    notifier = SlackNotifier("https://hooks.slack.com/test")
    assert notifier.webhook_url == "https://hooks.slack.com/test"


def test_slack_notifier_empty_url():
    """빈 URL일 때 전송하지 않음."""
    notifier = SlackNotifier("")
    result = notifier.send_search_result(
        restaurant_name="테스트",
        address="서울",
        date_str="2026-02-16",
        time_str="12:00",
        party_size=10,
    )
    assert result is False
