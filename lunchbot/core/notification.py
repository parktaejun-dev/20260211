"""알림 발송 모듈 (Slack Webhook)"""

import json

import httpx

from core.reservation import ReservationResult


class SlackNotifier:
    """Slack Webhook을 통한 예약 결과 알림."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_reservation_result(self, result: ReservationResult) -> bool:
        """예약 결과를 Slack으로 전송합니다."""
        if not self.webhook_url:
            return False

        emoji = "\u2705" if result.status == "success" else "\u274c"
        color = "#36a64f" if result.status == "success" else "#ff0000"

        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} 부서점심 예약 {'완료' if result.status == 'success' else '실패'}",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*식당:*\n{result.restaurant_name}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*날짜:*\n{result.reservation_date}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*시간:*\n{result.reservation_time}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*인원:*\n{result.party_size}명",
                                },
                            ],
                        },
                    ],
                }
            ]
        }

        if result.reservation_number:
            payload["attachments"][0]["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*예약번호:* `{result.reservation_number}`",
                    },
                }
            )

        if result.message:
            payload["attachments"][0]["blocks"].append(
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": result.message},
                    ],
                }
            )

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
