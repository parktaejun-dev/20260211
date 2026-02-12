"""DB 관리 페이지"""

import streamlit as st
import pandas as pd
from core.db import db
from utils.parser import parse_uploaded_file, parse_naver_map_url

def render_db_management_tab():
    """DB 관리 탭 (즐겨찾기/제외목록/데이터추가)"""
    st.header("🗄️ 데이터베이스 관리")

    tab1, tab2, tab3 = st.tabs(["⭐ 즐겨찾기", "🚫 제외 식당", "📤 데이터 추가"])

    with tab1:
        _render_favorites()

    with tab2:
        _render_exclusions()

    with tab3:
        _render_data_import()


def _render_favorites():
    st.subheader("즐겨찾기 목록")
    favorites = db.get_favorites()

    if not favorites:
        st.info("즐겨찾기한 식당이 없습니다.")
        return

    for item in favorites:
        name = item["restaurant_name"]
        address = item["address"] or ""
        memo = item["memo"] or ""
        
        with st.expander(f"⭐ {name}", expanded=False):
            if address:
                st.caption(f"📍 {address}")
            if item.get("category"):
                st.caption(f"📂 {item['category']}")
            if memo:
                 st.caption(f"📝 {memo}")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚫 제외", key=f"fav_to_ex_{item['id']}", use_container_width=True):
                    db.remove_favorite(name, address)
                    db.add_exclusion(name, address, "즐겨찾기에서 이동됨")
                    st.toast(f"🚫 {name} 제외 목록으로 이동")
                    st.rerun()

            with col_btn2:
                if st.button("삭제", key=f"del_fav_{item['id']}", use_container_width=True):
                    db.remove_favorite(name, address)
                    st.toast(f"🗑️ {name} 삭제 완료")
                    st.rerun()

def _render_exclusions():
    st.subheader("제외된 식당 목록")
    st.caption("이 목록에 있는 식당은 검색 결과에 나타나지 않습니다.")
    
    exclusions = db.get_exclusions()

    if not exclusions:
        st.info("제외된 식당이 없습니다.")
        return

    for item in exclusions:
        name = item["restaurant_name"]
        address = item["address"] or ""
        reason = item["reason"] or ""
        
        with st.expander(f"🚫 {name}", expanded=False):
             if address:
                st.caption(f"📍 {address}")
             if reason:
                 st.caption(f"📝 사유: {reason}")

             col_btn1, col_btn2 = st.columns(2)
             with col_btn1:
                if st.button("⭐ 즐겨찾기", key=f"ex_to_fav_{item['id']}", use_container_width=True):
                    db.remove_exclusion(name, address)
                    db.add_favorite(name, address, "제외 목록에서 복구됨")
                    st.toast(f"⭐ {name} 즐겨찾기로 이동")
                    st.rerun()

             with col_btn2:
                if st.button("해제", key=f"restore_ex_{item['id']}", use_container_width=True):
                    db.remove_exclusion(name, address)
                    st.toast(f"✅ {name} 제외 해제 완료")
                    st.rerun()

def _render_data_import():
    st.subheader("데이터 일괄 추가")
    st.info("즐겨찾기(Favorites)에 데이터를 추가합니다.")

    # 1. 파일 업로드
    st.markdown("### 📂 파일로 추가 (Excel/CSV)")
    st.caption("컬럼명: `name`(필수), `address`, `memo`, `category`")

    # 예제 파일 다운로드
    example_data = pd.DataFrame([{
        "name": "무교동미슐랭",
        "address": "서울 중구 무교로 123",
        "memo": "김치찌개 맛집",
        "category": "한식"
    }])
    csv_buffer = example_data.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 예제 파일 다운로드 (CSV)",
        data=csv_buffer,
        file_name="lunchbot_template.csv",
        mime="text/csv",
    )
    
    uploaded_file = st.file_uploader("파일 선택", type=["csv", "xlsx", "xls"])
    if uploaded_file:
        if st.button("파일 데이터 가져오기"):
            data = parse_uploaded_file(uploaded_file)
            if data:
                count = db.import_favorites(data)
                st.success(f"✅ {count}개 식당을 즐겨찾기에 추가했습니다.")
            else:
                st.error("데이터를 파싱할 수 없습니다. 컬럼명을 확인해주세요.")

    st.divider()

    # 2. URL 추가
    st.markdown("### 🔗 URL로 추가 (네이버 지도)")
    url = st.text_input("네이버 지도 공유 URL 붙여넣기", placeholder="https://naver.me/...")
    
    if url and st.button("URL 정보 가져오기"):
        # URL 파싱 시도
        info = parse_naver_map_url(url)
        if info:
            cat_str = f" ({info['category']})" if info.get('category') else ""
            st.success(f"식당을 찾았습니다: **{info['name']}**{cat_str}")
            if db.add_favorite(info["name"], info["address"], category=info.get("category", "")):
                st.toast(f"✅ {info['name']} 추가 완료!")
            else:
                st.warning("이미 즐겨찾기에 있는 식당입니다.")
        else:
            st.error("URL에서 정보를 가져오지 못했습니다. 직접 입력해주세요.")

