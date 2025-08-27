# plot_inline_trend_by_for_key.py
# -----------------------------------------------
# iqc_data.xlsx를 읽어 FOR_KEY별로 필터링한 뒤
# (DEVICE / OPER / ROUTE 등) 기준(color)으로
# px.box + USL/LSL/TGT 라인을 겹쳐 저장(HTML)
# -----------------------------------------------

import os
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


EXCEL_FILE = "iqc_data.xlsx"      # 동일 폴더에 두세요
OUTPUT_DIR = "plots"              # 결과 저장 폴더
CRITERIA_LIST = ["DEVICE", "OPER", "ROUTE"]  # 색상 기준으로 쓸 컬럼 목록
# 특정 FOR_KEY만 그릴 때 리스트로 지정(없으면 전체)
TARGET_FOR_KEYS: Optional[List[str]] = None


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print("⚠️ iqc_data.xlsx 파일이 없어 샘플 데이터를 사용합니다.")
        data = [
            {
                "FOR_KEY":"P1931.52926.5","TEAM":"A","TRANS_DATE":"2025-07-16 16:33:14","DEVICE":"D1","ROUTE":"R","ROUTE_DESC":"G",
                "OPER":1,"RECIPE":"R1","LOT_NO":"L1","WAFER_ID":"W1","MAIN_EQ":"E1","ZONE":1,"EQ_ZONE":"E11","PARA":"P1",
                "NO_VAL":9,
                "NO_VAL1":29.05,"NO_VAL2":29.162,"NO_VAL3":29.132,"NO_VAL4":28.974,"NO_VAL5":29.269,
                "NO_VAL6":29.178,"NO_VAL7":29.118,"NO_VAL8":28.569,"NO_VAL9":29.858,"NO_VAL10":None,
                "USL":31.5,"UCL":30.5,"TGT":29,"LSL":26.5,"LCL":27.5
            },
            {
                "FOR_KEY":"P1931.52926.5","TEAM":"A","TRANS_DATE":"2025-07-16 15:01:17","DEVICE":"D1","ROUTE":"R","ROUTE_DESC":"G",
                "OPER":1,"RECIPE":"R1","LOT_NO":"L2","WAFER_ID":"W2","MAIN_EQ":"E1","ZONE":4,"EQ_ZONE":"E14","PARA":"P1",
                "NO_VAL":9,
                "NO_VAL1":28.93,"NO_VAL2":29.062,"NO_VAL3":29.254,"NO_VAL4":29.26,"NO_VAL5":29.466,
                "NO_VAL6":29.017,"NO_VAL7":28.817,"NO_VAL8":28.75,"NO_VAL9":29.225,"NO_VAL10":None,
                "USL":31.5,"UCL":30.5,"TGT":29,"LSL":26.5,"LCL":27.5
            },
            {
                "FOR_KEY":"P29129121113","TEAM":"A","TRANS_DATE":"2025-07-26 22:47:15","DEVICE":"D2","ROUTE":"R","ROUTE_DESC":"G",
                "OPER":1,"RECIPE":"R2","LOT_NO":"L3","WAFER_ID":"W3","MAIN_EQ":"E1","ZONE":4,"EQ_ZONE":"E14","PARA":"P2",
                "NO_VAL":9,
                "NO_VAL1":122.49,"NO_VAL2":122.12,"NO_VAL3":122.36,"NO_VAL4":122.39,"NO_VAL5":122.2,
                "NO_VAL6":122.75,"NO_VAL7":122.85,"NO_VAL8":122.61,"NO_VAL9":122.43,"NO_VAL10":None,
                "USL":129,"UCL":126,"TGT":121,"LSL":113,"LCL":116
            },
            {
                "FOR_KEY":"P29129121113","TEAM":"A","TRANS_DATE":"2025-07-21 18:14:23","DEVICE":"D1","ROUTE":"R","ROUTE_DESC":"G",
                "OPER":1,"RECIPE":"R1","LOT_NO":"L4","WAFER_ID":"W4","MAIN_EQ":"E2","ZONE":2,"EQ_ZONE":"E22","PARA":"P2",
                "NO_VAL":9,
                "NO_VAL1":120.8,"NO_VAL2":120.59,"NO_VAL3":120.38,"NO_VAL4":120.31,"NO_VAL5":120.25,
                "NO_VAL6":120.69,"NO_VAL7":120.63,"NO_VAL8":120.38,"NO_VAL9":120.27,"NO_VAL10":None,
                "USL":129,"UCL":126,"TGT":121,"LSL":113,"LCL":116
            },
        ]
        return pd.DataFrame(data)

    return pd.read_excel(path)


def sanitize(name: str) -> str:
    return re.sub(r"[^\w\-.]+", "_", str(name))


def detect_no_val_cols(df: pd.DataFrame) -> List[str]:
    cols = [c for c in df.columns if re.fullmatch(r"NO_VAL\d+", str(c))]
    cols.sort(key=lambda x: int(re.sub(r"\D", "", x)))
    return cols


