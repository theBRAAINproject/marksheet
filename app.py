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
# st.title("University Generative AI Policy Grading Tool")
# st.sidebar.caption("5-point grading protocol loaded from GradingProtocol-5point.xlsx")

row = protocol.iloc[st.session_state.index]
metric = row.Metric
st.subheader(f"Metric {st.session_state.index + 1} of {len(protocol)}: {metric}")


# with st.expander("Metric definition", expanded=True):
st.markdown(row["Metric Defination"])

# with st.expander("Rating guidance (0–5)", expanded=False):
guidance_data = {
    # "Rating": ["5", "4", "3", "2", "1", "0"],
    "Rating": ["Rating 5", "Rating 4", "Rating 3", "Rating 2", "Rating 1", "Rating 0"],
    "Description": [
        row["Rating 5 (max positive)"],
        row["Rating 4"],
        row["Rating 3"],
        row["Rating 2"],
        row["Rating 1"],
        row["Rating 0 (N/A or absent)"]
    ]
}
guidance_df = pd.DataFrame(guidance_data)
st.dataframe(guidance_df, use_container_width=True, hide_index=True)

# Rating selector
rating_columns = [
    "Rating 5 (max positive)",
    "Rating 4",
    "Rating 3",
    "Rating 2",
    "Rating 1",
    "Rating 0 (N/A or absent)"
]
rating_values = [5, 4, 3, 2, 1, 0]
rating_labels = [f"{val} - {row[col][:50]}..." if len(row[col]) > 50 else f"{val} - {row[col]}" 
                 for val, col in zip(rating_values, rating_columns)]

rating = st.selectbox(
    "Select rating",
    options=rating_values,
    format_func=lambda x: rating_labels[rating_values.index(x)],
    index=None,
    placeholder="Choose a rating..."
)

if rating is not None:
    st.session_state.responses[metric]["rating"] = rating
else:
    st.session_state.responses[metric]["rating"] = None

# Evidence text
st.text_area(
    "Paste relevant policy text (editable)",
    key=f"evidence_{metric}",
    value=st.session_state.responses[metric]["evidence"],
    height=160
)

st.session_state.responses[metric]["evidence"] = st.session_state.get(f"evidence_{metric}", "")

# Notes
# st.text_area(
#     "Evaluator notes / justification",
#     key=f"notes_{metric}",
#     value=st.session_state.responses[metric]["notes"],
#     height=110
# )

st.session_state.responses[metric]["notes"] = st.session_state.get(f"notes_{metric}", "")

# Navigation
selected_rating = st.session_state.responses[metric]["rating"]
evidence_text = (st.session_state.responses[metric]["evidence"] or "").strip()
next_disabled = (
    st.session_state.index == len(protocol) - 1
    or selected_rating is None
    or evidence_text == ""
)

col1, col2, col3 = st.columns([1, 4, 2])
with col1:
    st.button("⬅ Back", on_click=prev_metric, disabled=st.session_state.index == 0)
with col2:
    st.button("Next ➡", on_click=next_metric, disabled=next_disabled)

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