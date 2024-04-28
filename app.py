import os
import time
import pandas as pd
import streamlit as st


# 로컬 CSS 파일을 적용하는 함수 정의
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# CSS 파일 적용
local_css("style.css")

# 데이터 파일 경로
DATA_FILE = 'mk_place.csv'


# 데이터 불러오기 함수 정의
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except pd.errors.EmptyDataError:
            # 빈 데이터 파일인 경우 빈 데이터프레임 반환
            return pd.DataFrame(columns=['장소명', '링크', '태그'])
    else:
        # 데이터 파일이 없는 경우 빈 데이터프레임 반환
        return pd.DataFrame(columns=['장소명', '링크', '태그'])


# 데이터 저장 함수 정의
def save_data(data):
    data.to_csv(DATA_FILE, index=False)


# 세션 상태에서 데이터 로드
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# 모든 태그 추출
all_tags = list(
    set([tag.strip() for sublist in st.session_state.data['태그'].apply(lambda x: x.split(',')) for tag in sublist]))

# 데이터가 비어있지 않은 경우
if not st.session_state.data.empty:
    categories = all_tags
    selected_categories = st.session_state.get('selected_categories', set())

    # 카테고리 별 필터링 버튼 생성
    cols = st.columns(6)
    for idx, category in enumerate(categories):
        col = cols[idx % 6]
        button_label = f"✔ {category}" if category in selected_categories else category
        if col.button(button_label, key=f'button_{category}'):
            if category in selected_categories:
                selected_categories.remove(category)
            else:
                selected_categories.add(category)
            st.session_state['selected_categories'] = selected_categories
            st.rerun()

    # 선택된 카테고리가 있는 경우 데이터프레임 필터링
    if selected_categories:
        filtered_data = st.session_state.data[
            st.session_state.data['태그'].apply(lambda x: any(cat in x for cat in selected_categories))]
        st.dataframe(filtered_data)

# 장소 입력 폼 생성
with st.form("place_input", clear_on_submit=True):
    name = st.text_input("장소명을 입력해주세요.", key="name")
    link = st.text_input("장소에 해당하는 지도의 링크를 붙여넣어주세요.", key="link")
    selected_tags = st.multiselect("태그를 지정해주세요.", all_tags, key="categories")
    new_tag = st.text_input("새 태그를 추가하고 싶다면 여기에 입력해주세요.")
    submit_button = st.form_submit_button("추가하기")

# 장소 추가 버튼 클릭 시 데이터 추가
if submit_button and name and link and (selected_tags or new_tag):
    if new_tag:
        selected_tags.append(new_tag.strip())
        all_tags.append(new_tag.strip())
    new_data = pd.DataFrame({'장소명': [name], '링크': [link], '태그': [', '.join(selected_tags)]})
    st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
    save_data(st.session_state.data)
    st.success("추가 완료 !")

# 저장된 장소 출력
if not st.session_state.data.empty:
    st.write("저장된 모든 장소:")
    for i, row in st.session_state.data.iterrows():
        cols = st.columns([2, 1, 1, 1, 1, 2])
        cols[0].write(row['장소명'])
        cols[1].write(row['링크'])
        cols[2].write(row['태그'])

        edit_state_key = f"edit_state_{i}"

        # 수정 버튼 클릭 시 해당 행을 수정할 수 있는 폼 표시
        if cols[3].button("수정", key=f"edit_{i}"):
            st.session_state[edit_state_key] = {
                '장소명': row['장소명'],
                '링크': row['링크'],
                '태그': row['태그'].split(', '),
                'editing': True
            }

        if st.session_state.get(edit_state_key, {}).get('editing', False):
            edit_info = st.session_state[edit_state_key]
            new_name = st.text_input("장소명", value=edit_info['장소명'], key=f"new_name_{i}")
            new_link = st.text_input("링크", value=edit_info['링크'], key=f"new_link_{i}")
            new_tags = st.multiselect("태그 선택", all_tags, default=edit_info['태그'], key=f"new_tags_{i}")
            new_tag = st.text_input("새 태그를 추가하고 싶다면 여기에 입력해주세요.", key=f"new_tag_{i}")
            if new_tag:
                new_tags.append(new_tag.strip())
                all_tags.append(new_tag.strip())

            # 수정 내용 저장 버튼 클릭 시 데이터 업데이트
            if st.button("저장", key=f"save_{i}"):
                st.session_state.data.at[i, '장소명'] = new_name
                st.session_state.data.at[i, '링크'] = new_link
                st.session_state.data.at[i, '태그'] = ', '.join(new_tags)
                save_data(st.session_state.data)
                st.success("수정해드릴게요 !")
                st.session_state[edit_state_key]['editing'] = False
                time.sleep(0.8)
                st.rerun()

        # 삭제 버튼 클릭 시 해당 행 삭제
        if cols[4].button("삭제", key=f"delete_{i}"):
            st.session_state.data = st.session_state.data.drop(index=i)
            save_data(st.session_state.data)
            st.rerun()
else:
    st.write("데이터를 추가해주세요.")
