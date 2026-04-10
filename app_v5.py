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
# CSS
# -----------------------------
st.markdown("""
<style>
.main {
    background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
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
.type-card-red {
    background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid #fecdd3;
}
.type-card-orange {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid #fdba74;
}
.type-card-blue {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid #93c5fd;
}
.comment-box {
    background: #f9fafb;
    padding: 16px 18px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    color: #374151;
    line-height: 1.7;
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
    margin-bottom: 0.6rem;
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 데이터
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_csv("dashboard_supply.csv")

df = load_data()

def min_max_scale(series):
    if series.max() == series.min():
        return pd.Series([0] * len(series), index=series.index)
    return (series - series.min()) / (series.max() - series.min())

# -----------------------------
# 지수 계산
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

# 정책 유형 분류
facility_low_threshold = df["영유아1000명당시설수"].quantile(0.3)
risk_high_threshold = df["보호구역1개당사고수"].quantile(0.7)
mismatch_high_threshold = df["미스매치점수"].quantile(0.7)

def classify_row(row):
    if row["미스매치점수"] >= mismatch_high_threshold and row["영유아1000명당시설수"] <= facility_low_threshold:
        return "공급 확충 우선형"
    elif row["보호구역1개당사고수"] >= risk_high_threshold:
        return "안전 보완형"
    else:
        return "상대 양호형"

df["정책유형"] = df.apply(classify_row, axis=1)

# 반올림
round_cols = [
    "일평균방문자수", "평균통행속도", "영유아1000명당시설수",
    "영유아1000명당주차장수", "보호구역1개당사고수",
    "수요지수", "공급지수", "위험지수", "미스매치점수"
]
for col in round_cols:
    if col in df.columns:
        df[col] = df[col].round(3)

# 정렬 데이터
df_mismatch = df.sort_values("미스매치점수", ascending=False)
df_top10 = df_mismatch.head(10).copy()
df_facility_low = df.sort_values("영유아1000명당시설수", ascending=True).head(5).copy()
df_risk_high = df.sort_values("보호구역1개당사고수", ascending=False).head(5).copy()

# -----------------------------
# 사이드바
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
# 헤더
# -----------------------------
st.markdown("<h1>서울 자치구별 유아 동반 나들이 공급 현황 대시보드</h1>", unsafe_allow_html=True)
st.caption("영유아 인구, 방문 수요, 교통, 시설, 주차, 안전 데이터를 통합해 자치구별 공급 여건을 비교한 공급자 관점 대시보드")

# -----------------------------
# KPI
# -----------------------------
total_facilities = int(df["시설수"].sum())
avg_facility_per_1000 = round(df["영유아1000명당시설수"].mean(), 2)
vulnerable_count = int((df["공급취약여부"] == "취약").sum())
top_priority_gu = df_mismatch.iloc[0]["자치구"]

c1, c2, c3, c4 = st.columns(4)
kpi_data = [
    ("총 시설 수", f"{total_facilities:,}"),
    ("평균 영유아 1천명당 시설 수", f"{avg_facility_per_1000}"),
    ("공급 취약 자치구 수", f"{vulnerable_count}"),
    ("확충 우선 지역 1위", top_priority_gu),
]
for col, (label, value) in zip([c1, c2, c3, c4], kpi_data):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="small-label">{label}</div>
            <div class="big-number">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# -----------------------------
# TOP 3
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
# 정책유형 카드
# -----------------------------
st.markdown('<div class="section-title">정책 유형별 주요 자치구</div>', unsafe_allow_html=True)

type1 = df[df["정책유형"] == "공급 확충 우선형"]["자치구"].tolist()[:5]
type2 = df[df["정책유형"] == "안전 보완형"]["자치구"].tolist()[:5]
type3 = df[df["정책유형"] == "상대 양호형"]["자치구"].tolist()[:5]

t1, t2, t3 = st.columns(3)

with t1:
    st.markdown(f"""
    <div class="type-card-red">
        <b>공급 확충 우선형</b><br><br>
        {'<br>'.join(type1) if type1 else '해당 없음'}
    </div>
    """, unsafe_allow_html=True)

with t2:
    st.markdown(f"""
    <div class="type-card-orange">
        <b>안전 보완형</b><br><br>
        {'<br>'.join(type2) if type2 else '해당 없음'}
    </div>
    """, unsafe_allow_html=True)

with t3:
    st.markdown(f"""
    <div class="type-card-blue">
        <b>상대 양호형</b><br><br>
        {'<br>'.join(type3) if type3 else '해당 없음'}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# 선택 자치구 요약
# -----------------------------
if selected_gu != "전체":
    row = filtered_df.iloc[0]
    st.info(
        f"선택 자치구: **{row['자치구']}** | "
        f"정책유형: **{row['정책유형']}** | "
        f"시설수 **{int(row['시설수'])}개**, "
        f"영유아 인구 **{int(row['영유아인구수']):,}명**, "
        f"영유아 1천명당 시설 수 **{row['영유아1000명당시설수']:.2f}**, "
        f"미스매치점수 **{row['미스매치점수']:.2f}**"
    )

# -----------------------------
# 지도 + 오른쪽 차트
# -----------------------------
left, right = st.columns([1.2, 0.8])

with left:
    st.markdown('<div class="section-title">서울 자치구 지도</div>', unsafe_allow_html=True)

    geojson_url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"

    color_scale = "OrRd"
    if metric_option == "영유아1000명당시설수":
        color_scale = "Blues"

    fig_map = px.choropleth_mapbox(
        df,
        geojson=geojson_url,
        locations="자치구",
        featureidkey="properties.name",
        color=metric_option,
        color_continuous_scale=color_scale,
        hover_name="자치구",
        hover_data={
            "시설수": True,
            "영유아인구수": True,
            "일평균방문자수": True,
            "평균통행속도": True,
            "미스매치점수": True,
            "위험지수": True,
            "정책유형": True,
            metric_option: True
        },
        center={"lat": 37.565, "lon": 126.978},
        zoom=9.8,
        opacity=0.82
    )

    fig_map.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=620,
        coloraxis_colorbar=dict(title=metric_option)
    )

    st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.markdown('<div class="section-title">공급취약 자치구 TOP 10 (미스매치 기준)</div>', unsafe_allow_html=True)

    bar_df = df_top10.sort_values("미스매치점수", ascending=True)

    fig_bar = px.bar(
        bar_df,
        x="미스매치점수",
        y="자치구",
        orientation="h",
        color="정책유형",
        text="미스매치점수",
        color_discrete_map={
            "공급 확충 우선형": "#ef4444",
            "안전 보완형": "#f59e0b",
            "상대 양호형": "#3b82f6"
        }
    )

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="미스매치점수",
        yaxis_title="",
        legend_title="정책유형"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# 수요/공급 비교 (Top 10만)
