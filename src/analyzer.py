"""
HanziPulse - analyzer.py
키워드 연관관계 분석 (Co-occurrence + Network Graph)
"""

import json
import logging
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations

log = logging.getLogger("HanziPulse.analyzer")

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ── 1. Trends 분석 ─────────────────────────────────────────
class TrendsAnalyzer:
    def __init__(self, trends_csv: str):
        self.df = pd.read_csv(trends_csv, index_col=0, parse_dates=True)

    def top_keywords(self, n: int = 20) -> pd.Series:
        """평균 관심도 기준 상위 키워드"""
        return self.df.mean().sort_values(ascending=False).head(n)

    def rising_keywords(self, n: int = 10) -> pd.Series:
        """최근 4주 vs 이전 대비 상승 키워드"""
        recent = self.df.tail(4).mean()
        overall = self.df.mean()
        growth = (recent - overall) / (overall + 1)  # +1로 0나눔 방지
        return growth.sort_values(ascending=False).head(n)

    def correlation_matrix(self) -> pd.DataFrame:
        """키워드 간 상관관계 행렬"""
        return self.df.corr()

    def save_summary(self):
        summary = {
            "top_keywords": self.top_keywords().to_dict(),
            "rising_keywords": self.rising_keywords().to_dict(),
        }
        path = PROCESSED_DIR / "trends_summary.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        log.info(f"Trends summary 저장: {path}")
        return summary


