
import pytest
from unittest.mock import MagicMock, patch
from core.search import RestaurantSearcher

def test_search_splits_keywords():
    """검색어가 공백으로 구분된 경우 분리해서 호출하는지 테스트"""
    # given
    searcher = RestaurantSearcher("id", "secret")
    
    # _search_single_area를 모의 객체로 대체
    searcher._search_single_area = MagicMock(return_value=[])
    
    # SEARCH_AREAS를 1개로 제한하여 테스트 단순화
    with patch("core.search.SEARCH_AREAS", ["테스트지역"]):
        # when
        searcher.search(
            area_name="무시됨", 
            cuisine_keyword="양식 파스타", 
            budget_keyword="저렴한"
        )
        
    # then
    # "양식", "파스타" 각각에 대해 "테스트지역"에서 호출되어야 함
    # API 호출 횟수 = 지역(1) * 키워드(2) = 2회
    assert searcher._search_single_area.call_count == 2
    
    # 호출 인자 확인
    calls = searcher._search_single_area.call_args_list
    
    # 순서는 보장되지 않을 수 있으므로 집합으로 비교하거나 각각 확인
    args_list = [c.args for c in calls]
    
    assert ("테스트지역", "양식", "저렴한") in args_list
    assert ("테스트지역", "파스타", "저렴한") in args_list
