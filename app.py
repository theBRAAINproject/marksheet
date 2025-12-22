import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os

# -----------------------------
# Load grading protocols
# -----------------------------
@st.cache_data
def load_protocol_5point():
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
    # Normalize metric names - strip regular and non-breaking spaces
    df["Metric"] = df["Metric"].str.replace('\xa0', ' ').str.strip()
    return df

@st.cache_data
def load_protocol_2point():
    df = pd.read_excel("data/GradingProtocol-2point.xlsx")
    df = df.dropna(subset=["Metric"])
    # Normalize metric names - strip regular and non-breaking spaces
    df["Metric"] = df["Metric"].str.replace('\xa0', ' ').str.strip()
    return df

# -----------------------------
# Session State
# -----------------------------
if "protocol_type" not in st.session_state:
    st.session_state.protocol_type = "2-point"  # Always start with 2-point
if "completed_2point" not in st.session_state:
    st.session_state.completed_2point = False
if "results_2point" not in st.session_state:
    st.session_state.results_2point = {}
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
    st.session_state.responses = {}

# -----------------------------
# Navigation helpers
# -----------------------------
def next_metric():
    protocol = load_protocol_5point() if st.session_state.protocol_type == "5-point" else load_protocol_2point()
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
    
    # Show which protocol they're about to complete - only for initial start
    if not st.session_state.completed_2point:
        st.info("📋 Step 1 of 2: You will first complete the 2-point grading protocol.")
        
        st.session_state.grader_name = st.text_input("Grader's initials", value=st.session_state.grader_name)
        st.session_state.document_name = st.text_input("Document name", value=st.session_state.document_name)
        st.session_state.tag = st.text_input("Tag (optional)", value=st.session_state.tag)
        
        start_disabled = not (
            st.session_state.grader_name.strip() and 
            st.session_state.document_name.strip()
        )
        
        if st.button("Start 2-point grading", disabled=start_disabled, type="primary"):
            # Initialize responses based on current protocol
            protocol = load_protocol_2point()
            st.session_state.responses = {
                row.Metric: {
                    "rating": None,
                    "evidence": "",
                    "notes": ""
                }
                for _, row in protocol.iterrows()
            }
            st.session_state.index = 0
            st.session_state.started = True
            st.rerun()
    else:
        # Automatically initialize 5-point grading without showing setup screen
        protocol = load_protocol_5point()
        st.session_state.responses = {
            row.Metric: {
                "rating": None,
                "evidence": "",
                "notes": ""
            }
            for _, row in protocol.iterrows()
        }
        st.session_state.index = 0
        st.session_state.started = True
        st.rerun()
    
    st.stop()

# Load the selected protocol
protocol = load_protocol_5point() if st.session_state.protocol_type == "5-point" else load_protocol_2point()

row = protocol.iloc[st.session_state.index]
metric = row.Metric

# Show progress indicator
protocol_name = "2-point" if st.session_state.protocol_type == "2-point" else "5-point"
st.caption(f"Protocol: {protocol_name} grading")
st.subheader(f"Metric {st.session_state.index + 1} of {len(protocol)}: {metric}")

st.markdown(row["Metric Defination"])

# Display rating guidance based on protocol type
if st.session_state.protocol_type == "5-point":
    rating_columns = [
        "Rating 5 (max positive)",
        "Rating 4",
        "Rating 3",
        "Rating 2",
        "Rating 1",
        "Rating 0 (N/A or absent)"
    ]
    rating_values = [5, 4, 3, 2, 1, 0]
else:  # 2-point
    # Dynamically determine rating columns from the protocol
    available_cols = [col for col in protocol.columns if col.startswith("Rating")]
    if not available_cols:
        st.error("No rating columns found in 2-point protocol")
        st.stop()
    
    # Sort by rating value (extract number from column name)
    rating_columns = sorted(available_cols, key=lambda x: int(''.join(filter(str.isdigit, x.split()[1]))), reverse=True)
    rating_values = [int(''.join(filter(str.isdigit, col.split()[1]))) for col in rating_columns]

