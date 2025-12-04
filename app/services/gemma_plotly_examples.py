"""
Example scaffolding for using the Gemma-3-27b-it model to create Plotly.js
specifications without embedding raw data points.

The helper functions below illustrate:
  * how to prepare prompts that describe the desired chart.
  * the JSON skeleton we expect Gemma to produce (data placeholders only).
  * how a backend might call the local Gemma endpoint at http://localhost:8000.

NOTE:
  - No real chart data is injected into the Plotly spec.  Gemma returns only
    layout/trace scaffolding plus references to external dataset keys.
  - Adapt HTTP payloads to match your actual Gemma serving interface.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Dict, List

import requests

GEMMA_ENDPOINT = "http://localhost:8000/v1/chat/completions"


@dataclass
class PromptContext:
    chart_type: str
    system_prompt_en: str
    system_prompt_ko: str
    user_prompt_en: str
    user_prompt_ko: str
    expected_response_skeleton: Dict[str, Any]


def _schema_block(schema: Dict[str, Any]) -> str:
    """Render dataset schema information as pretty JSON for prompt injection."""
    return json.dumps(schema, indent=2, ensure_ascii=False)


def _preview_block(preview: Dict[str, Any]) -> str:
    """Render dataset preview info (head, shape, etc.) as JSON string."""
    return json.dumps(preview, indent=2, ensure_ascii=False)


def _conversation_block(messages: List[Dict[str, str]]) -> str:
    """Render previous conversation turns as JSON."""
    return json.dumps(messages, indent=2, ensure_ascii=False)


def _build_system_prompts(
    dataset_key: str,
    dataset_schema: Dict[str, Any],
    dataset_preview: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
) -> Dict[str, str]:
    """Return English/Korean system prompts that embed schema, preview, history."""
    schema_json = _schema_block(dataset_schema)
    preview_json = _preview_block(dataset_preview)
    history_json = _conversation_block(conversation_history)

    system_en = dedent(
        f"""
        You are an expert Plotly.js spec generator.  Use only JSON responses.

        Data Origin:
          - Parsed from an uploaded Excel file.
          - Dataset key: "{dataset_key}" (do NOT inline raw values; reference via EXTERNAL_REF markers).

        Dataset Schema:
        {schema_json}

        Dataset Preview (head, summary):
        {preview_json}

        Conversation History (latest last):
        {history_json}

        Requirements:
          1. Follow user modifications or corrections implied by the latest messages.
          2. Do not include raw data arrays in traces; instead use placeholders like
             EXTERNAL_REF::{dataset_key}::column_name.
          3. Ensure any auxiliary references (shapes, annotations, etc.) also use keys
             provided in "metadata".
          4. Response must be valid JSON without extra commentary.
        """
    ).strip()

    system_ko = dedent(
        f"""
        당신은 Plotly.js 스펙을 작성하는 전문가입니다. 반드시 JSON만 응답하세요.

        데이터 출처:
          - 업로드된 엑셀 파일을 파싱한 결과입니다.
          - 데이터셋 키: "{dataset_key}" (실제 값을 인라인하지 말고 EXTERNAL_REF 표기법으로 참조하세요)

        데이터셋 스키마:
        {schema_json}

        데이터 미리보기(head, 통계 요약 등):
        {preview_json}

        이전 대화 이력(최신 메시지가 마지막):
        {history_json}

        지침:
          1. 최신 메시지에 포함된 수정/요청 사항이 있다면 반드시 반영하세요.
          2. raw 데이터 배열을 trace에 직접 넣지 말고
             EXTERNAL_REF::{dataset_key}::컬럼명 형태로 참조하세요.
          3. shapes, annotations 등 보조 요소도 metadata에 정의된 키만 사용하세요.
          4. JSON 외의 설명 문구는 절대 포함하지 마세요.
        """
    ).strip()

    return {"en": system_en, "ko": system_ko}


def build_bar_chart_prompt(
    dataset_key: str,
    dataset_schema: Dict[str, Any],
    dataset_preview: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    user_prompt_en: str,
    user_prompt_ko: str,
) -> PromptContext:
    """Prompt and skeleton for a grouped bar graph spec."""
    system_prompts = _build_system_prompts(
        dataset_key, dataset_schema, dataset_preview, conversation_history
    )
    user_prompt_en_full = dedent(
        f"""
        Goal: grouped bar chart specification.
        Additional user instructions:
        {user_prompt_en}

        Response format:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}}
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}"
          }}
        }}
        """
    ).strip()
    user_prompt_ko_full = dedent(
        f"""
        목표: grouped bar chart 스펙 생성.
        추가 사용자 지시사항:
        {user_prompt_ko}

        응답 형식:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}}
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}"
          }}
        }}
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "bar",
                    "name": "Current",
                    "x": f"EXTERNAL_REF::{dataset_key}::device",
                    "y": f"EXTERNAL_REF::{dataset_key}::yield_current",
                    "marker": {"color": "#1f77b4"},
                },
                {
                    "type": "bar",
                    "name": "Baseline",
                    "x": f"EXTERNAL_REF::{dataset_key}::device",
                    "y": f"EXTERNAL_REF::{dataset_key}::yield_baseline",
                    "marker": {"color": "#ff7f0e"},
                },
            ],
            "layout": {
                "title": {"text": "Device Yield Comparison"},
                "barmode": "group",
                "xaxis": {"title": {"text": "Device"}},
                "yaxis": {"title": {"text": "Yield (%)"}},
                "legend": {"orientation": "h", "y": -0.2},
            },
            "config": {"displaylogo": False, "responsive": True},
        },
        "metadata": {"dataset_key": dataset_key},
    }
    return PromptContext(
        chart_type="bar_graph",
        system_prompt_en=system_prompts["en"],
        system_prompt_ko=system_prompts["ko"],
        user_prompt_en=user_prompt_en_full,
        user_prompt_ko=user_prompt_ko_full,
        expected_response_skeleton=skeleton,
    )


