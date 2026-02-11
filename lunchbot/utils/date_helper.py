"""날짜 유틸리티"""

from datetime import date, timedelta


def get_next_monday(from_date: date | None = None) -> date:
    """다음 월요일 날짜를 반환. 오늘이 월요일이면 오늘 반환."""
    if from_date is None:
        from_date = date.today()

    days_ahead = 0 - from_date.weekday()  # 월요일 = 0
    if days_ahead <= 0:
        days_ahead += 7

    # 오늘이 월요일이면 오늘 반환
    if from_date.weekday() == 0:
        return from_date

    return from_date + timedelta(days=days_ahead)


def format_date_korean(d: date) -> str:
    """날짜를 한국어 형식으로 포맷. 예: '2026년 2월 16일 (월)'"""
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekdays[d.weekday()]
    return f"{d.year}년 {d.month}월 {d.day}일 ({weekday})"


def format_date_short(d: date) -> str:
    """짧은 형식. 예: '02/16 (월)'"""
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekdays[d.weekday()]
    return f"{d.month:02d}/{d.day:02d} ({weekday})"
