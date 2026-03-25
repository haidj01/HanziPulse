"""
HanziPulse - visualizer.py
Streamlit 대시보드
실행: streamlit run visualizer.py
"""

import json
import glob
import pandas as pd
import numpy as np
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from collections import defaultdict
from itertools import combinations

# ── 설정 ──────────────────────────────────────────────────
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

st.set_page_config(
    page_title="HanziPulse",
    page_icon="⛩️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 스타일 ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

.main { background-color: #0D0D0D; }

.stApp {
    background-color: #0D0D0D;
    color: #E8E0D0;
}

h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: #E8E0D0 !important;
}

.metric-card {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-left: 3px solid #C8963E;
    border-radius: 4px;
    padding: 16px 20px;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 2rem;
    font-weight: 500;
    color: #C8963E;
    font-family: 'DM Serif Display', serif;
}

.metric-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.tag-chip {
    display: inline-block;
    background: #1E1E1E;
    border: 1px solid #333;
    color: #C8963E;
    padding: 3px 10px;
    border-radius: 2px;
    font-size: 0.78rem;
    margin: 2px;
    font-family: 'DM Mono', monospace;
}

.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: #E8E0D0;
    border-bottom: 1px solid #2A2A2A;
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
}

.stSidebar {
    background-color: #111111 !important;
}

.stSidebar [data-testid="stMarkdownContainer"] p {
    color: #888 !important;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)


# ── 데이터 로더 ────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_latest_trends():
    files = sorted(glob.glob(str(RAW_DIR / "trends_*.csv")))
    if not files:
        return None, None
    path = files[-1]
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df, path

@st.cache_data(ttl=300)
def load_latest_etsy():
    files = sorted(glob.glob(str(RAW_DIR / "etsy_tags_*.json")))
    if not files:
        return None, None
    path = files[-1]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, path

@st.cache_data(ttl=300)
def load_trends_summary():
    path = PROCESSED_DIR / "trends_summary.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=300)
def load_network_summary():
    path = PROCESSED_DIR / "network_summary.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 분석 함수 ──────────────────────────────────────────────
def build_cooccurrence(etsy_data: dict, min_count: int = 2) -> list:
    cooccur = defaultdict(lambda: defaultdict(int))
    for keyword, info in etsy_data.items():
        tags = list(set([t.lower().strip() for t in info.get("tags", [])]))
        for t1, t2 in combinations(tags, 2):
            cooccur[t1][t2] += 1
            cooccur[t2][t1] += 1
    pairs = []
    seen = set()
    for k, related in cooccur.items():
        for v, count in related.items():
            if count >= min_count:
                key = tuple(sorted([k, v]))
                if key not in seen:
                    pairs.append({"tag1": k, "tag2": v, "count": count})
                    seen.add(key)
    return sorted(pairs, key=lambda x: x["count"], reverse=True)

def build_network_figure(pairs: list, top_n: int = 50) -> go.Figure:
    top_pairs = pairs[:top_n]
    G = nx.Graph()
    for p in top_pairs:
        G.add_edge(p["tag1"], p["tag2"], weight=p["count"])

    pos = nx.spring_layout(G, k=2.5, seed=42)
    communities = list(nx.community.greedy_modularity_communities(G))
    palette = ["#C8963E", "#4E9AF1", "#2ECC9A", "#E05C5C", "#9B7FD4", "#F5A623"]
    color_map = {}
    for i, comm in enumerate(communities):
        for node in comm:
            color_map[node] = palette[i % len(palette)]

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.8, color="#333333"),
        hoverinfo="none", mode="lines"
    )

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_colors = [color_map.get(n, "#888") for n in G.nodes()]
    node_sizes = [10 + G.degree(n, weight="weight") * 3 for n in G.nodes()]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=list(G.nodes()),
        textposition="top center",
        textfont=dict(size=9, color="#CCCCCC", family="DM Mono"),
        hoverinfo="text",
        marker=dict(
            color=node_colors,
            size=node_sizes,
            line=dict(width=1, color="#0D0D0D")
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            paper_bgcolor="#0D0D0D",
            plot_bgcolor="#0D0D0D",
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=550
        )
    )
    return fig


