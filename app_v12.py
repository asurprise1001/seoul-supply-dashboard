import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="서울시 자치구별 유아 친화 지표",
    page_icon="👶",
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
    padding-top: 1.6rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}
h1, h2, h3 {
    color: #1f2937;
}
.metric-card {
    background: white;
    padding: 14px 16px;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border: 1px solid #eef2f7;
    min-height: 110px;
}
.top-card {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid #fed7aa;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    min-height: 120px;
}
.type-card-red {
    background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid #fecdd3;
    min-height: 120px;
}
.type-card-orange {
    background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid #fdba74;
    min-height: 120px;
}
.type-card-blue {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid #93c5fd;
    min-height: 120px;
}
.action-card-yellow {
    background: linear-gradient(135deg, #fffaf0 0%, #fef3c7 100%);
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid #fcd34d;
    min-height: 150px;
}
.action-card-red {
    background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid #fda4af;
    min-height: 150px;
}
.action-card-blue {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid #93c5fd;
    min-height: 150px;
}
.comment-box {
    background: #f9fafb;
    padding: 14px 16px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    color: #374151;
    line-height: 1.7;
}
.small-label {
    font-size: 0.88rem;
    color: #6b7280;
}
.big-number {
    font-size: 1.85rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.15;
}
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
    color: #111827;
}
.info-note {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 10px 14px;
    color: #475569;
    font-size: 0.93rem;
}
.selected-summary {
    background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
    border: 1px solid #dbeafe;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}
.filter-summary {
    background: linear-gradient(135deg, #ffffff 0%, #fffaf5 100%);
    border: 1px solid #fde68a;
    border-radius: 16px;
    padding: 12px 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}
.badge-red {
    display: inline-block;
    background: #fee2e2;
    color: #991b1b;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.badge-orange {
    display: inline-block;
    background: #ffedd5;
    color: #9a3412;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.badge-blue {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.type-count {
    font-size: 1.45rem;
    font-weight: 700;
    color: #111827;
    margin-top: 6px;
}
.type-list {
    color: #374151;
    margin-top: 8px;
    line-height: 1.55;
    font-size: 0.93rem;
}
.tight-space {
    margin-top: 0.2rem;
    margin-bottom: 0.5rem;
}
.action-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #111827;
}
.action-list {
    margin-top: 8px;
    color: #374151;
    line-height: 1.65;
    font-size: 0.93rem;
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

round_cols = [
    "일평균방문자수", "평균통행속도", "영유아1000명당시설수",
    "영유아1000명당주차장수", "보호구역1개당사고수",
    "수요지수", "공급지수", "위험지수", "미스매치점수"
]
for col in round_cols:
    if col in df.columns:
        df[col] = df[col].round(3)

df_mismatch = df.sort_values("미스매치점수", ascending=False)
df_top10 = df_mismatch.head(10).copy()

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("필터")
selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + sorted(df["자치구"].tolist()))
metric_option = st.sidebar.radio(
    "서울 해석 기준",
    ["미스매치점수", "위험지수", "영유아1000명당시설수"]
)

if selected_gu != "전체":
    filtered_df = df[df["자치구"] == selected_gu].copy()
else:
    filtered_df = df.copy()

# -----------------------------
# 헤더
# -----------------------------
st.markdown("<h1>서울시 자치구별 유아 친화 지표</h1>", unsafe_allow_html=True)
st.caption("영유아 인구, 방문 수요, 교통, 시설, 주차, 안전 데이터를 통합해 자치구별 공급 여건을 비교한 공급자 관점 대시보드")

# -----------------------------
# 지표 설명 박스
# -----------------------------
with st.expander("지표 설명 보기"):
    st.markdown("""
**1. 수요지수**  
- 의미: 해당 자치구의 유아 동반 나들이 수요 압력을 나타내는 상대 지표  
- 계산: 표준화(영유아인구수) + 표준화(일평균방문자수) + 교통혼잡지표

**2. 공급지수**  
- 의미: 해당 자치구의 나들이 관련 공급 여건을 나타내는 상대 지표  
- 계산: 표준화(시설수) + 표준화(주차장수) + 표준화(보호구역수)

**3. 위험지수**  
- 의미: 어린이 안전 측면의 취약성을 나타내는 상대 지표  
- 계산: 표준화(어린이교통사고) + 표준화(보호구역1개당사고수)

**4. 미스매치점수**  
- 의미: 수요 대비 공급 부족 정도를 보여주는 핵심 지표  
- 계산: 수요지수 - 공급지수  
- 해석: 값이 높을수록 수요에 비해 공급 압력이 큰 자치구

**5. 정책유형**  
- 공급 확충 우선형: 수요 대비 공급 부족이 크고, 인구 대비 시설도 부족한 지역  
- 안전 보완형: 보호구역 대비 사고 수준이 높은 지역  
- 상대 양호형: 위 두 유형에 속하지 않는 지역

**6. 공급취약여부**  
- 의미: 미스매치점수가 전체 자치구 중앙값보다 높은 경우 '취약'으로 분류한 값
""")

st.markdown("""
<div class="info-note">
※ 수요지수·공급지수·위험지수·미스매치점수는 자치구 간 상대 비교를 위해 프로젝트에서 정의한 지표입니다.
</div>
""", unsafe_allow_html=True)

st.markdown("")

# -----------------------------
# 현재 해석 기준
# -----------------------------
if metric_option == "미스매치점수":
    metric_desc = "수요 대비 공급 압력"
    metric_top3 = df.sort_values("미스매치점수", ascending=False)["자치구"].head(3).tolist()
    metric_title = "현재 기준: 미스매치점수"
    right_title = "공급취약 자치구 TOP 10"
    right_df = df.sort_values("미스매치점수", ascending=False).head(10).copy().sort_values("미스매치점수", ascending=True)
    right_x = "미스매치점수"
    right_color = "정책유형"
elif metric_option == "위험지수":
    metric_desc = "안전 취약성"
    metric_top3 = df.sort_values("위험지수", ascending=False)["자치구"].head(3).tolist()
    metric_title = "현재 기준: 위험지수"
    right_title = "안전 취약 자치구 TOP 10"
    right_df = df.sort_values("위험지수", ascending=False).head(10).copy().sort_values("위험지수", ascending=True)
    right_x = "위험지수"
    right_color = "정책유형"
else:
    metric_desc = "시설 공급 수준"
    metric_top3 = df.sort_values("영유아1000명당시설수", ascending=True)["자치구"].head(3).tolist()
    metric_title = "현재 기준: 영유아 1천명당 시설 수"
    right_title = "시설수준 취약 자치구 TOP 10"
    right_df = df.sort_values("영유아1000명당시설수", ascending=True).head(10).copy().sort_values("영유아1000명당시설수", ascending=False)
    right_x = "영유아1000명당시설수"
    right_color = "정책유형"

# -----------------------------
# 선택 자치구 요약
# -----------------------------
if selected_gu != "전체":
    row = filtered_df.iloc[0]

    avg_mismatch = df["미스매치점수"].mean()
    avg_risk = df["위험지수"].mean()
    avg_facility = df["영유아1000명당시설수"].mean()

    mismatch_rank = int(df["미스매치점수"].rank(ascending=False, method="min")[row.name])
    risk_rank = int(df["위험지수"].rank(ascending=False, method="min")[row.name])
    facility_rank = int(df["영유아1000명당시설수"].rank(ascending=False, method="min")[row.name])

    if row["정책유형"] == "공급 확충 우선형":
        badge_class = "badge-red"
    elif row["정책유형"] == "안전 보완형":
        badge_class = "badge-orange"
    else:
        badge_class = "badge-blue"

    st.markdown('<div class="section-title">선택 자치구 요약</div>', unsafe_allow_html=True)

    left_summary, right_summary = st.columns([1.2, 0.8])

    with left_summary:
        st.markdown(f"""
        <div class="selected-summary">
            <div class="small-label">현재 선택</div>
            <div class="big-number">{row['자치구']}</div>
            <div style="margin-top:8px;">
                <span class="{badge_class}">{row['정책유형']}</span>
            </div>
            <div style="margin-top:12px; color:#374151; line-height:1.75;">
                시설수 <b>{int(row['시설수'])}개</b> · 영유아 인구 <b>{int(row['영유아인구수']):,}명</b><br>
                시설수준 <b>{row['영유아1000명당시설수']:.2f}</b> / 평균 {avg_facility:.2f}<br>
                미스매치 <b>{row['미스매치점수']:.2f}</b> / 평균 {avg_mismatch:.2f}<br>
                위험지수 <b>{row['위험지수']:.2f}</b> / 평균 {avg_risk:.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right_summary:
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-label">미스매치</div>
                <div class="big-number">{mismatch_rank}위</div>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-label">위험지수</div>
                <div class="big-number">{risk_rank}위</div>
            </div>
            """, unsafe_allow_html=True)
        with r3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-label">시설수준</div>
                <div class="big-number">{facility_rank}위</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

# -----------------------------
# 상단 재배치
# -----------------------------
top_left, top_right = st.columns([1.0, 1.25])

with top_left:
    st.markdown('<div class="section-title">현재 해석 기준</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="filter-summary">
    <b>{metric_title}</b> · {metric_desc}<br>
    기준상 주요 자치구: <b>{", ".join(metric_top3)}</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="tight-space"></div>', unsafe_allow_html=True)

    total_facilities = int(df["시설수"].sum())
    avg_facility_per_1000 = round(df["영유아1000명당시설수"].mean(), 2)
    vulnerable_count = int((df["공급취약여부"] == "취약").sum())
    top_priority_gu = df_mismatch.iloc[0]["자치구"]

    k1, k2 = st.columns(2)
    k3, k4 = st.columns(2)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="small-label">총 시설 수</div>
            <div class="big-number">{total_facilities:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="small-label">평균 영유아 1천명당 시설 수</div>
            <div class="big-number">{avg_facility_per_1000}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="small-label">공급 취약 자치구 수</div>
            <div class="big-number">{vulnerable_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="small-label">확충 우선 지역 1위</div>
            <div class="big-number">{top_priority_gu}</div>
        </div>
        """, unsafe_allow_html=True)

with top_right:
    st.markdown('<div class="section-title">확충 우선 지역 TOP 3</div>', unsafe_allow_html=True)
    top3_cols = st.columns(3)
    top3 = df_mismatch.head(3)

    for i, row in top3.reset_index(drop=True).iterrows():
        if row["정책유형"] == "공급 확충 우선형":
            badge_class = "badge-red"
        elif row["정책유형"] == "안전 보완형":
            badge_class = "badge-orange"
        else:
            badge_class = "badge-blue"

        with top3_cols[i]:
            st.markdown(f"""
            <div class="top-card">
                <div class="small-label">TOP {i+1}</div>
                <div class="big-number">{row['자치구']}</div>
                <div style="margin-top:8px;">
                    <span class="{badge_class}">{row['정책유형']}</span>
                </div>
                <div style="margin-top:10px; color:#374151;">
                    미스매치 <b>{row['미스매치점수']:.2f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="tight-space"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">정책 유형별 주요 자치구</div>', unsafe_allow_html=True)

    type1 = df[df["정책유형"] == "공급 확충 우선형"]["자치구"].tolist()
    type2 = df[df["정책유형"] == "안전 보완형"]["자치구"].tolist()
    type3 = df[df["정책유형"] == "상대 양호형"]["자치구"].tolist()

    t1, t2, t3 = st.columns(3)

    with t1:
        st.markdown(f"""
        <div class="type-card-red">
            <b>공급 확충 우선형</b>
            <div class="type-count">{len(type1)}개 구</div>
            <div class="type-list">{' · '.join(type1[:5]) if type1 else '해당 없음'}</div>
        </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown(f"""
        <div class="type-card-orange">
            <b>안전 보완형</b>
            <div class="type-count">{len(type2)}개 구</div>
            <div class="type-list">{' · '.join(type2[:5]) if type2 else '해당 없음'}</div>
        </div>
        """, unsafe_allow_html=True)

    with t3:
        st.markdown(f"""
        <div class="type-card-blue">
            <b>상대 양호형</b>
            <div class="type-count">{len(type3)}개 구</div>
            <div class="type-list">{' · '.join(type3[:5]) if type3 else '해당 없음'}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# 지도 + 오른쪽 차트
# -----------------------------
left, right = st.columns([1.2, 0.8])

with left:
    st.markdown('<div class="section-title">서울 자치구 지도</div>', unsafe_allow_html=True)

    geojson_url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"
    color_scale = "OrRd" if metric_option != "영유아1000명당시설수" else "Blues"

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

    fig_map.update_traces(
        marker_line_width=1.2,
        marker_line_color="rgba(70,70,70,0.7)"
    )

    if selected_gu != "전체":
        selected_outline_df = df[df["자치구"] == selected_gu].copy()

        fig_map.add_trace(
            go.Choroplethmapbox(
                geojson=geojson_url,
                locations=selected_outline_df["자치구"],
                z=[1] * len(selected_outline_df),
                featureidkey="properties.name",
                colorscale=[[0, "rgba(255,255,255,0.08)"], [1, "rgba(255,255,255,0.08)"]],
                showscale=False,
                hoverinfo="skip",
                marker=dict(
                    line=dict(color="#111827", width=5)
                ),
                name="선택 자치구"
            )
        )

    fig_map.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=620,
        coloraxis_colorbar=dict(title=metric_option),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        )
    )

    st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.markdown(f'<div class="section-title">{right_title}</div>', unsafe_allow_html=True)

    fig_bar = px.bar(
        right_df,
        x=right_x,
        y="자치구",
        orientation="h",
        color=right_color,
        text=right_x,
        color_discrete_map={
            "공급 확충 우선형": "#ef4444",
            "안전 보완형": "#f59e0b",
            "상대 양호형": "#3b82f6"
        } if right_color == "정책유형" else None,
        color_continuous_scale="Blues" if metric_option == "영유아1000명당시설수" else "OrRd"
    )

    # 선택 자치구가 TOP10 안에 있으면 별도 강조
    if selected_gu != "전체":
        marker_colors = []
        for gu in right_df["자치구"]:
            if gu == selected_gu:
                marker_colors.append("#111827")
            else:
                marker_colors.append(None)
        try:
            fig_bar.update_traces(marker_color=marker_colors)
        except Exception:
            pass

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=right_x,
        yaxis_title=""
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# 우선순위 매트릭스
# -----------------------------
st.markdown('<div class="section-title">우선순위 매트릭스</div>', unsafe_allow_html=True)
st.caption("x축은 공급 부족(미스매치), y축은 안전 취약성(위험지수), 버블 크기는 영유아 인구 규모를 의미합니다.")

matrix_df = df.copy()
matrix_df["강조여부"] = np.where(matrix_df["자치구"] == selected_gu, "선택 자치구", "기타")

fig_matrix = px.scatter(
    matrix_df,
    x="미스매치점수",
    y="위험지수",
    size="영유아인구수",
    color="정책유형",
    hover_name="자치구",
    text="자치구",
    color_discrete_map={
        "공급 확충 우선형": "#ef4444",
        "안전 보완형": "#f59e0b",
        "상대 양호형": "#3b82f6"
    },
    size_max=38
)

fig_matrix.update_traces(textposition="top center")
fig_matrix.add_vline(x=df["미스매치점수"].median(), line_dash="dash", line_color="#94a3b8")
fig_matrix.add_hline(y=df["위험지수"].median(), line_dash="dash", line_color="#94a3b8")

if selected_gu != "전체":
    selected_row = matrix_df[matrix_df["자치구"] == selected_gu].iloc[0]
    fig_matrix.add_trace(
        go.Scatter(
            x=[selected_row["미스매치점수"]],
            y=[selected_row["위험지수"]],
            mode="markers",
            marker=dict(
                size=selected_row["영유아인구수"] / matrix_df["영유아인구수"].max() * 38 + 12,
                color="rgba(0,0,0,0)",
                line=dict(color="#111827", width=3)
            ),
            hoverinfo="skip",
            showlegend=False
        )
    )

fig_matrix.update_layout(
    height=520,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis_title="미스매치점수",
    yaxis_title="위험지수"
)

st.plotly_chart(fig_matrix, use_container_width=True)

# -----------------------------
# 액션플랜
# -----------------------------
st.markdown('<div class="section-title">액션플랜 제안</div>', unsafe_allow_html=True)
st.caption("분석 결과를 바탕으로 자치구 유형별 우선 실행 방향을 제안합니다.")

action_col1, action_col2, action_col3 = st.columns(3)

priority_supply = "· ".join(type1[:3]) if len(type1) > 0 else "해당 없음"
priority_safety = "· ".join(type2[:5]) if len(type2) > 0 else "해당 없음"
priority_monitor = "· ".join(type3[:5]) if len(type3) > 0 else "해당 없음"

with action_col1:
    st.markdown(f"""
    <div class="action-card-yellow">
        <div class="action-title">① 공급 확충 우선</div>
        <div class="action-list">
        대상: <b>{priority_supply}</b><br><br>
        - 공공형 키즈공간·실내 놀이공간 우선 검토<br>
        - 영유아 인구 대비 시설 부족 생활권부터 단계적 확대<br>
        - 기존 시설의 운영시간·수용력 확장 검토
        </div>
    </div>
    """, unsafe_allow_html=True)

with action_col2:
    st.markdown(f"""
    <div class="action-card-red">
        <div class="action-title">② 안전 보완 우선</div>
        <div class="action-list">
        대상: <b>{priority_safety}</b><br><br>
        - 보호구역 사고 다발 구간 현장점검 우선 시행<br>
        - 시설 인근 보행동선·횡단보도·감속 유도시설 개선<br>
        - 유아 동반 이동 경로 중심 교통안전 보완
        </div>
    </div>
    """, unsafe_allow_html=True)

with action_col3:
    st.markdown(f"""
    <div class="action-card-blue">
        <div class="action-title">③ 유지·모니터링</div>
        <div class="action-list">
        대상: <b>{priority_monitor}</b><br><br>
        - 현 수준 유지 및 혼잡도·수요 변화 지속 모니터링<br>
        - 가족친화 시설 운영 우수사례 관리<br>
        - 수요 증가 시 우선순위 재평가
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# 수요/공급 비교
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
# 하단 시각화
# -----------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.markdown('<div class="section-title">영유아 1천명당 시설 수 하위 5개</div>', unsafe_allow_html=True)

    low_df = df.sort_values("영유아1000명당시설수", ascending=True).head(5).copy()
    low_mean = df["영유아1000명당시설수"].mean()

    fig_low = go.Figure()

    fig_low.add_vline(
        x=low_mean,
        line_dash="dash",
        line_color="#94a3b8"
    )
    fig_low.add_annotation(
        x=low_mean,
        y=1.08,
        yref="paper",
        text="전체 평균",
        showarrow=False,
        font=dict(color="#64748b", size=12),
        xanchor="center"
    )

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
        hovertemplate="<b>%{y}</b><br>영유아 1천명당 시설 수: %{x:.2f}<br><extra></extra>"
    ))

    x_max_low = max(low_mean, low_df["영유아1000명당시설수"].max()) * 1.10
    x_min_low = max(0, low_df["영유아1000명당시설수"].min() * 0.75)

    fig_low.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="영유아 1천명당 시설 수",
        yaxis_title="",
        plot_bgcolor="white"
    )
    fig_low.update_xaxes(range=[x_min_low, x_max_low])
    fig_low.update_yaxes(automargin=True)

    st.plotly_chart(fig_low, use_container_width=True)

with col_b:
    st.markdown('<div class="section-title">보호구역 1개당 사고 수 상위 5개</div>', unsafe_allow_html=True)

    risk_df = df.sort_values("보호구역1개당사고수", ascending=False).head(5).copy().sort_values("보호구역1개당사고수", ascending=True)
    risk_mean = df["보호구역1개당사고수"].mean()

    fig_risk = go.Figure()

    fig_risk.add_vline(
        x=risk_mean,
        line_dash="dash",
        line_color="#94a3b8"
    )
    fig_risk.add_annotation(
        x=risk_mean,
        y=1.08,
        yref="paper",
        text="전체 평균",
        showarrow=False,
        font=dict(color="#64748b", size=12),
        xanchor="center"
    )

    for _, row in risk_df.iterrows():
        fig_risk.add_shape(
            type="line",
            x0=0,
            x1=row["보호구역1개당사고수"],
            y0=row["자치구"],
            y1=row["자치구"],
            line=dict(color="#fca5a5", width=6)
        )

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
        hovertemplate="<b>%{y}</b><br>보호구역 1개당 사고 수: %{x:.3f}<br><extra></extra>"
    ))

    x_max_risk = max(risk_mean, risk_df["보호구역1개당사고수"].max()) * 1.08

    fig_risk.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="보호구역 1개당 사고 수",
        yaxis_title="",
        plot_bgcolor="white"
    )
    fig_risk.update_xaxes(range=[0, x_max_risk])
    fig_risk.update_yaxes(automargin=True)

    st.plotly_chart(fig_risk, use_container_width=True)

# -----------------------------
# 요약 해석
# -----------------------------
top3_names = ", ".join(df_mismatch.head(3)["자치구"].tolist())
risk_top3 = ", ".join(df.sort_values("보호구역1개당사고수", ascending=False).head(3)["자치구"].tolist())
facility_low3 = ", ".join(df.sort_values("영유아1000명당시설수", ascending=True).head(3)["자치구"].tolist())

st.markdown('<div class="section-title">요약 해석</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="comment-box">
1. 미스매치 기준 주요 자치구: <b>{top3_names}</b><br>
2. 안전 보완 우선 검토 자치구: <b>{risk_top3}</b><br>
3. 시설 공급 수준이 낮은 자치구: <b>{facility_low3}</b>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# 상세 데이터
# -----------------------------
with st.expander("자치구별 상세 데이터 보기"):
    cols_to_show = [
        "자치구", "정책유형", "시설수", "영유아인구수", "일평균방문자수",
        "평균통행속도", "영유아1000명당시설수", "보호구역1개당사고수",
        "수요지수", "공급지수", "위험지수", "미스매치점수"
    ]
    show_df = filtered_df[cols_to_show].copy() if selected_gu != "전체" else df[cols_to_show].copy()
    st.dataframe(show_df, use_container_width=True, hide_index=True)