def build_line_chart_prompt(
    dataset_key: str,
    dataset_schema: Dict[str, Any],
    dataset_preview: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    user_prompt_en: str,
    user_prompt_ko: str,
    maintenance_key: str = "maintenance_events_key",
) -> PromptContext:
    """Prompt and skeleton for a multi-line trend plot."""
    system_prompts = _build_system_prompts(
        dataset_key, dataset_schema, dataset_preview, conversation_history
    )
    user_prompt_en_full = dedent(
        f"""
        Goal: multi-series line chart (time-series).
        Additional user instructions:
        {user_prompt_en}

        Response format:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}},
            "frames": []
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}",
            "auxiliary_keys": {{
              "maintenance_events": "{maintenance_key}"
            }}
          }}
        }}
        """
    ).strip()
    user_prompt_ko_full = dedent(
        f"""
        목표: 다중 시리즈 선형 차트(시계열).
        추가 사용자 지시사항:
        {user_prompt_ko}

        응답 형식:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}},
            "frames": []
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}",
            "auxiliary_keys": {{
              "maintenance_events": "{maintenance_key}"
            }}
          }}
        }}
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Series Placeholder",
                    "x": f"EXTERNAL_REF::{dataset_key}::timestamp",
                    "y": f"EXTERNAL_REF::{dataset_key}::kpi_value",
                    "customdata": f"EXTERNAL_REF::{dataset_key}::metric_unit",
                    "hovertemplate": "%{y:.2f} %{customdata}",
                }
            ],
            "layout": {
                "title": {"text": "KPI Trend"},
                "xaxis": {"title": {"text": "Timestamp"}},
                "yaxis": {"title": {"text": "KPI Value"}},
                "shapes": f"EXTERNAL_REF::{maintenance_key}",
            },
            "config": {"displaylogo": False, "scrollZoom": True},
            "frames": [],
        },
        "metadata": {
            "dataset_key": dataset_key,
            "auxiliary_keys": {"maintenance_events": maintenance_key},
        },
    }
    return PromptContext(
        chart_type="line_graph",
        system_prompt_en=system_prompts["en"],
        system_prompt_ko=system_prompts["ko"],
        user_prompt_en=user_prompt_en_full,
        user_prompt_ko=user_prompt_ko_full,
        expected_response_skeleton=skeleton,
    )


def build_box_plot_prompt(
    dataset_key: str,
    dataset_schema: Dict[str, Any],
    dataset_preview: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    user_prompt_en: str,
    user_prompt_ko: str,
) -> PromptContext:
    """Prompt and skeleton for a grouped box plot."""
    system_prompts = _build_system_prompts(
        dataset_key, dataset_schema, dataset_preview, conversation_history
    )
    user_prompt_en_full = dedent(
        f"""
        Goal: grouped box plot comparing device distributions.
        Additional user instructions:
        {user_prompt_en}

        Response format:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}}
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}"
          }}
        }}
        """
    ).strip()
    user_prompt_ko_full = dedent(
        f"""
        목표: 디바이스별 분포를 비교하는 박스플롯.
        추가 사용자 지시사항:
        {user_prompt_ko}

        응답 형식:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}}
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}"
          }}
        }}
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "box",
                    "name": "Device Placeholder",
                    "x": f"EXTERNAL_REF::{dataset_key}::device",
                    "y": f"EXTERNAL_REF::{dataset_key}::value",
                    "marker": {"color": "#636efa"},
                    "customdata": f"EXTERNAL_REF::{dataset_key}::wafer_count",
                    "hovertemplate": "Device: %{x}<br>Value: %{y:.2f}<br>Wafers: %{customdata}<extra></extra>",
                }
            ],
            "layout": {
                "title": {"text": "Parameter Distribution by Device"},
                "yaxis": {"title": {"text": "Measurement"}},
                "boxmode": "group",
                "margin": {
                    "l": 80,
                    "r": 80,
                    "t": 100,
                    "b": 120,
                    "pad": 10
                },
                "autosize": True,
                "shapes": [
                    {
                        "type": "line",
                        "xref": "paper",
                        "yref": "y",
                        "x0": 0,
                        "x1": 1,
                        "y0": "EXTERNAL_REF::spec_values::USL",
                        "y1": "EXTERNAL_REF::spec_values::USL",
                        "line": {"color": "rgba(255, 0, 0, 0.6)", "width": 2, "dash": "dash"},
                        "name": "USL"
                    },
                    {
                        "type": "line",
                        "xref": "paper",
                        "yref": "y",
                        "x0": 0,
                        "x1": 1,
                        "y0": "EXTERNAL_REF::spec_values::LSL",
                        "y1": "EXTERNAL_REF::spec_values::LSL",
                        "line": {"color": "rgba(255, 0, 0, 0.6)", "width": 2, "dash": "dash"},
                        "name": "LSL"
                    },
                    {
                        "type": "line",
                        "xref": "paper",
                        "yref": "y",
                        "x0": 0,
                        "x1": 1,
                        "y0": "EXTERNAL_REF::spec_values::TGT",
                        "y1": "EXTERNAL_REF::spec_values::TGT",
                        "line": {"color": "rgba(0, 128, 0, 0.8)", "width": 2, "dash": "solid"},
                        "name": "TGT"
                    }
                ],
                "annotations": [
                    {
                        "showarrow": False,
                        "text": "Spec lines: USL (red dash), LSL (red dash), TGT (green solid)",
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": -0.15,
                        "xanchor": "center",
                        "font": {"size": 10, "color": "#666"}
                    }
                ],
            },
            "config": {"displaylogo": False, "responsive": True},
        },
        "metadata": {
            "dataset_key": dataset_key,
            "spec_values": {
                "USL": "EXTERNAL_REF::spec_key::USL",
                "LSL": "EXTERNAL_REF::spec_key::LSL",
                "TGT": "EXTERNAL_REF::spec_key::TGT"
            }
        },
    }
    return PromptContext(
        chart_type="box_plot",
        system_prompt_en=system_prompts["en"],
        system_prompt_ko=system_prompts["ko"],
        user_prompt_en=user_prompt_en_full,
        user_prompt_ko=user_prompt_ko_full,
        expected_response_skeleton=skeleton,
    )


