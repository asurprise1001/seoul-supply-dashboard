import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="서울 자치구 공급자 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# 0. CSS 꾸미기
# -----------------------------
st.markdown("""
<style>
.main {
    background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
h1, h2, h3 {
    color: #1f2937;
}
.metric-card {
    background: white;
    padding: 18px 20px;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    border: 1px solid #eef2f7;
}
.top-card {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid #fed7aa;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}
.small-label {
    font-size: 0.9rem;
    color: #6b7280;
}
.big-number {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111827;
}
.section-title {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

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

# 보기 좋게 반올림
for col in ["수요지수", "공급지수", "위험지수", "미스매치점수"]:
    df[col] = df[col].round(3)

# 정렬용
df_mismatch = df.sort_values("미스매치점수", ascending=False)
df_facility_low = df.sort_values("영유아1000명당시설수", ascending=True).head(5)
df_risk_high = df.sort_values("보호구역1개당사고수", ascending=False).head(5)

# -----------------------------
# 4. 사이드바
# -----------------------------
st.sidebar.header("필터")
selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + sorted(df["자치구"].tolist()))

metric_option = st.sidebar.radio(
    "지도 색상 기준",
    ["미스매치점수", "위험지수", "영유아1000명당시설수"]
)

if selected_gu != "전체":
    filtered_df = df[df["자치구"] == selected_gu]
else:
    filtered_df = df.copy()

# -----------------------------
# 5. 제목
# -----------------------------
st.markdown("<h1>서울 자치구별 유아 동반 나들이 공급 현황 대시보드</h1>", unsafe_allow_html=True)
st.caption("영유아 인구, 방문 수요, 교통, 시설, 주차, 안전 데이터를 통합해 자치구별 공급 여건을 비교한 공급자 관점 대시보드")

# -----------------------------
# 6. KPI 카드
# -----------------------------
total_facilities = int(df["시설수"].sum())
avg_facility_per_1000 = round(df["영유아1000명당시설수"].mean(), 2)
vulnerable_count = int((df["공급취약여부"] == "취약").sum())
top_priority_gu = df_mismatch.iloc[0]["자치구"]

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="small-label">총 시설 수</div>
        <div class="big-number">{total_facilities:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="small-label">평균 영유아 1천명당 시설 수</div>
        <div class="big-number">{avg_facility_per_1000}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="small-label">공급 취약 자치구 수</div>
        <div class="big-number">{vulnerable_count}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="small-label">확충 우선 지역 1위</div>
        <div class="big-number">{top_priority_gu}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# -----------------------------
# 7. 확충 우선 지역 TOP 3
# -----------------------------
st.markdown('<div class="section-title">확충 우선 지역 TOP 3</div>', unsafe_allow_html=True)
top3_cols = st.columns(3)
top3 = df_mismatch.head(3)

for i, col in enumerate(top3_cols):
    row = top3.iloc[i]
    with col:
        st.markdown(f"""
        <div class="top-card">
            <div class="small-label">TOP {i+1}</div>
            <div class="big-number">{row['자치구']}</div>
            <div style="margin-top:8px; color:#374151;">
                미스매치점수: <b>{row['미스매치점수']:.2f}</b><br>
                영유아 1천명당 시설 수: <b>{row['영유아1000명당시설수']:.2f}</b><br>
                보호구역 1개당 사고수: <b>{row['보호구역1개당사고수']:.3f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# 8. 선택 자치구 요약
# -----------------------------
if selected_gu != "전체":
    row = filtered_df.iloc[0]
    st.info(
        f"선택 자치구: **{row['자치구']}** | "
        f"시설수 **{int(row['시설수'])}개**, "
        f"영유아 인구 **{int(row['영유아인구수']):,}명**, "
        f"평균통행속도 **{row['평균통행속도']:.2f}**, "
        f"미스매치점수 **{row['미스매치점수']:.2f}**"
    )

# -----------------------------
# 9. 지도 + 메인 차트
# -----------------------------
left, right = st.columns([1.15, 0.85])

with left:
    st.markdown('<div class="section-title">서울 자치구 지도</div>', unsafe_allow_html=True)

    geojson_url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"

    map_df = df.copy()

    fig_map = px.choropleth_mapbox(
        map_df,
        geojson=geojson_url,
        locations="자치구",
        featureidkey="properties.name",
        color=metric_option,
        color_continuous_scale="OrRd" if metric_option != "영유아1000명당시설수" else "Blues",
        hover_name="자치구",
        hover_data={
            "시설수": True,
            "영유아인구수": True,
            "일평균방문자수": True,
            "평균통행속도": True,
            "미스매치점수": True,
            "위험지수": True,
            metric_option: True
        },
        center={"lat": 37.565, "lon": 126.978},
        zoom=9.8,
        opacity=0.78
    )

    fig_map.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600,
        coloraxis_colorbar=dict(title=metric_option)
    )

    st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.markdown('<div class="section-title">미스매치 점수 상위 10개</div>', unsafe_allow_html=True)

    top10 = df_mismatch.head(10).sort_values("미스매치점수", ascending=True)

    fig_bar = px.bar(
        top10,
        x="미스매치점수",
        y="자치구",
        orientation="h",
        color="미스매치점수",
        color_continuous_scale="Sunsetdark",
        text="미스매치점수"
    )

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
        xaxis_title="미스매치점수",
        yaxis_title=""
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# 10. 수요 vs 공급 비교
# -----------------------------
st.markdown('<div class="section-title">자치구별 수요지수와 공급지수 비교</div>', unsafe_allow_html=True)

compare_df = df.sort_values("수요지수", ascending=False)

fig_compare = go.Figure()
fig_compare.add_trace(go.Bar(
    x=compare_df["자치구"],
    y=compare_df["수요지수"],
    name="수요지수"
))
fig_compare.add_trace(go.Bar(
    x=compare_df["자치구"],
    y=compare_df["공급지수"],
    name="공급지수"
))

fig_compare.update_layout(
    barmode="group",
    height=450,
    xaxis_tickangle=-45,
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", y=1.08, x=0.8)
)

st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# 11. 하위/상위 테이블
# -----------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.markdown('<div class="section-title">영유아 1천명당 시설 수 하위 5개</div>', unsafe_allow_html=True)
    st.dataframe(
        df_facility_low[["자치구", "영유아1000명당시설수", "시설수", "영유아인구수"]],
        use_container_width=True,
        hide_index=True
    )

with col_b:
    st.markdown('<div class="section-title">보호구역 1개당 사고 수 상위 5개</div>', unsafe_allow_html=True)
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