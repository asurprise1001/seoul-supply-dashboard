import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="서울 자치구 공급자 대시보드",
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
.info-note {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 10px 14px;
    color: #475569;
    font-size: 0.95rem;
}
.selected-summary {
    background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
    border: 1px solid #dbeafe;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}
.filter-summary {
    background: linear-gradient(135deg, #ffffff 0%, #fffaf5 100%);
    border: 1px solid #fde68a;
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}
.badge-red {
    display: inline-block;
    background: #fee2e2;
    color: #991b1b;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge-orange {
    display: inline-block;
    background: #ffedd5;
    color: #9a3412;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge-blue {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
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
df_facility_low = df.sort_values("영유아1000명당시설수", ascending=True).head(10).copy()
df_risk_high = df.sort_values("보호구역1개당사고수", ascending=False).head(10).copy()

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
※ 본 대시보드의 수요지수·공급지수·위험지수·미스매치점수는 공식 통계지표가 아니라, 자치구 간 상대 비교를 위해 프로젝트에서 정의한 지표입니다.
</div>
""", unsafe_allow_html=True)

st.markdown("")

# -----------------------------
# 현재 해석 기준 요약
# -----------------------------
if metric_option == "미스매치점수":
    metric_desc = "수요지수에서 공급지수를 뺀 값으로, 값이 높을수록 수요 대비 공급 압력이 큰 자치구입니다."
    metric_top3 = df.sort_values("미스매치점수", ascending=False)["자치구"].head(3).tolist()
    metric_title = "현재 기준: 미스매치점수"
    right_title = "공급취약 자치구 TOP 10 (미스매치 기준)"
    right_df = df.sort_values("미스매치점수", ascending=False).head(10).copy()
    right_df = right_df.sort_values("미스매치점수", ascending=True)
    right_x = "미스매치점수"
    right_color = "정책유형"
elif metric_option == "위험지수":
    metric_desc = "어린이 교통사고와 보호구역 대비 사고 부담을 반영한 상대 지표로, 값이 높을수록 안전 취약성이 큽니다."
    metric_top3 = df.sort_values("위험지수", ascending=False)["자치구"].head(3).tolist()
    metric_title = "현재 기준: 위험지수"
    right_title = "안전 취약 자치구 TOP 10 (위험지수 기준)"
    right_df = df.sort_values("위험지수", ascending=False).head(10).copy()
    right_df = right_df.sort_values("위험지수", ascending=True)
    right_x = "위험지수"
    right_color = "정책유형"
else:
    metric_desc = "영유아 1천명당 시설 수로, 값이 낮을수록 인구 대비 시설 공급 수준이 상대적으로 낮습니다."
    metric_top3 = df.sort_values("영유아1000명당시설수", ascending=True)["자치구"].head(3).tolist()
    metric_title = "현재 기준: 영유아 1천명당 시설 수"
    right_title = "시설수준 취약 자치구 TOP 10 (영유아 1천명당 시설 수 하위)"
    right_df = df.sort_values("영유아1000명당시설수", ascending=True).head(10).copy()
    right_df = right_df.sort_values("영유아1000명당시설수", ascending=False)
    right_x = "영유아1000명당시설수"
    right_color = "정책유형"

metric_top3_text = ", ".join(metric_top3)

st.markdown('<div class="section-title">현재 해석 기준 요약</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="filter-summary">
<b>{metric_title}</b><br><br>
{metric_desc}<br><br>
현재 기준에서 상대적으로 두드러지는 자치구: <b>{metric_top3_text}</b>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# -----------------------------
# 선택 자치구 반응형 상단 요약
# -----------------------------
if selected_gu != "전체":
    row = filtered_df.iloc[0]

    avg_mismatch = df["미스매치점수"].mean()
    avg_risk = df["위험지수"].mean()
    avg_facility = df["영유아1000명당시설수"].mean()

    mismatch_vs_avg = "서울 평균보다 높음" if row["미스매치점수"] > avg_mismatch else "서울 평균보다 낮음"
    risk_vs_avg = "서울 평균보다 높음" if row["위험지수"] > avg_risk else "서울 평균보다 낮음"
    facility_vs_avg = "서울 평균보다 높음" if row["영유아1000명당시설수"] > avg_facility else "서울 평균보다 낮음"

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

    left_summary, right_summary = st.columns([1.15, 0.85])

    with left_summary:
        st.markdown(f"""
        <div class="selected-summary">
            <div class="small-label">현재 선택</div>
            <div class="big-number">{row['자치구']}</div>
            <div style="margin-top:8px;">
                <span class="{badge_class}">{row['정책유형']}</span>
            </div>
            <div style="margin-top:14px; color:#374151; line-height:1.8;">
                시설수 <b>{int(row['시설수'])}개</b><br>
                영유아 인구 <b>{int(row['영유아인구수']):,}명</b><br>
                영유아 1천명당 시설 수 <b>{row['영유아1000명당시설수']:.2f}</b> ({facility_vs_avg})<br>
                미스매치점수 <b>{row['미스매치점수']:.2f}</b> ({mismatch_vs_avg})<br>
                위험지수 <b>{row['위험지수']:.2f}</b> ({risk_vs_avg})
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right_summary:
        s1, s2, s3 = st.columns(3)

        with s1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-label">미스매치 순위</div>
                <div class="big-number">{mismatch_rank}위</div>
            </div>
            """, unsafe_allow_html=True)

        with s2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-label">위험지수 순위</div>
                <div class="big-number">{risk_rank}위</div>
            </div>
            """, unsafe_allow_html=True)

        with s3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-label">시설수준 순위</div>
                <div class="big-number">{facility_rank}위</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        if row["정책유형"] == "공급 확충 우선형":
            summary_text = "이 자치구는 수요 대비 공급 압력이 높고, 인구 대비 시설 공급도 부족한 편이라 직접적인 공급 확충 우선 검토 대상입니다."
        elif row["정책유형"] == "안전 보완형":
            summary_text = "이 자치구는 시설 부족보다도 보호구역 대비 사고 부담이 상대적으로 높아 안전 보완 정책을 우선 검토할 필요가 있습니다."
        else:
            summary_text = "이 자치구는 현재 기준으로 상대적으로 양호한 편이지만, 세부 지표를 함께 보며 유지·보완 방향을 검토할 수 있습니다."

        st.markdown(f"""
        <div class="comment-box">
        <b>{row['자치구']} 해석</b><br>
        {summary_text}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

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
st.caption("미스매치점수를 기준으로 수요 대비 공급 압력이 높은 자치구 3곳을 표시합니다.")

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
st.caption("자치구를 단순 순위가 아니라 ‘공급 확충’, ‘안전 보완’, ‘상대 양호’ 관점으로 분류한 해석용 카드입니다.")

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
# 지도 + 오른쪽 차트
# -----------------------------
left, right = st.columns([1.2, 0.8])

with left:
    st.markdown('<div class="section-title">서울 자치구 지도</div>', unsafe_allow_html=True)
    st.caption("선택한 해석 기준에 따라 자치구별 상대 수준을 지도에 표시합니다.")

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
    st.markdown(f'<div class="section-title">{right_title}</div>', unsafe_allow_html=True)
    st.caption("좌측의 해석 기준 선택에 따라 이 순위 차트도 함께 바뀝니다.")

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

    text_format = "%{text:.2f}"
    if right_x == "영유아1000명당시설수":
        text_format = "%{text:.2f}"
    elif right_x == "위험지수":
        text_format = "%{text:.2f}"

    fig_bar.update_traces(texttemplate=text_format, textposition="outside")
    fig_bar.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=right_x,
        yaxis_title=""
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# 수요/공급 비교 (Top 10만)
# -----------------------------
st.markdown('<div class="section-title">미스매치 상위 10개 자치구의 수요지수와 공급지수 비교</div>', unsafe_allow_html=True)
st.caption("수요지수는 영유아 인구·방문수요·교통혼잡을, 공급지수는 시설·주차·보호구역을 반영한 상대 비교 지표입니다.")

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
    st.caption("영유아 인구 대비 시설 수가 상대적으로 낮은 자치구를 보여줍니다.")

    low_df = df.sort_values("영유아1000명당시설수", ascending=True).head(5).copy()

    fig_low = go.Figure()
    fig_low.add_vline(
        x=df["영유아1000명당시설수"].mean(),
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="전체 평균",
        annotation_position="top"
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
    st.caption("보호구역 수를 고려했을 때 사고 부담이 상대적으로 높은 자치구를 보여줍니다.")

    risk_df = df.sort_values("보호구역1개당사고수", ascending=False).head(5).copy()
    risk_df = risk_df.sort_values("보호구역1개당사고수", ascending=True)

    fig_risk = go.Figure()
    fig_risk.add_vline(
        x=df["보호구역1개당사고수"].mean(),
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="전체 평균",
        annotation_position="top"
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
risk_top3 = ", ".join(df.sort_values("보호구역1개당사고수", ascending=False).head(3)["자치구"].tolist())
facility_low3 = ", ".join(df.sort_values("영유아1000명당시설수", ascending=True).head(3)["자치구"].tolist())

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