# ── 사이드바 ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⛩️ HanziPulse")
    st.markdown("Korean Market Intelligence")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📈 Trends", "🔗 Network", "🏷️ Tag Analysis"],
        label_visibility="collapsed"
    )

    st.divider()

    if st.button("🔄 Reload Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    trends_df, trends_path = load_latest_trends()
    etsy_data, etsy_path = load_latest_etsy()

    if trends_path:
        fname = Path(trends_path).name
        ts = fname.replace("trends_", "").replace(".csv", "")
        st.markdown(f"**Trends:** `{ts[:8]}`")
    else:
        st.markdown("**Trends:** No data")

    if etsy_path:
        fname = Path(etsy_path).name
        ts = fname.replace("etsy_tags_", "").replace(".json", "")
        st.markdown(f"**Etsy:** `{ts[:8]}`")
    else:
        st.markdown("**Etsy:** Pending approval")


# ── 페이지: Trends ─────────────────────────────────────────
if page == "📈 Trends":
    st.markdown("# Trend Analysis")

    if trends_df is None:
        st.warning("⚠️ Trends 데이터 없음 — `python collector.py` 먼저 실행하세요")
        st.stop()

    summary = load_trends_summary()

    # 메트릭 카드
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(trends_df.columns)}</div>
            <div class="metric-label">Keywords Tracked</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        top_kw = trends_df.mean().idxmax()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.2rem">{top_kw}</div>
            <div class="metric-label">Top Keyword</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        date_range = f"{trends_df.index[0].strftime('%Y.%m')} – {trends_df.index[-1].strftime('%Y.%m')}"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.2rem">{date_range}</div>
            <div class="metric-label">Date Range</div>
        </div>""", unsafe_allow_html=True)

    # 키워드 선택
    st.markdown('<div class="section-title">Interest Over Time</div>', unsafe_allow_html=True)
    all_kw = list(trends_df.columns)
    selected = st.multiselect(
        "Keywords",
        all_kw,
        default=all_kw[:6],
        label_visibility="collapsed"
    )

    if selected:
        fig = px.line(
            trends_df[selected],
            color_discrete_sequence=["#C8963E", "#4E9AF1", "#2ECC9A",
                                      "#E05C5C", "#9B7FD4", "#F5A623"],
        )
        fig.update_layout(
            paper_bgcolor="#0D0D0D",
            plot_bgcolor="#111111",
            font=dict(color="#E8E0D0", family="DM Mono"),
            legend=dict(bgcolor="#0D0D0D", bordercolor="#333"),
            xaxis=dict(gridcolor="#1E1E1E"),
            yaxis=dict(gridcolor="#1E1E1E"),
            height=380,
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top / Rising
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">🔝 Top Keywords</div>', unsafe_allow_html=True)
        top_series = trends_df.mean().sort_values(ascending=False).head(15)
        fig2 = px.bar(
            x=top_series.values,
            y=top_series.index,
            orientation="h",
            color=top_series.values,
            color_continuous_scale=["#1A1A1A", "#C8963E"]
        )
        fig2.update_layout(
            paper_bgcolor="#0D0D0D", plot_bgcolor="#111111",
            font=dict(color="#E8E0D0", family="DM Mono"),
            showlegend=False, coloraxis_showscale=False,
            height=400, margin=dict(l=0, r=0, t=0, b=0),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">🚀 Rising Keywords</div>', unsafe_allow_html=True)
        recent = trends_df.tail(4).mean()
        overall = trends_df.mean()
        growth = ((recent - overall) / (overall + 1)).sort_values(ascending=False).head(15)
        fig3 = px.bar(
            x=growth.values,
            y=growth.index,
            orientation="h",
            color=growth.values,
            color_continuous_scale=["#1A1A1A", "#2ECC9A"]
        )
        fig3.update_layout(
            paper_bgcolor="#0D0D0D", plot_bgcolor="#111111",
            font=dict(color="#E8E0D0", family="DM Mono"),
            showlegend=False, coloraxis_showscale=False,
            height=400, margin=dict(l=0, r=0, t=0, b=0),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig3, use_container_width=True)

    # 상관관계 히트맵
    st.markdown('<div class="section-title">📊 Keyword Correlation</div>', unsafe_allow_html=True)
    corr = trends_df[selected].corr() if selected else trends_df.corr()
    fig4 = px.imshow(
        corr,
        color_continuous_scale=["#0D0D0D", "#C8963E"],
        zmin=-1, zmax=1
    )
    fig4.update_layout(
        paper_bgcolor="#0D0D0D",
        font=dict(color="#E8E0D0", family="DM Mono"),
        height=400, margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig4, use_container_width=True)


# ── 페이지: Network ────────────────────────────────────────
elif page == "🔗 Network":
    st.markdown("# Keyword Network")

    if etsy_data is None:
        st.info("⏳ Etsy API 승인 대기 중 — 승인 후 네트워크 분석 가능")
        st.stop()

    min_count = st.slider("Min co-occurrence", 2, 10, 3)
    top_n = st.slider("Max nodes", 20, 100, 50)

    pairs = build_cooccurrence(etsy_data, min_count=min_count)

    if not pairs:
        st.warning("Co-occurrence 데이터 부족")
        st.stop()

    # 브릿지 키워드
    G = nx.Graph()
    for p in pairs[:top_n]:
        G.add_edge(p["tag1"], p["tag2"], weight=p["count"])
    centrality = nx.betweenness_centrality(G, weight="weight")
    bridge_kws = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:8]

    st.markdown('<div class="section-title">🌉 Bridge Keywords</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (kw, score) in enumerate(bridge_kws):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size:1rem">{kw}</div>
                <div class="metric-label">score {score:.3f}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">🕸️ Network Graph</div>', unsafe_allow_html=True)
    fig = build_network_figure(pairs, top_n=top_n)
    st.plotly_chart(fig, use_container_width=True)

    # 클러스터
    communities = list(nx.community.greedy_modularity_communities(G))
    st.markdown('<div class="section-title">🎯 Keyword Clusters</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(communities), 3))
    palette = ["#C8963E", "#4E9AF1", "#2ECC9A", "#E05C5C", "#9B7FD4"]
    for i, comm in enumerate(communities[:3]):
        with cols[i]:
            color = palette[i % len(palette)]
            st.markdown(f"**Cluster {i+1}**")
            chips = " ".join([f'<span class="tag-chip">{t}</span>' for t in list(comm)[:15]])
            st.markdown(chips, unsafe_allow_html=True)


# ── 페이지: Tag Analysis ───────────────────────────────────
elif page == "🏷️ Tag Analysis":
    st.markdown("# Tag Analysis")

    if etsy_data is None:
        st.info("⏳ Etsy API 승인 대기 중")
        st.stop()

    # 키워드별 listing 수
    st.markdown('<div class="section-title">📦 Listing Count by Keyword</div>', unsafe_allow_html=True)
    listing_counts = {kw: info["listing_count"] for kw, info in etsy_data.items()}
    df_counts = pd.DataFrame(
        list(listing_counts.items()), columns=["keyword", "count"]
    ).sort_values("count", ascending=False)

    fig = px.bar(
        df_counts, x="count", y="keyword", orientation="h",
        color="count", color_continuous_scale=["#1A1A1A", "#C8963E"]
    )
    fig.update_layout(
        paper_bgcolor="#0D0D0D", plot_bgcolor="#111111",
        font=dict(color="#E8E0D0", family="DM Mono"),
        showlegend=False, coloraxis_showscale=False,
        height=500, margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 키워드별 태그 탐색
    st.markdown('<div class="section-title">🔍 Tag Explorer</div>', unsafe_allow_html=True)
    selected_kw = st.selectbox("Select Keyword", list(etsy_data.keys()))
    if selected_kw:
        tags = etsy_data[selected_kw].get("tags", [])
        tag_counts = pd.Series(tags).value_counts().head(30)
        chips = " ".join([
            f'<span class="tag-chip">{t} <span style="color:#666">×{c}</span></span>'
            for t, c in tag_counts.items()
        ])
        st.markdown(chips, unsafe_allow_html=True)
