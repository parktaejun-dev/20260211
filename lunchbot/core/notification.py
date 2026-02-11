"""알림 발송 모듈 (Slack Webhook)"""

import json

import httpx


class SlackNotifier:
    """Slack Webhook을 통한 검색 결과 알림."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_search_result(
        self,
        restaurant_name: str,
        address: str,
        date_str: str,
        time_str: str,
        party_size: int,
        phone: str = "",
    ) -> bool:
        """선택한 식당 정보를 Slack으로 전송합니다."""
        if not self.webhook_url:
            return False

        fields = [
            {"type": "mrkdwn", "text": f"*식당:*\n{restaurant_name}"},
            {"type": "mrkdwn", "text": f"*주소:*\n{address}"},
            {"type": "mrkdwn", "text": f"*날짜:*\n{date_str}"},
            {"type": "mrkdwn", "text": f"*시간:*\n{time_str}"},
            {"type": "mrkdwn", "text": f"*인원:*\n{party_size}명"},
        ]

        if phone:
            fields.append({"type": "mrkdwn", "text": f"*전화:*\n{phone}"})

        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "\U0001f37d\ufe0f 부서점심 식당 선택 완료",
                    },
                },
                {"type": "section", "fields": fields},
            ]
        }

        try:
            response = httpx.post(
                self.webhook_url,
                content=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False