# -----------------------------
st.markdown('<div class="section-title">미스매치 상위 10개 자치구의 수요지수와 공급지수 비교</div>', unsafe_allow_html=True)

compare_df = df_top10.sort_values("미스매치점수", ascending=False)

fig_compare = go.Figure()
fig_compare.add_trace(go.Bar(
    x=compare_df["자치구"],
    y=compare_df["수요지수"],
    name="수요지수",
    marker_color="#2563eb"
))
fig_compare.add_trace(go.Bar(
    x=compare_df["자치구"],
    y=compare_df["공급지수"],
    name="공급지수",
    marker_color="#93c5fd"
))

fig_compare.update_layout(
    barmode="group",
    height=420,
    xaxis_tickangle=-25,
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", y=1.08, x=0.78)
)
st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# 하단 시각화 개선: dot plot + lollipop chart
# -----------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.markdown('<div class="section-title">영유아 1천명당 시설 수 하위 5개</div>', unsafe_allow_html=True)

    low_df = df_facility_low.sort_values("영유아1000명당시설수", ascending=True).copy()

    fig_low = go.Figure()

    # 기준선
    fig_low.add_vline(
        x=df["영유아1000명당시설수"].mean(),
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="전체 평균",
        annotation_position="top"
    )

    # 점 그래프
    fig_low.add_trace(go.Scatter(
        x=low_df["영유아1000명당시설수"],
        y=low_df["자치구"],
        mode="markers+text",
        marker=dict(
            size=18,
            color=low_df["영유아1000명당시설수"],
            colorscale="Blues",
            showscale=False,
            line=dict(color="white", width=1.5)
        ),
        text=[f"{v:.2f}" for v in low_df["영유아1000명당시설수"]],
        textposition="middle right",
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "영유아 1천명당 시설 수: %{x:.2f}<br>" +
            "<extra></extra>"
        )
    ))

    fig_low.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="영유아 1천명당 시설 수",
        yaxis_title="",
        plot_bgcolor="white"
    )

    st.plotly_chart(fig_low, use_container_width=True)