def choose_x_column(df: pd.DataFrame) -> str:
    """
    FOR_KEY로 필터링한 후, x축으로 쓸 'key' 후보 우선순위:
    1) TRANS_DATE  2) LOT_NO  3) WAFER_ID  4) 기존 FOR_KEY(단일 카테고리)  5) 행 인덱스
    """
    if "TRANS_DATE" in df.columns:
        # 시간 정렬 후 문자열화
        df["_sort_ts"] = pd.to_datetime(df["TRANS_DATE"], errors="coerce")
        df.sort_values("_sort_ts", inplace=True)
        df["key"] = df["_sort_ts"].dt.strftime("%Y-%m-%d %H:%M:%S").fillna(df["TRANS_DATE"].astype(str))
        df.drop(columns=["_sort_ts"], inplace=True)
        return "key"
    for cand in ["LOT_NO", "WAFER_ID"]:
        if cand in df.columns:
            df["key"] = df[cand].astype(str)
            return "key"
    if "FOR_KEY" in df.columns:
        df["key"] = df["FOR_KEY"].astype(str)
        return "key"
    df["key"] = df.reset_index().index.astype(str)
    return "key"


def add_spec_lines(fig, df: pd.DataFrame, key_order: List[str]) -> None:
    """Python/px와 동일한 느낌: 행 단위 시리즈를 그대로 넣어서 그립니다."""
    def _series_or_none(col):
        return df[col].tolist() if col in df.columns else None

    # key_order는 df['key']의 순서와 동일하게 만들어야 합니다.
    # 여기서는 df가 이미 그 순서로 정렬되었다고 가정합니다.
    if "USL" in df.columns:
        fig.add_trace(go.Scatter(
            x=key_order, y=_series_or_none("USL"),
            mode="lines", name=f"USL({df['USL'].iloc[0]})" if pd.notna(df['USL'].iloc[0]) else "USL",
            line=dict(color="rgba(0,0,0,0.8)", width=2), hoverinfo="none"
        ))
    if "LSL" in df.columns:
        fig.add_trace(go.Scatter(
            x=key_order, y=_series_or_none("LSL"),
            mode="lines", name=f"LSL({df['LSL'].iloc[0]})" if pd.notna(df['LSL'].iloc[0]) else "LSL",
            line=dict(color="rgba(0,0,0,0.8)", width=2), hoverinfo="none"
        ))
    if "TGT" in df.columns:
        fig.add_trace(go.Scatter(
            x=key_order, y=_series_or_none("TGT"),
            mode="lines", name=f"TGT({df['TGT'].iloc[0]})" if pd.notna(df['TGT'].iloc[0]) else "TGT",
            line=dict(color="rgba(0,0,0,0.5)", width=2), hoverinfo="none"
        ))


def plot_one(df_all: pd.DataFrame, for_key: str, color_col: str, outdir: Path) -> Path:
    df = df_all[df_all["FOR_KEY"].astype(str) == str(for_key)].copy()
    if df.empty:
        raise ValueError(f"FOR_KEY={for_key} 데이터가 없습니다.")

    # x축용 key 선택/생성 & 정렬
    x_col = choose_x_column(df)
    # NO_VAL* 감지 및 숫자화
    no_cols = detect_no_val_cols(df)
    if not no_cols:
        raise ValueError("NO_VAL1.. 형태의 측정 컬럼을 찾을 수 없습니다.")
    for c in no_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 범례 색상 기준이 없으면 단색으로 표시
    color_kw = {}
    if color_col in df.columns:
        color_kw["color"] = color_col

    # 카테고리 순서(현재 df['key'] 순)
    key_order = df["key"].astype(str).tolist()

    title = f"INLINE Trend | FOR_KEY={for_key} (color={color_col if color_col in df.columns else 'N/A'})"
    fig = px.box(
        df,
        x="key",
        y=no_cols,
        category_orders={"key": key_order},
        boxmode="overlay",
        title=title,
        height=600,
        **color_kw,
    )
    fig.update_traces(boxpoints=False)

    # Spec 라인 (행 단위 시리즈 그대로)
    add_spec_lines(fig, df, key_order)

    fig.update_layout(
        xaxis_title="Key",
        yaxis_title="Values",
        boxmode="overlay",
        hovermode="closest"
    )

    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / f"{sanitize(for_key)}__color_{sanitize(color_col if color_col in df.columns else 'NA')}.html"
    fig.write_html(str(fname), include_plotlyjs="cdn")
    print(f"✅ 저장: {fname}")
    return fname


def main():
    df_all = load_data(EXCEL_FILE)
    if "FOR_KEY" not in df_all.columns:
        raise ValueError("엑셀에 FOR_KEY 컬럼이 없습니다.")

    # 대상 FOR_KEY 집합 결정
    all_keys = df_all["FOR_KEY"].astype(str).unique().tolist()
    target_keys = TARGET_FOR_KEYS or all_keys

    outdir = Path(OUTPUT_DIR)

    for fk in target_keys:
        for crit in CRITERIA_LIST:
            try:
                plot_one(df_all, fk, crit, outdir)
            except Exception as e:
                print(f"⚠️ FOR_KEY={fk}, color={crit} 처리 중 스킵: {e}")

    print("🎉 완료!")


if __name__ == "__main__":
    main()
