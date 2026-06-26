import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="여수시 시민여객선", layout="wide", page_icon="🚢")

BASE_CSV = "전라남도 여수시_시민여객선 운임 _여객선 터미널 이용료 기초자료 정보 기항지 정보_20250516.csv"
ROUTE_CSV = "전라남도 여수시_시민여객선 운임지원_여객선 항로 정보_20240613.csv"

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #f5f7fa;
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        padding: 14px 16px;
    }
    h1 {padding-bottom: 0.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    base = pd.read_csv(BASE_CSV, encoding="cp949")
    base.columns = [c.strip() for c in base.columns]
    route = pd.read_csv(ROUTE_CSV, encoding="cp949")
    route.columns = [c.strip() for c in route.columns]

    merged = base.merge(route, how="left", left_on="항로", right_on="항로명")
    merged.to_csv("merged.csv", index=False, encoding="utf-8-sig")
    return merged


df = load_data()

st.title("🚢 여수시 시민여객선")
st.caption("운임 · 터미널 이용료 · 항로 정보 대시보드")

st.sidebar.header("필터")
routes = st.sidebar.multiselect("항로", sorted(df["항로"].dropna().unique()))
departures = st.sidebar.multiselect("출발지", sorted(df["출발지"].dropna().unique()))
ships = st.sidebar.multiselect("선박", sorted(df["선박"].dropna().unique()))

filtered = df.copy()
if routes:
    filtered = filtered[filtered["항로"].isin(routes)]
if departures:
    filtered = filtered[filtered["출발지"].isin(departures)]
if ships:
    filtered = filtered[filtered["선박"].isin(ships)]

CHART_LAYOUT = dict(
    margin=dict(l=10, r=10, t=40, b=10),
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(size=13),
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("항로 수", filtered["항로"].nunique())
col2.metric("선박 수", filtered["선박"].nunique())
col3.metric("평균 일반대인 요금", f"{filtered['일반대인'].mean():,.0f}원")
col4.metric("평균 일반소아 요금", f"{filtered['일반소아'].mean():,.0f}원")

st.divider()

tab1, tab2 = st.tabs(["📊 차트", "📋 데이터"])

with tab1:
    fare_by_route = (
        filtered.groupby("항로")["일반대인"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    fig_fare = px.bar(
        fare_by_route,
        x="일반대인",
        y="항로",
        orientation="h",
        title="항로별 평균 일반대인 요금 (상위 15)",
        text_auto=",.0f",
    )
    fig_fare.update_yaxes(autorange="reversed", title=None)
    fig_fare.update_xaxes(title="요금(원)")
    fig_fare.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_fare, use_container_width=True)

    left, right = st.columns(2)
    with left:
        ship_counts = (
            filtered["선박"].value_counts().head(12).reset_index()
        )
        ship_counts.columns = ["선박", "건수"]
        fig_ship = px.bar(
            ship_counts, x="건수", y="선박", orientation="h", title="선박별 운항 건수"
        )
        fig_ship.update_yaxes(autorange="reversed", title=None)
        fig_ship.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_ship, use_container_width=True)

    with right:
        grade_counts = filtered["객실등급"].value_counts().reset_index()
        grade_counts.columns = ["객실등급", "건수"]
        fig_grade = px.pie(
            grade_counts, names="객실등급", values="건수", title="객실등급 분포", hole=0.4
        )
        fig_grade.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_grade, use_container_width=True)

with tab2:
    st.dataframe(
        filtered[
            [
                "항로", "출발지", "도착지", "선박", "객실등급",
                "일반대인", "일반소아", "도서대인", "도서소아",
                "시행일자", "터미널", "거리(마일)", "사용여부", "연륙교 여부", "기항지 이용료 여부",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "일반대인": st.column_config.NumberColumn(format="%,d원"),
            "일반소아": st.column_config.NumberColumn(format="%,d원"),
            "도서대인": st.column_config.NumberColumn(format="%,d원"),
            "도서소아": st.column_config.NumberColumn(format="%,d원"),
            "거리(마일)": st.column_config.NumberColumn(format="%.1f"),
        },
    )
