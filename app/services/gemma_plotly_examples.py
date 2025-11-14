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
class PlotlyPrompt:
    chart_type: str
    prompt: str
    expected_response_skeleton: Dict[str, Any]


def build_bar_chart_prompt() -> PlotlyPrompt:
    """Prompt and skeleton for a grouped bar graph spec."""
    prompt = dedent(
        """
        You are a Plotly.js specialist. Produce ONLY valid JSON.

        Goal: grouped bar chart specification.
        Data source: do NOT inline the data array. Instead, refer to an external
        dataset key called "dataset_key". The frontend will join traces with
        the actual rows by this key at runtime.

        Requirements:
          - use layout.title.text == "Device Yield Comparison".
          - xaxis.title.text == "Device".
          - yaxis.title.text == "Yield (%)".
          - Provide two bar traces referencing fields "device" and
            "yield_current" / "yield_baseline" in the dataset.
          - Include legend grouped on trace names "Current" and "Baseline".

        Response format:
        {
          "figure": {
            "data": [...],
            "layout": {...},
            "config": {...}
          },
          "metadata": {
            "dataset_key": "string identifying the external dataset"
          }
        }
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "bar",
                    "name": "Current",
                    "x": "EXTERNAL_REF::dataset_key::device",
                    "y": "EXTERNAL_REF::dataset_key::yield_current",
                    "marker": {"color": "#1f77b4"},
                },
                {
                    "type": "bar",
                    "name": "Baseline",
                    "x": "EXTERNAL_REF::dataset_key::device",
                    "y": "EXTERNAL_REF::dataset_key::yield_baseline",
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
        "metadata": {"dataset_key": "device_yield_summary"},
    }
    return PlotlyPrompt(chart_type="bar_graph", prompt=prompt, expected_response_skeleton=skeleton)


def build_line_chart_prompt() -> PlotlyPrompt:
    """Prompt and skeleton for a multi-line trend plot."""
    prompt = dedent(
        """
        You are a Plotly.js specialist. Produce ONLY valid JSON.

        Goal: multi-series line chart showing KPI trends over time.
        Data source: external dataset key "kpi_timeseries". Do not inline raw data.

        Requirements:
          - Show two traces for columns "timestamp" vs "kpi_value" grouped by
            the column "series_label".
          - Use scatter traces with mode "lines+markers".
          - Provide hovertemplate referencing %{customdata.metric_unit}.
          - Add vertical line shapes for maintenance windows provided via an
            external array "maintenance_events" (do not inline coordinates; just
            reference the key).
          - Layout.title.text == "KPI Trend".

        Response format:
        {
          "figure": {
            "data": [...],
            "layout": {...},
            "config": {...},
            "frames": []
          },
          "metadata": {
            "dataset_key": "kpi_timeseries",
            "auxiliary_keys": {
              "maintenance_events": "maintenance_events_key"
            }
          }
        }
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Series Placeholder",
                    "x": "EXTERNAL_REF::kpi_timeseries::timestamp",
                    "y": "EXTERNAL_REF::kpi_timeseries::kpi_value",
                    "customdata": "EXTERNAL_REF::kpi_timeseries::metric_unit",
                    "hovertemplate": "%{y:.2f} %{customdata}",
                }
            ],
            "layout": {
                "title": {"text": "KPI Trend"},
                "xaxis": {"title": {"text": "Timestamp"}},
                "yaxis": {"title": {"text": "KPI Value"}},
                "shapes": "EXTERNAL_REF::maintenance_events_key",
            },
            "config": {"displaylogo": False, "scrollZoom": True},
            "frames": [],
        },
        "metadata": {
            "dataset_key": "kpi_timeseries",
            "auxiliary_keys": {"maintenance_events": "maintenance_events_key"},
        },
    }
    return PlotlyPrompt(chart_type="line_graph", prompt=prompt, expected_response_skeleton=skeleton)


def build_box_plot_prompt() -> PlotlyPrompt:
    """Prompt and skeleton for a grouped box plot."""
    prompt = dedent(
        """
        You are a Plotly.js specialist. Produce ONLY valid JSON.

        Goal: grouped box plot comparing parameter distributions across devices.
        Data source: external dataset key "param_distribution".

        Requirements:
          - Do not inline data arrays.
          - Each box trace should reference fields "device" and "value".
          - Use color per device via Plotly template, but you may specify marker.color.
          - Add annotations describing the number of wafers per device from the
            field "wafer_count".
          - Layout.boxmode == "group".

        Response format:
        {
          "figure": {
            "data": [...],
            "layout": {...},
            "config": {...}
          },
          "metadata": {
            "dataset_key": "param_distribution"
          }
        }
        """
    ).strip()

    skeleton = {
        "figure": {
            "data": [
                {
                    "type": "box",
                    "name": "Device Placeholder",
                    "x": "EXTERNAL_REF::param_distribution::device",
                    "y": "EXTERNAL_REF::param_distribution::value",
                    "marker": {"color": "#636efa"},
                    "customdata": "EXTERNAL_REF::param_distribution::wafer_count",
                    "hovertemplate": "Device: %{x}<br>Value: %{y:.2f}<br>Wafers: %{customdata}<extra></extra>",
                }
            ],
            "layout": {
                "title": {"text": "Parameter Distribution by Device"},
                "yaxis": {"title": {"text": "Measurement"}},
                "boxmode": "group",
                "annotations": [
                    {
                        "showarrow": False,
                        "text": "Annotations reference wafer counts",
                        "xref": "paper",
                        "yref": "paper",
                        "x": 1.02,
                        "y": 1,
                    }
                ],
            },
            "config": {"displaylogo": False},
        },
        "metadata": {"dataset_key": "param_distribution"},
    }
    return PlotlyPrompt(chart_type="box_plot", prompt=prompt, expected_response_skeleton=skeleton)


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


EXAMPLE_PROMPTS: List[PlotlyPrompt] = [
    build_bar_chart_prompt(),
    build_line_chart_prompt(),
    build_box_plot_prompt(),
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