def build_scatter_plot_prompt(
    dataset_key: str,
    dataset_schema: Dict[str, Any],
    dataset_preview: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    user_prompt_en: str,
    user_prompt_ko: str,
) -> PromptContext:
    """Prompt and skeleton for a scatter plot (optionally colored/sized)."""
    system_prompts = _build_system_prompts(
        dataset_key, dataset_schema, dataset_preview, conversation_history
    )
    user_prompt_en_full = dedent(
        f"""
        Goal: scatter plot illustrating relationships between columns.
        Additional user instructions:
        {user_prompt_en}

        Response format:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}}
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}"
          }}
        }}
        """
    ).strip()
    user_prompt_ko_full = dedent(
        f"""
        목표: 컬럼 간 관계를 보여주는 산점도(scatter plot)를 생성.
        추가 사용자 지시사항:
        {user_prompt_ko}

        응답 형식:
        {{
          "figure": {{
            "data": [...],
            "layout": {{...}},
            "config": {{...}}
          }},
          "metadata": {{
            "dataset_key": "{dataset_key}"
          }}
        }}
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Scatter Series",
                    "x": f"EXTERNAL_REF::{dataset_key}::x_value",
                    "y": f"EXTERNAL_REF::{dataset_key}::y_value",
                    "marker": {
                        "color": f"EXTERNAL_REF::{dataset_key}::category",
                        "size": f"EXTERNAL_REF::{dataset_key}::size_metric",
                        "sizemode": "area",
                        "sizeref": 2.0,
                    },
                    "customdata": f"EXTERNAL_REF::{dataset_key}::tooltip",
                    "hovertemplate": "%{x}, %{y}<br>%{customdata}<extra></extra>",
                }
            ],
            "layout": {
                "title": {"text": "Scatter Plot"},
                "xaxis": {"title": {"text": "X Axis"}},
                "yaxis": {"title": {"text": "Y Axis"}},
            },
            "config": {"displaylogo": False},
        },
        "metadata": {"dataset_key": dataset_key},
    }

    return PromptContext(
        chart_type="scatter_plot",
        system_prompt_en=system_prompts["en"],
        system_prompt_ko=system_prompts["ko"],
        user_prompt_en=user_prompt_en_full,
        user_prompt_ko=user_prompt_ko_full,
        expected_response_skeleton=skeleton,
    )


def request_plotly_spec(prompt: str) -> Dict[str, Any]:
    """
    Example HTTP call to the locally served Gemma model. Adjust the payload to
    match your inference server contract.
    """
    payload: Dict[str, Any] = {
        "model": "gemma-3-27b-it",
        "messages": [
            {"role": "system", "content": "You produce Plotly.js figure JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
    }

    response = requests.post(GEMMA_ENDPOINT, json=payload, timeout=60)
    response.raise_for_status()
    body = response.json()

    # Adjust if your server schema differs (below assumes OpenAI-compatible API).
    content = body["choices"][0]["message"]["content"]
    return json.loads(content)


_EXAMPLE_SCHEMA_BAR = {
    "dataset_key": "device_yield_summary",
    "columns": {
        "device": "string",
        "yield_current": "float",
        "yield_baseline": "float",
        "lot_count": "integer",
    },
    "row_count": 128,
    "source": "uploaded_excel/device_yield_summary.xlsx",
}

_EXAMPLE_SCHEMA_LINE = {
    "dataset_key": "kpi_timeseries",
    "columns": {
        "timestamp": "datetime",
        "kpi_value": "float",
        "series_label": "string",
        "metric_unit": "string",
    },
    "row_count": 720,
    "source": "uploaded_excel/kpi_export.xlsx",
}

_EXAMPLE_SCHEMA_BOX = {
    "dataset_key": "param_distribution",
    "columns": {
        "device": "string",
        "value": "float",
        "wafer_count": "integer",
    },
    "row_count": 256,
    "source": "uploaded_excel/param_distribution.csv",
}

# Example preview data (head, stats)
_EXAMPLE_PREVIEW_BAR = {
    "head": [
        {"device": "D1", "yield_current": 95.1, "yield_baseline": 91.4, "lot_count": 12},
        {"device": "D2", "yield_current": 94.8, "yield_baseline": 90.1, "lot_count": 10},
    ],
    "shape": [128, 4],
    "numeric_summary": {"yield_current": {"mean": 93.2}, "yield_baseline": {"mean": 89.5}},
}

_EXAMPLE_PREVIEW_LINE = {
    "head": [
        {
            "timestamp": "2024-01-01 00:00:00",
            "kpi_value": 10.2,
            "series_label": "Metric A",
            "metric_unit": "%",
        },
        {
            "timestamp": "2024-01-01 01:00:00",
            "kpi_value": 11.5,
            "series_label": "Metric B",
            "metric_unit": "%",
        },
    ],
    "shape": [720, 4],
    "numeric_summary": {"kpi_value": {"mean": 9.8, "std": 1.2}},
}

_EXAMPLE_PREVIEW_BOX = {
    "head": [
        {"device": "A1", "value": 1.23, "wafer_count": 42},
        {"device": "A2", "value": 1.35, "wafer_count": 38},
    ],
    "shape": [256, 3],
    "numeric_summary": {"value": {"median": 1.31, "iqr": 0.12}},
}

_EXAMPLE_SCHEMA_SCATTER = {
    "dataset_key": "correlation_points",
    "columns": {
        "x_value": "float",
        "y_value": "float",
        "category": "string",
        "size_metric": "float",
        "tooltip": "string",
    },
    "row_count": 512,
    "source": "uploaded_excel/correlation_points.xlsx",
}

_EXAMPLE_PREVIEW_SCATTER = {
    "head": [
        {
            "x_value": 1.2,
            "y_value": 3.4,
            "category": "Group A",
            "size_metric": 20.5,
            "tooltip": "Sample A",
        },
        {
            "x_value": 2.1,
            "y_value": 2.8,
            "category": "Group B",
            "size_metric": 10.0,
            "tooltip": "Sample B",
        },
    ],
    "shape": [512, 5],
    "numeric_summary": {
        "x_value": {"mean": 2.4},
        "y_value": {"mean": 3.1},
        "size_metric": {"mean": 15.0},
    },
}

_EXAMPLE_CONVERSATION = [
    {"role": "user", "content": "지난번에 만든 그래프에서 범례 순서를 바꿔주세요."},
    {"role": "assistant", "content": "범례 순서를 Current, Baseline 순으로 변경했습니다."},
]

EXAMPLE_PROMPTS: List[PromptContext] = [
    build_bar_chart_prompt(
        dataset_key="device_yield_summary",
        dataset_schema=_EXAMPLE_SCHEMA_BAR,
        dataset_preview=_EXAMPLE_PREVIEW_BAR,
        conversation_history=_EXAMPLE_CONVERSATION,
        user_prompt_en="Compare current vs baseline yield per device. Place legend below.",
        user_prompt_ko="디바이스별 현재/기준 수율을 비교하고 범례는 아래쪽에 배치해주세요.",
    ),
    build_line_chart_prompt(
        dataset_key="kpi_timeseries",
        dataset_schema=_EXAMPLE_SCHEMA_LINE,
        dataset_preview=_EXAMPLE_PREVIEW_LINE,
        conversation_history=_EXAMPLE_CONVERSATION,
        user_prompt_en="Plot KPI trend by series_label. Highlight maintenance windows.",
        user_prompt_ko="series_label별 KPI 추세를 그리고, 유지보수 기간은 강조해주세요.",
        maintenance_key="maintenance_events_key",
    ),
    build_box_plot_prompt(
        dataset_key="param_distribution",
        dataset_schema=_EXAMPLE_SCHEMA_BOX,
        dataset_preview=_EXAMPLE_PREVIEW_BOX,
        conversation_history=_EXAMPLE_CONVERSATION,
        user_prompt_en="Create box plots by device and include wafer_count in hover.",
        user_prompt_ko="디바이스별 박스플롯을 만들고 hover에 wafer_count를 보여주세요.",
    ),
    build_scatter_plot_prompt(
        dataset_key="correlation_points",
        dataset_schema=_EXAMPLE_SCHEMA_SCATTER,
        dataset_preview=_EXAMPLE_PREVIEW_SCATTER,
        conversation_history=_EXAMPLE_CONVERSATION,
        user_prompt_en="Create a scatter plot of x_value vs y_value, colored by category and sized by size_metric.",
        user_prompt_ko="x_value와 y_value를 산점도로 그리고, category로 색상을, size_metric으로 점 크기를 조절해주세요.",
    ),
]


def demo():
    """Utility to print prompts and skeletons without calling the model."""
    for prompt in EXAMPLE_PROMPTS:
        print("=" * 80)
        print(f"Chart type: {prompt.chart_type}")
        print("\nPrompt:\n")
        print(prompt.prompt)
        print("\nExpected skeleton:\n")
        print(json.dumps(prompt.expected_response_skeleton, indent=2))


if __name__ == "__main__":
    demo()


# --------------------------------------------------------------------------------------
# Backend → Frontend payload examples (without inline data)
# --------------------------------------------------------------------------------------

# 1) bar_graph
# {
#   "analysis_type": "bar_graph",
#   "file_name": "example.xlsx",
#   "graph_spec": {
#     "figure": {
#       "data": [
#         {
#           "type": "bar",
#           "name": "Current",
#           "x": "EXTERNAL_REF::device_yield_summary::device",
#           "y": "EXTERNAL_REF::device_yield_summary::yield_current"
#         },
#         {
#           "type": "bar",
#           "name": "Baseline",
#           "x": "EXTERNAL_REF::device_yield_summary::device",
#           "y": "EXTERNAL_REF::device_yield_summary::yield_baseline"
#         }
#       ],
#       "layout": {
#         "title": {"text": "Device Yield Comparison"},
#         "barmode": "group"
#       },
#       "config": {"displaylogo": false}
#     },
#     "metadata": {"dataset_key": "device_yield_summary"}
#   },
#   "real_data": [
#     "[{\"device\":\"D1\",\"yield_current\":95.1,\"yield_baseline\":91.4}]"
#   ],
#   "success_message": "현재 수율과 기준 수율을 비교한 막대 그래프입니다."
# }

# 2) line_graph
# {
#   "analysis_type": "line_graph",
#   "file_name": null,
#   "graph_spec": {
#     "figure": {
#       "data": [
#         {
#           "type": "scatter",
#           "mode": "lines+markers",
#           "name": "Metric A",
#           "x": "EXTERNAL_REF::kpi_timeseries::timestamp",
#           "y": "EXTERNAL_REF::kpi_timeseries::kpi_value"
#         }
#       ],
#       "layout": {"title": {"text": "KPI Trend"}},
#       "config": {"scrollZoom": true}
#     },
#     "metadata": {
#       "dataset_key": "kpi_timeseries",
#       "auxiliary_keys": {"maintenance_events": "maintenance_events_key"}
#     }
#   },
#   "real_data": [
#     "[{\"timestamp\":\"2024-01-01\",\"kpi_value\":10.2,\"series_label\":\"Metric A\"}]"
#   ],
#   "success_message": "KPI 추세를 시간 순으로 비교했습니다."
# }

# 3) box_plot
# {
#   "analysis_type": "box_plot",
#   "file_name": "distribution.csv",
#   "graph_spec": {
#     "figure": {
#       "data": [
#         {
#           "type": "box",
#           "name": "Device Group 1",
#           "x": "EXTERNAL_REF::param_distribution::device",
#           "y": "EXTERNAL_REF::param_distribution::value"
#         }
#       ],
#       "layout": {"title": {"text": "Parameter Distribution by Device"}},
#       "config": {}
#     },
#     "metadata": {"dataset_key": "param_distribution"}
#   },
#   "real_data": [
#     "[{\"device\":\"G1\",\"value\":1.23,\"wafer_count\":42}]"
#   ],
#   "success_message": "디바이스별 분포를 박스플롯으로 나타냈습니다."
# }

# 4) general_text
# {
#   "analysis_type": "general_text",
#   "file_name": null,
#   "success_message": "데이터 품질 점검 결과 이상 징후가 발견되지 않았습니다.",
#   "summary": "최근 7일 간 KPI 편차는 ±2% 범위 내에 머물렀습니다.",
#   "real_data": []
# }

# 5) table
# {
#   "analysis_type": "table",
#   "file_name": "summary.xlsx",
#   "real_data": [
#     "[{\"device\":\"D1\",\"lot\":\"L001\",\"status\":\"PASS\"}]",
#     "[{\"device\":\"D2\",\"lot\":\"L004\",\"status\":\"REVIEW\"}]"
#   ],
#   "success_message": "검증 대상 로트 목록을 정리했습니다."
# }

# 6) scatter_plot
# {
#   "analysis_type": "scatter_plot",
#   "file_name": "scatter.xlsx",
#   "graph_spec": {
#     "figure": {
#       "data": [
#         {
#           "type": "scatter",
#           "mode": "markers",
#           "name": "Scatter Series",
#           "x": "EXTERNAL_REF::correlation_points::x_value",
#           "y": "EXTERNAL_REF::correlation_points::y_value",
#           "marker": {
#             "color": "EXTERNAL_REF::correlation_points::category",
#             "size": "EXTERNAL_REF::correlation_points::size_metric",
#             "sizemode": "area"
#           },
#           "customdata": "EXTERNAL_REF::correlation_points::tooltip",
#           "hovertemplate": "%{x}, %{y}<br>%{customdata}<extra></extra>"
#         }
#       ],
#       "layout": {
#         "title": {"text": "Scatter Plot"},
#         "xaxis": {"title": {"text": "X Axis"}},
#         "yaxis": {"title": {"text": "Y Axis"}}
#       },
#       "config": {"displaylogo": false}
#     },
#     "metadata": {"dataset_key": "correlation_points"}
#   },
#   "real_data": [
#     "[{\"x_value\":1.2,\"y_value\":3.4,\"category\":\"Group A\",\"size_metric\":20.5,\"tooltip\":\"Sample A\"}]"
#   ],
#   "success_message": "산점도를 통해 두 변수 간 상관 관계를 시각화했습니다."
# }
