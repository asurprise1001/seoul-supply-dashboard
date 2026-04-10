import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 한글 깨짐 방지 (맥)
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
    if series.max() == series.min():
        return pd.Series([0] * len(series), index=series.index)
    return (series - series.min()) / (series.max() - series.min())

# -----------------------------
# 3. 지수 계산
# -----------------------------
df["교통혼잡지표"] = 1 - min_max_scale(df["평균통행속도"])

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
df["공급취약여부"] = np.where(df["미스매치점수"] > df["미스매치점수"].median(), "취약", "보통")

# 정렬용 데이터
df_mismatch = df.sort_values("미스매치점수", ascending=False)
df_facility_low = df.sort_values("영유아1000명당시설수", ascending=True).head(5)
df_risk_high = df.sort_values("보호구역1개당사고수", ascending=False).head(5)

# -----------------------------
# 4. 제목 / 설명
# -----------------------------
st.title("서울 자치구별 유아 동반 나들이 공급 현황 대시보드")
st.caption("영유아 인구, 방문 수요, 교통, 시설, 주차, 안전 데이터를 기반으로 자치구별 공급 여건을 비교한 공급자 관점 대시보드")

# -----------------------------
# 5. 사이드바
# -----------------------------
st.sidebar.header("필터")
selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + sorted(df["자치구"].tolist()))

if selected_gu != "전체":
    filtered_df = df[df["자치구"] == selected_gu]
else:
    filtered_df = df.copy()

# -----------------------------
# 6. KPI
# -----------------------------
total_facilities = int(df["시설수"].sum())
avg_facility_per_1000 = round(df["영유아1000명당시설수"].mean(), 2)
vulnerable_count = int((df["공급취약여부"] == "취약").sum())
top_priority_gu = df_mismatch.iloc[0]["자치구"]

k1, k2, k3, k4 = st.columns(4)
k1.metric("총 시설 수", f"{total_facilities:,}")
k2.metric("평균 영유아 1천명당 시설 수", f"{avg_facility_per_1000}")
k3.metric("공급 취약 자치구 수", f"{vulnerable_count}")
k4.metric("확충 우선 지역 1위", top_priority_gu)

st.markdown("---")

# -----------------------------
# 7. 선택 자치구 요약
# -----------------------------
if selected_gu != "전체":
    row = filtered_df.iloc[0]
    st.info(
        f"선택 자치구: **{row['자치구']}** | "
        f"시설수: **{int(row['시설수'])}개**, "
        f"영유아 인구: **{int(row['영유아인구수']):,}명**, "
        f"영유아 1천명당 시설 수: **{row['영유아1000명당시설수']:.2f}**, "
        f"미스매치 점수: **{row['미스매치점수']:.2f}**"
    )

# -----------------------------
# 8. 확충 우선 지역 TOP5
# -----------------------------
st.subheader("확충 우선 지역 TOP 5")
top5 = df_mismatch.head(5)[["자치구", "미스매치점수", "영유아1000명당시설수", "보호구역1개당사고수"]].copy()
top5.columns = ["자치구", "미스매치점수", "영유아1000명당시설수", "보호구역1개당사고수"]
st.dataframe(top5, use_container_width=True, hide_index=True)

# -----------------------------
# 9. 메인 차트 1: 미스매치 점수
# -----------------------------
st.subheader("자치구별 수요-공급 미스매치 점수")

fig1, ax1 = plt.subplots(figsize=(13, 5))
ax1.bar(df_mismatch["자치구"], df_mismatch["미스매치점수"])
ax1.axhline(df["미스매치점수"].median(), linestyle="--")
ax1.set_title("자치구별 미스매치 점수")
ax1.set_xlabel("자치구")
ax1.set_ylabel("미스매치 점수")
plt.xticks(rotation=45)
st.pyplot(fig1)

# -----------------------------
# 10. 메인 차트 2: 수요지수 vs 공급지수
# -----------------------------
st.subheader("자치구별 수요지수와 공급지수 비교")

compare_df = df.sort_values("수요지수", ascending=False)

fig2, ax2 = plt.subplots(figsize=(13, 5))
x = np.arange(len(compare_df))
width = 0.35

ax2.bar(x - width/2, compare_df["수요지수"], width, label="수요지수")
ax2.bar(x + width/2, compare_df["공급지수"], width, label="공급지수")

ax2.set_xticks(x)
ax2.set_xticklabels(compare_df["자치구"], rotation=45)
ax2.set_title("자치구별 수요지수 vs 공급지수")
ax2.set_ylabel("지수")
ax2.legend()
st.pyplot(fig2)

# -----------------------------
# 11. 보조 차트 / 랭킹
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("영유아 1천명당 시설 수 하위 5개")
    st.dataframe(
        df_facility_low[["자치구", "영유아1000명당시설수", "시설수", "영유아인구수"]],
        use_container_width=True,
        hide_index=True
    )

with right:
    st.subheader("보호구역 1개당 사고 수 상위 5개")
    st.dataframe(
        df_risk_high[["자치구", "보호구역1개당사고수", "어린이교통사고", "보호구역수"]],
        use_container_width=True,
        hide_index=True
    )

# -----------------------------
# 12. 상세 데이터
# -----------------------------
with st.expander("자치구별 상세 데이터 보기"):
    cols_to_show = [
        "자치구", "시설수", "영유아인구수", "일평균방문자수", "평균통행속도",
        "주차장수", "어린이교통사고", "보호구역수",
        "영유아1000명당시설수", "영유아1000명당주차장수", "보호구역1개당사고수",
        "수요지수", "공급지수", "위험지수", "미스매치점수", "공급취약여부"
    ]
    
    if selected_gu == "전체":
        st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered_df[cols_to_show], use_container_width=True, hide_index=True)