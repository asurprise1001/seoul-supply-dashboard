import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False
st.set_page_config(page_title="서울 자치구 공급자 대시보드", layout="wide")

# -----------------------------
# 1. 데이터 불러오기
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_supply.csv")
    return df

df = load_data()

# -----------------------------
# 2. 표준화 함수
# -----------------------------
def min_max_scale(series):
    return (series - series.min()) / (series.max() - series.min())

# -----------------------------
# 3. 지수 계산
# -----------------------------
df["교통혼잡지표"] = 1 - min_max_scale(df["평균통행속도"])  # 속도 낮을수록 혼잡 높음

df["수요지수"] = (
    min_max_scale(df["영유아인구수"]) +
    min_max_scale(df["일평균방문자수"]) +
    df["교통혼잡지표"]
)

df["공급지수"] = (
    min_max_scale(df["시설수"]) +
    min_max_scale(df["주차장수"]) +
    min_max_scale(df["보호구역수"])
)

df["위험지수"] = (
    min_max_scale(df["어린이교통사고"]) +
    min_max_scale(df["보호구역1개당사고수"])
)

df["미스매치점수"] = df["수요지수"] - df["공급지수"]

# 공급 취약 지역 플래그
df["공급취약여부"] = np.where(df["미스매치점수"] > df["미스매치점수"].median(), "취약", "보통")

# -----------------------------
# 4. 제목
# -----------------------------
st.title("서울 자치구별 유아 동반 나들이 공급 현황 대시보드")
st.markdown("영유아 인구, 방문 수요, 교통, 시설, 주차, 안전 데이터를 기반으로 자치구별 공급 현황을 비교합니다.")

# -----------------------------
# 5. 사이드바 필터
# -----------------------------
st.sidebar.header("필터")
selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + sorted(df["자치구"].tolist()))

if selected_gu != "전체":
    filtered_df = df[df["자치구"] == selected_gu]
else:
    filtered_df = df.copy()

# -----------------------------
# 6. KPI 카드
# -----------------------------
total_facilities = int(df["시설수"].sum())
avg_facility_per_1000 = round(df["영유아1000명당시설수"].mean(), 2)
vulnerable_count = int((df["공급취약여부"] == "취약").sum())
top_risk_gu = df.sort_values("위험지수", ascending=False).iloc[0]["자치구"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("총 시설 수", f"{total_facilities:,}")
col2.metric("평균 영유아 1천명당 시설 수", f"{avg_facility_per_1000}")
col3.metric("공급 취약 자치구 수", f"{vulnerable_count}")
col4.metric("위험지수 상위 자치구", top_risk_gu)

st.markdown("---")

# -----------------------------
# 7. 자치구별 미스매치 점수
# -----------------------------
st.subheader("자치구별 수요-공급 미스매치 점수")

plot_df = df.sort_values("미스매치점수", ascending=False)

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(plot_df["자치구"], plot_df["미스매치점수"])
ax.set_title("자치구별 미스매치 점수")
ax.set_xlabel("자치구")
ax.set_ylabel("미스매치 점수 (수요지수 - 공급지수)")
plt.xticks(rotation=45)
st.pyplot(fig)

# -----------------------------
# 8. 수요지수 vs 공급지수 비교
# -----------------------------
st.subheader("자치구별 수요지수 vs 공급지수 비교")

compare_df = df.sort_values("수요지수", ascending=False)

fig, ax = plt.subplots(figsize=(12, 5))
x = np.arange(len(compare_df))
width = 0.35

ax.bar(x - width/2, compare_df["수요지수"], width, label="수요지수")
ax.bar(x + width/2, compare_df["공급지수"], width, label="공급지수")

ax.set_xticks(x)
ax.set_xticklabels(compare_df["자치구"], rotation=45)
ax.set_title("수요지수와 공급지수 비교")
ax.legend()
st.pyplot(fig)

# -----------------------------
# 9. 보조지표 랭킹
# -----------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("영유아 1천명당 시설 수 상/하위")
    rank_facility = df.sort_values("영유아1000명당시설수", ascending=False)[["자치구", "영유아1000명당시설수"]]
    st.dataframe(rank_facility, use_container_width=True)

with col_right:
    st.subheader("보호구역 1개당 사고수 상위")
    rank_risk = df.sort_values("보호구역1개당사고수", ascending=False)[["자치구", "보호구역1개당사고수"]]
    st.dataframe(rank_risk, use_container_width=True)

# -----------------------------
# 10. 선택 자치구 상세 보기
# -----------------------------
st.subheader("선택 자치구 상세 정보")

if selected_gu == "전체":
    st.dataframe(
        df[[
            "자치구", "시설수", "영유아인구수", "일평균방문자수", "평균통행속도",
            "주차장수", "어린이교통사고", "보호구역수",
            "영유아1000명당시설수", "영유아1000명당주차장수", "보호구역1개당사고수",
            "수요지수", "공급지수", "위험지수", "미스매치점수", "공급취약여부"
        ]],
        use_container_width=True
    )
else:
    st.dataframe(
        filtered_df[[
            "자치구", "시설수", "영유아인구수", "일평균방문자수", "평균통행속도",
            "주차장수", "어린이교통사고", "보호구역수",
            "영유아1000명당시설수", "영유아1000명당주차장수", "보호구역1개당사고수",
            "수요지수", "공급지수", "위험지수", "미스매치점수", "공급취약여부"
        ]],
        use_container_width=True
    )