# ── 2. Co-occurrence 분석 ──────────────────────────────────
class CooccurrenceAnalyzer:
    def __init__(self, etsy_tags_json: str, min_count: int = 3):
        with open(etsy_tags_json, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.min_count = min_count

    def build_cooccurrence_matrix(self) -> dict:
        """키워드별 태그 co-occurrence 계산"""
        cooccur = defaultdict(Counter)

        for keyword, info in self.data.items():
            tags = info.get("tags", [])
            tags_clean = [t.lower().strip() for t in tags]
            # 태그 쌍 생성
            for t1, t2 in combinations(set(tags_clean), 2):
                cooccur[t1][t2] += 1
                cooccur[t2][t1] += 1

        # min_count 이하 제거
        filtered = {
            k: {v: c for v, c in pairs.items() if c >= self.min_count}
            for k, pairs in cooccur.items()
        }
        return filtered

    def top_cooccurrences(self, n: int = 30) -> list:
        """가장 많이 함께 등장한 태그 쌍"""
        matrix = self.build_cooccurrence_matrix()
        pairs = []
        seen = set()
        for k, related in matrix.items():
            for v, count in related.items():
                key = tuple(sorted([k, v]))
                if key not in seen:
                    pairs.append({"tag1": k, "tag2": v, "count": count})
                    seen.add(key)
        return sorted(pairs, key=lambda x: x["count"], reverse=True)[:n]

    def save_summary(self):
        top = self.top_cooccurrences()
        path = PROCESSED_DIR / "cooccurrence_summary.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(top, f, ensure_ascii=False, indent=2)
        log.info(f"Co-occurrence summary 저장: {path}")
        return top


# ── 3. Network Graph 분석 ─────────────────────────────────
class NetworkAnalyzer:
    def __init__(self, cooccurrence_data: list):
        self.data = cooccurrence_data
        self.G = self._build_graph()

    def _build_graph(self) -> nx.Graph:
        G = nx.Graph()
        for item in self.data:
            G.add_edge(item["tag1"], item["tag2"], weight=item["count"])
        return G

    def bridge_keywords(self, n: int = 10) -> list:
        """
        브릿지 키워드 = betweenness centrality 높은 노드
        traditional ↔ streetwear 연결하는 핵심 키워드
        """
        centrality = nx.betweenness_centrality(self.G, weight="weight")
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:n]

    def clusters(self) -> list:
        """키워드 클러스터 감지"""
        communities = nx.community.greedy_modularity_communities(self.G)
        return [list(c) for c in communities]

    def visualize(self, output_path: str = None, top_n: int = 40):
        """네트워크 그래프 시각화"""
        # 상위 노드만 표시
        top_nodes = sorted(
            self.G.degree(weight="weight"),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        subgraph = self.G.subgraph([n for n, _ in top_nodes])

        fig, ax = plt.subplots(figsize=(16, 12))
        pos = nx.spring_layout(subgraph, k=2, seed=42)

        # 노드 크기 = degree
        node_size = [subgraph.degree(n, weight="weight") * 50 for n in subgraph.nodes()]
        # 엣지 두께 = weight
        edge_width = [subgraph[u][v]["weight"] * 0.3 for u, v in subgraph.edges()]

        # 클러스터별 색상
        communities = list(nx.community.greedy_modularity_communities(subgraph))
        color_map = {}
        colors = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261", "#264653"]
        for i, community in enumerate(communities):
            for node in community:
                color_map[node] = colors[i % len(colors)]
        node_colors = [color_map.get(n, "#999999") for n in subgraph.nodes()]

        nx.draw_networkx_nodes(subgraph, pos, node_size=node_size,
                               node_color=node_colors, alpha=0.85, ax=ax)
        nx.draw_networkx_edges(subgraph, pos, width=edge_width,
                               alpha=0.4, edge_color="#cccccc", ax=ax)
        nx.draw_networkx_labels(subgraph, pos, font_size=8,
                                font_color="#222222", ax=ax)

        ax.set_title("HanziPulse — Keyword Network Graph", fontsize=16, pad=20)
        ax.axis("off")
        plt.tight_layout()

        save_path = output_path or str(PROCESSED_DIR / "network_graph.png")
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        log.info(f"Network graph 저장: {save_path}")
        plt.show()

    def save_summary(self):
        summary = {
            "bridge_keywords": self.bridge_keywords(),
            "clusters": self.clusters()
        }
        path = PROCESSED_DIR / "network_summary.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        log.info(f"Network summary 저장: {path}")
        return summary


# ── 메인 실행 ──────────────────────────────────────────────
def run(trends_csv: str = None, etsy_tags_json: str = None):
    results = {}

    # 1. Trends 분석
    if trends_csv and Path(trends_csv).exists():
        log.info("=== Trends 분석 시작 ===")
        ta = TrendsAnalyzer(trends_csv)
        results["trends"] = ta.save_summary()
        print("\n📈 Top Keywords:")
        print(ta.top_keywords())
        print("\n🚀 Rising Keywords:")
        print(ta.rising_keywords())

    # 2. Co-occurrence + Network 분석 (Etsy 데이터 있을 때)
    if etsy_tags_json and Path(etsy_tags_json).exists():
        log.info("=== Co-occurrence 분석 시작 ===")
        ca = CooccurrenceAnalyzer(etsy_tags_json)
        cooccur_data = ca.save_summary()
        results["cooccurrence"] = cooccur_data

        log.info("=== Network 분석 시작 ===")
        na = NetworkAnalyzer(cooccur_data)
        results["network"] = na.save_summary()
        na.visualize()

        print("\n🔗 Bridge Keywords (Traditional ↔ Streetwear):")
        for kw, score in na.bridge_keywords():
            print(f"  {kw}: {score:.4f}")

    return results


if __name__ == "__main__":
    import glob

    # 가장 최근 파일 자동 선택
    trends_files = sorted(glob.glob(str(RAW_DIR / "trends_*.csv")))
    etsy_files = sorted(glob.glob(str(RAW_DIR / "etsy_tags_*.json")))

    trends_csv = trends_files[-1] if trends_files else None
    etsy_json = etsy_files[-1] if etsy_files else None

    if not trends_csv:
        log.warning("Trends 데이터 없음 — collector.py 먼저 실행하세요")
    else:
        run(trends_csv=trends_csv, etsy_tags_json=etsy_json)
