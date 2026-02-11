"""커스텀 CSS 스타일"""

CUSTOM_CSS = """
<style>
    /* 전체 앱 스타일 */
    .main .block-container {
        padding-top: 2rem;
        max-width: 800px;
    }

    /* 헤더 스타일 */
    .app-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 2rem;
    }

    /* 식당 카드 스타일 */
    .restaurant-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        background-color: #fafafa;
        transition: box-shadow 0.2s;
    }
    .restaurant-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* 예약 가능 뱃지 */
    .badge-bookable {
        background-color: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }

    /* 예약 불가 뱃지 */
    .badge-unavailable {
        background-color: #9e9e9e;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }

    /* 결과 카드 */
    .result-card {
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    .result-card.failed {
        border-color: #f44336;
    }

    /* 이력 테이블 */
    .history-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0f0f0;
    }

    /* 사이드바 스타일 */
    .sidebar .block-container {
        padding-top: 1rem;
    }

    /* 진행 상태 */
    .step-indicator {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .step-active {
        font-weight: bold;
        color: #1a73e8;
    }
    .step-inactive {
        color: #999;
    }
</style>
"""