with col_b:
    st.markdown('<div class="section-title">보호구역 1개당 사고 수 상위 5개</div>', unsafe_allow_html=True)

    risk_df = df_risk_high.sort_values("보호구역1개당사고수", ascending=True).copy()

    fig_risk = go.Figure()

    # 전체 평균 기준선
    fig_risk.add_vline(
        x=df["보호구역1개당사고수"].mean(),
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="전체 평균",
        annotation_position="top"
    )

    # 로리팝 막대 줄기
    for _, row in risk_df.iterrows():
        fig_risk.add_shape(
            type="line",
            x0=0,
            x1=row["보호구역1개당사고수"],
            y0=row["자치구"],
            y1=row["자치구"],
            line=dict(color="#fca5a5", width=6)
        )

    # 끝 점
    fig_risk.add_trace(go.Scatter(
        x=risk_df["보호구역1개당사고수"],
        y=risk_df["자치구"],
        mode="markers+text",
        marker=dict(
            size=18,
            color=risk_df["보호구역1개당사고수"],
            colorscale="Reds",
            showscale=False,
            line=dict(color="white", width=1.5)
        ),
        text=[f"{v:.3f}" for v in risk_df["보호구역1개당사고수"]],
        textposition="middle right",
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "보호구역 1개당 사고 수: %{x:.3f}<br>" +
            "<extra></extra>"
        )
    ))

    fig_risk.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="보호구역 1개당 사고 수",
        yaxis_title="",
        plot_bgcolor="white"
    )

    st.plotly_chart(fig_risk, use_container_width=True)

# -----------------------------
# 자동 해석 문장
# -----------------------------
top3_names = ", ".join(df_mismatch.head(3)["자치구"].tolist())
risk_top3 = ", ".join(df_risk_high.head(3)["자치구"].tolist())
facility_low3 = ", ".join(df_facility_low.head(3)["자치구"].tolist())

st.markdown('<div class="section-title">요약 해석</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="comment-box">
1. 미스매치 점수 기준으로 볼 때 <b>{top3_names}</b>는 수요 대비 공급 압력이 높은 자치구로 나타났습니다.<br>
2. 안전 측면에서는 <b>{risk_top3}</b>가 보호구역 대비 사고 수가 높아 보완 우선 검토 대상입니다.<br>
3. 시설 공급 수준 측면에서는 <b>{facility_low3}</b>가 영유아 1천명당 시설 수가 낮아 상대적으로 취약한 편입니다.<br>
4. 따라서 본 대시보드는 자치구를 단순 순위화하는 데 그치지 않고, <b>공급 확충</b>, <b>안전 보완</b>, <b>상대 양호</b>의 정책 유형으로 구분해 해석할 수 있습니다.
</div>
""", unsafe_allow_html=True)

# -----------------------------
# 상세 데이터 간소화
# -----------------------------
with st.expander("자치구별 상세 데이터 보기"):
    cols_to_show = [
        "자치구", "정책유형", "시설수", "영유아인구수", "일평균방문자수",
        "평균통행속도", "영유아1000명당시설수", "보호구역1개당사고수",
        "수요지수", "공급지수", "위험지수", "미스매치점수"
    ]
    show_df = filtered_df[cols_to_show].copy() if selected_gu != "전체" else df[cols_to_show].copy()
    st.dataframe(show_df, use_container_width=True, hide_index=True)