guidance_data = {
    "Rating": rating_columns,
    "Description": [str(row[col]) if pd.notna(row[col]) else "" for col in rating_columns]
}
guidance_df = pd.DataFrame(guidance_data)
st.dataframe(guidance_df, use_container_width=True, hide_index=True)

# Rating selector
rating_labels = []
for val, col in zip(rating_values, rating_columns):
    desc = str(row[col]) if pd.notna(row[col]) else ""
    label = f"{val} - {desc[:50]}..." if len(desc) > 50 else f"{val} - {desc}"
    rating_labels.append(label)

stored_rating = st.session_state.responses[metric]["rating"]
rating_index = rating_values.index(stored_rating) if stored_rating in rating_values else None

rating = st.selectbox(
    "Select rating",
    options=rating_values,
    format_func=lambda x: rating_labels[rating_values.index(x)],
    index=rating_index,
    placeholder="Choose a rating...",
    key=f"rating_{metric}"
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

st.session_state.responses[metric]["notes"] = st.session_state.get(f"notes_{metric}", "")

# Navigation
selected_rating = st.session_state.responses[metric]["rating"]
evidence_text = (st.session_state.responses[metric]["evidence"] or "").strip()
next_disabled = (
    st.session_state.index == len(protocol) - 1
    or selected_rating is None
    or evidence_text == ""
)

# Change button text based on protocol completion status
if st.session_state.protocol_type == "2-point":
    save_button_text = "Complete 2-point & Continue"
else:
    save_button_text = "Create Final Evaluation Log"

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
    save_clicked = st.button(save_button_text, disabled=save_disabled, type="primary")

# -----------------------------
# Save JSON
# -----------------------------
if st.session_state.index == len(protocol) - 1:
    st.markdown("---")
    if save_clicked:
        # Check if we need to proceed to 5-point grading
        if st.session_state.protocol_type == "2-point" and not st.session_state.completed_2point:
            # Save 2-point results temporarily
            st.session_state.results_2point = st.session_state.responses.copy()
            st.session_state.completed_2point = True
            st.session_state.protocol_type = "5-point"
            st.session_state.started = False
            st.session_state.index = 0
            # Clear widget states
            for k in [k for k in list(st.session_state.keys()) if k.startswith(("evidence_", "notes_", "rating_"))]:
                del st.session_state[k]
            st.success("✅ 2-point grading complete!")
            st.rerun()
        else:
            # Create merged output with both 2-point and 5-point results
            output = {
                "metadata": {
                    "date": datetime.utcnow().isoformat(),
                    "protocols": ["GradingProtocol-2point.xlsx", "GradingProtocol-5point.xlsx"],
                    "grader_name": st.session_state.grader_name,
                    "document_name": st.session_state.document_name,
                    "tag": st.session_state.tag or None,
                },
                "results": {
                    "2-point": st.session_state.results_2point,
                    "5-point": st.session_state.responses
                }
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
            st.success(f"✅ Complete! Merged log file created: {filename}")
            st.download_button(
                "Download Merged Evaluation Log",
                data=json.dumps(output, indent=2),
                file_name=filename,
                mime="application/json",
                type="primary"
            )

#restart evaluation
st.markdown("---")
with st.expander("Session controls", expanded=False):
    if st.button("🔄 Restart Evaluation"):
        # clear widget states for metric-bound inputs
        for k in [k for k in list(st.session_state.keys()) if k.startswith(("evidence_", "notes_", "rating_"))]:
            del st.session_state[k]
        # reset responses to pristine state
        st.session_state.responses = {}
        st.session_state.results_2point = {}
        # reset metadata and navigation
        st.session_state.grader_name = ""
        st.session_state.document_name = ""
        st.session_state.tag = ""
        st.session_state.protocol_type = "2-point"
        st.session_state.completed_2point = False
        st.session_state.index = 0
        st.session_state.started = False
        st.success("Session reset.")
        st.rerun()