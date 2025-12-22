import streamlit as st
import json
import pandas as pd
from datetime import datetime

# -----------------------------
# Load grading protocol (5-point + 0)
# -----------------------------
@st.cache_data

def load_protocol():
    df = pd.read_excel("data/GradingProtocol-5point.xlsx")
    df = df[[
        "Metric",
        "Metric Defination",
        "Rating 5 (max positive)",
        "Rating 4",
        "Rating 3",
        "Rating 2",
        "Rating 1",
        "Rating 0 (N/A or absent)"
    ]]
    df = df.dropna(subset=["Metric"])
    return df


# Metric	Metric Defination		Rating 5 (max positive)	Rating 4	Rating 3	Rating 2	Rating 1	
protocol = load_protocol()

# -----------------------------
# Session State
# -----------------------------
if "index" not in st.session_state:
    st.session_state.index = 0

if "responses" not in st.session_state:
    st.session_state.responses = {
        row.Metric: {
            "rating": None,
            "evidence": "",
            "notes": ""
        }
        for _, row in protocol.iterrows()
    }

# -----------------------------
# Navigation helpers
# -----------------------------

def next_metric():
    if st.session_state.index < len(protocol) - 1:
        st.session_state.index += 1


def prev_metric():
    if st.session_state.index > 0:
        st.session_state.index -= 1

# -----------------------------
# UI
# -----------------------------
st.title("University Generative AI Policy Grading Tool")
st.caption("5-point grading protocol loaded from GradingProtocol-5point.xlsx")

row = protocol.iloc[st.session_state.index]
metric = row.Metric

st.subheader(f"Metric {st.session_state.index + 1} of {len(protocol)}")
st.markdown(f"### {metric}")

with st.expander("Metric definition", expanded=True):
    st.markdown(row["Metric Defination"])

with st.expander("Rating guidance (0–5)", expanded=False):
    st.markdown("**5 — Exemplary / max positive**")
    st.markdown(row["Rating 5 (max positive)"])
    st.markdown("**4 — Strong**")
    st.markdown(row["Rating 4"])
    st.markdown("**3 — Adequate**")
    st.markdown(row["Rating 3"])
    st.markdown("**2 — Weak**")
    st.markdown(row["Rating 2"])
    st.markdown("**1 — Problematic**")
    st.markdown(row["Rating 1"])
    st.markdown("**0 — N/A or Absent**")
    st.markdown(row["Rating 0, (N/A or absent)"])

# Rating selector
rating_options = [5, 4, 3, 2, 1, 0]

rating = st.radio(
    "Select rating",
    rating_options,
    index=(rating_options.index(st.session_state.responses[metric]["rating"])
           if st.session_state.responses[metric]["rating"] is not None else 0)
)

st.session_state.responses[metric]["rating"] = rating

# Evidence text
st.text_area(
    "Paste relevant policy text (editable)",
    key=f"evidence_{metric}",
    value=st.session_state.responses[metric]["evidence"],
    height=160
)

st.session_state.responses[metric]["evidence"] = st.session_state.get(f"evidence_{metric}", "")

# Notes
st.text_area(
    "Evaluator notes / justification",
    key=f"notes_{metric}",
    value=st.session_state.responses[metric]["notes"],
    height=110
)

st.session_state.responses[metric]["notes"] = st.session_state.get(f"notes_{metric}", "")

# Navigation
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.button("⬅ Back", on_click=prev_metric, disabled=st.session_state.index == 0)
with col2:
    st.button("Next ➡", on_click=next_metric, disabled=st.session_state.index == len(protocol) - 1)

# -----------------------------
# Save JSON
# -----------------------------
if st.session_state.index == len(protocol) - 1:
    st.markdown("---")
    if st.button("💾 Save Evaluation"):
        output = {
            "metadata": {
                "date": datetime.utcnow().isoformat(),
                "protocol": "GradingProtocol-5point.xlsx"
            },
            "results": st.session_state.responses
        }

        st.download_button(
            "Download JSON",
            data=json.dumps(output, indent=2),
            file_name="genai_policy_grading.json",
            mime="application/json"
        )