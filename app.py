import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os

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
if "grader_name" not in st.session_state:
    st.session_state.grader_name = ""
if "document_name" not in st.session_state:
    st.session_state.document_name = ""
if "tag" not in st.session_state:
    st.session_state.tag = ""
if "started" not in st.session_state:
    st.session_state.started = False

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
if not st.session_state.started:
    st.title("Grading Setup")
    st.session_state.grader_name = st.text_input("Grader name", value=st.session_state.grader_name)
    st.session_state.document_name = st.text_input("Document name", value=st.session_state.document_name)
    st.session_state.tag = st.text_input("Tag (optional)", value=st.session_state.tag)
    start_disabled = not (
        st.session_state.grader_name.strip() and st.session_state.document_name.strip()
    )
    if st.button("Start grading", disabled=start_disabled, type="primary"):
        st.session_state.index = 0
        st.session_state.started = True
    st.stop()

row = protocol.iloc[st.session_state.index]
metric = row.Metric
st.subheader(f"Metric {st.session_state.index + 1} of {len(protocol)}: {metric}")


# with st.expander("Metric definition", expanded=True):
st.markdown(row["Metric Defination"])

# with st.expander("Rating guidance (0–5)", expanded=False):
guidance_data = {
    # "Rating": ["5", "4", "3", "2", "1", "0"],
    "Rating": ["Rating 5 (max positive)", "Rating 4", "Rating 3", "Rating 2", "Rating 1", "Rating 0 (N/A or absent)"],
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

stored_rating = st.session_state.responses[metric]["rating"]
rating_index = rating_values.index(stored_rating) if stored_rating in rating_values else None

rating = st.selectbox(
    "Select rating",
    options=rating_values,
    format_func=lambda x: rating_labels[rating_values.index(x)],
    index=rating_index,
    placeholder="Choose a rating...",
    key=f"rating_{metric}"  # ensure widget state is per-metric and resettable
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
save_disabled = (
    st.session_state.index != len(protocol) - 1
    or selected_rating is None
    or evidence_text == ""
)
save_clicked = False

col1, col2, col3 = st.columns([1, 4, 2])
with col1:
    st.button("⬅ Back", on_click=prev_metric, disabled=st.session_state.index == 0)
with col2:
    st.button("Next ➡", on_click=next_metric, disabled=next_disabled)
with col3:
    save_clicked = st.button("💾 Create Evaluation log file", disabled=save_disabled, type="primary")

# -----------------------------
# Save JSON
# -----------------------------
if st.session_state.index == len(protocol) - 1:
    st.markdown("---")
    if save_clicked:
        output = {
            "metadata": {
                "date": datetime.utcnow().isoformat(),
                "protocol": "GradingProtocol-5point.xlsx",
                "grader_name": st.session_state.grader_name,
                "document_name": st.session_state.document_name,
                "tag": st.session_state.tag or None,
            },
            "results": st.session_state.responses
        }
        os.makedirs("outputs", exist_ok=True)
        safe = lambda s: ("".join(ch if ch.isalnum() else "_" for ch in s.strip())) or "unnamed"
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename_parts = []
        if st.session_state.tag.strip():
            filename_parts.append(safe(st.session_state.tag))
        filename_parts.extend([safe(st.session_state.grader_name), safe(st.session_state.document_name), timestamp])
        filename = f"outputs/{'_'.join(filename_parts)}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        st.success(f"File created: {filename}")
        st.download_button(
            "Download JSON",
            data=json.dumps(output, indent=2),
            file_name=filename,
            mime="application/json"
        )


#restart evaluation
st.markdown("---")
with st.expander("Session controls", expanded=False):
    if st.button("🔄 Restart Evaluation"):
        # clear widget states for metric-bound inputs
        for k in [k for k in list(st.session_state.keys()) if k.startswith(("evidence_", "notes_", "rating_"))]:
            del st.session_state[k]
        # reset responses to pristine state
        st.session_state.responses = {
            row.Metric: {"rating": None, "evidence": "", "notes": ""}
            for _, row in protocol.iterrows()
        }
        # reset metadata and navigation
        st.session_state.grader_name = ""
        st.session_state.document_name = ""
        st.session_state.tag = ""
        st.session_state.index = 0
        st.session_state.started = False
        st.success("Session reset.")
        st.rerun()