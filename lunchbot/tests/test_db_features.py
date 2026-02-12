import pytest
import sqlite3
import pandas as pd
from core.db import DatabaseManager
from utils.parser import parse_uploaded_file

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    return db

def test_favorite_search(test_db):
    test_db.add_favorite("맛있는 국밥", "서울 중구", "존맛")
    test_db.add_favorite("파스타집", "서울 종로", "분위기")
    
    # Search by Name
    results = test_db.search_favorites("국밥")
    assert len(results) == 1
    assert results[0]["restaurant_name"] == "맛있는 국밥"
    
    # Search by Memo
    results = test_db.search_favorites("분위기")
    assert len(results) == 1
    assert results[0]["restaurant_name"] == "파스타집"
    
    # Search Fail
    results = test_db.search_favorites("없음")
    assert len(results) == 0

def test_import_favorites(test_db):
    data = [
        {"name": "Imported 1", "address": "Addr 1", "memo": "Memo 1"},
        {"name": "Imported 2", "address": "Addr 2", "memo": "Memo 2"},
    ]
    
    count = test_db.import_favorites(data)
    assert count == 2
    
    favs = test_db.get_favorites()
    assert len(favs) == 2
    assert favs[0]["restaurant_name"] == "Imported 2" # ORDER BY DESC
