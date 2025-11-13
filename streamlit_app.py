import re
import streamlit as st
import httpx
import base64
import asyncio
import websockets
import json
import uuid
import os
import shutil
from pathlib import Path
from typing import Optional
from weasyprint import HTML
import io
import markdown

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
WS_URL_BASE = os.environ.get("BACKEND_WS_URL", "ws://localhost:8000")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")

CLIENT_DATA_DIR = Path("./test_data/")

st.set_page_config(page_title="Transcript Insight", page_icon="📄", layout="wide")


def _new_session():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.final_text = None
    st.session_state.analysis_report = None
    st.session_state.uploaded_file_name = None
    st.session_state.spec_saved = False
    st.session_state.cost = 0.0

if "session_id" not in st.session_state:
    _new_session()

if "final_text" not in st.session_state:
    st.session_state.final_text = None
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "spec_saved" not in st.session_state:
    st.session_state.spec_saved = False



def build_analysis_spec_from_session_state() -> dict:
    """Collect the AnalysisSpec payload using the latest session values."""
    return {
        "focus": st.session_state.get("spec_focus", "GPA trend, major GPA"),
        "audience": st.session_state.get("spec_audience", "student"),
        "audience_spec": st.session_state.get("spec_audience_spec", ""),
        "audience_goal": st.session_state.get("spec_audience_goal", "general insight"),
        "evaluation_criteria": st.session_state.get("spec_evaluation_criteria", ""),
        "decision_context": st.session_state.get("spec_decision_context", ""),
        "time_scope": st.session_state.get("spec_time_scope", "전체 학기"),
        "comparison_target": st.session_state.get("spec_comparison_target") or None,
        "tone": st.session_state.get("spec_tone", "neutral"),
        "language": st.session_state.get("spec_language", "ko"),
        "insight_style": st.session_state.get("spec_insight_style", "descriptive"),
        "report_format": st.session_state.get("spec_report_format", "html"),
    }

def clear_data_only():
    """Clear parsed/analysis artifacts while keeping the session id."""
    try:
        if session_dir.exists():
            for p in session_dir.iterdir():
                if p.is_file():
                    p.unlink(missing_ok=True)
                else:
                    shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass
    st.session_state.final_text = None
    st.session_state.analysis_report = None
    st.session_state.uploaded_file_name = None

# --- Session Directory Setup ---
session_id = st.session_state.session_id
session_dir = CLIENT_DATA_DIR / 'users'/ session_id
session_dir.mkdir(exist_ok=True, parents=True)


async def listen_to_websocket(placeholder, session_id):
    WEBSOCKET_URL = f"{WS_URL_BASE}/ws/{session_id}"
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            async for message in websocket:  # 연결 유지 + 메시지 대기
                data = json.loads(message)

                # just check connection (keepalive)
                if data.get("event") == "keepalive":
                    continue

                if "name" in data and "status" in data:
                    status = data["status"]
                    if status == "start":
                        placeholder.text(f"Processing: {data['name']}...")
                    elif status == "progress":
                        comp = data.get("completed")
                        total = data.get("total")
                        if isinstance(comp, int) and isinstance(total, int) and total > 0:
                            placeholder.text(f"Processing: {data['name']}… ({comp}/{total})")
                        else:
                            placeholder.text(f"Processing: {data['name']}…")
                    elif status == "end":
                        if "duration" in data:
                            placeholder.text(f"Finished: {data['name']} in {data['duration']}s")
                        else:
                            placeholder.text(f"Finished: {data['name']}")

                if data.get("event") == "eof":
                    placeholder.success("Finished Analyst — assembling final report…")
                    await websocket.close()
                    break

    except websockets.exceptions.ConnectionClosed:
        # 서버나 클라이언트에서 종료되면 여기로 옴
        pass


async def parse_with_backend(file, placeholder) -> None: 

    async def _upload_pdf(): 
        files = {"file": (file.name, file.getvalue(), "application/pdf")} 
        async with httpx.AsyncClient(timeout=300) as client: 
            response = await client.post(f"{BACKEND_URL}/upload/{session_id}", files=files) 
            response.raise_for_status() 
            data = response.json() 
            st.session_state.final_text = data.get("final_result") 
    await asyncio.gather(
        listen_to_websocket(placeholder, session_id),
        _upload_pdf()
    )

async def run_analysis(transcript_payload: dict, report_placeholder):
    spec = build_analysis_spec_from_session_state()
    async def _call_analyze():
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{BACKEND_URL}/analyze/{session_id}",
                json={"transcript": transcript_payload, "analyst": spec, "url": PUBLIC_BACKEND_URL}
            )
        response.raise_for_status()
        response_state = response.json()
        st.session_state.analysis_report = response_state.get("report")
        cost = response_state.get("cost", 0.0)
        st.session_state.cost = cost
        st.session_state.analysis_run_id = response_state.get("run_id")

        report_format = st.session_state.get("spec_report_format", "html") or "html"
        report_path = Path(f"{CLIENT_DATA_DIR}/users/{session_id}/{session_id}.{report_format}")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            f.write(response_state.get("report"))
    await asyncio.gather(
        listen_to_websocket(report_placeholder, session_id),
        _call_analyze()
    )

async def save_spec_to_backend():
    spec = build_analysis_spec_from_session_state()
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{BACKEND_URL}/spec/{session_id}",
            json=spec
        )


st.title("📄 Transcript Insight")

st.markdown(
    f"<small>Session: <code>{session_id}</code></small>",
    unsafe_allow_html=True,
)
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 New Session / Clear All", use_container_width=True):
            try:
                if session_dir.exists():
                    shutil.rmtree(session_dir)
            except Exception:
                pass
            _new_session()
            st.rerun()
    with c2:
        if st.button("🧹 Clear Data (keep session)", use_container_width=True):
            clear_data_only()
            st.toast("Cleared parsed data and analysis results.", icon="🧹")

st.divider()

st.header("1) Upload Transcript")

with st.container():
    transcript_placeholder = st.empty()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📄 PDF Upload")
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_file")
        if st.button("▶ Start Parsing", disabled=(pdf_file is None)):
            with st.spinner("Parsing your PDF…"):
                asyncio.run(parse_with_backend(pdf_file, transcript_placeholder))
                if st.session_state.final_text is not None:
                    st.success("✅ Parsing complete")

    with c2:
        st.subheader("📝 JSON Upload")
        json_file = st.file_uploader("Upload JSON", type=["json"], key="json_file")
        if json_file is not None:
            try:
                parsed_json = json.load(json_file)
                st.session_state.final_text = parsed_json
                st.success("✅ JSON file loaded successfully.")
            except Exception as e:
                st.error(f"Invalid JSON file: {e}")

# JSON 결과 확인은 공통
if st.session_state.final_text is not None:
    with st.expander("📦 Extracted JSON (toggle)", expanded=False):
        if isinstance(st.session_state.final_text, dict):
            st.json(st.session_state.final_text, expanded=False)
        else:
            st.text_area("Result", str(st.session_state.final_text), height=400)
st.divider()
            

st.header("2) Analyst Settings & Run")

with st.expander("⚙️ Analyst Settings", expanded=False):
    # Use a form so that "Save" applies all together (less clutter)
    with st.form("analyst_settings_form", clear_on_submit=False):
        st.markdown("**Focus & Audience**")
        st.text_input("Focus (comma or a single phrase)", value="GPA trend, major GPA", key="spec_focus")
        st.selectbox("Audience", ["student", "evaluator", "advisor"], index=0, key="spec_audience")
        st.text_input("Audience Spec (예: AI company recruiter)", value="", key="spec_audience_spec")
        st.text_input("Audience Goal", value="general insight", key="spec_audience_goal")
        st.text_input("Evaluation Criteria (comma)", value="", key="spec_evaluation_criteria")
        st.text_input("Decision Context (예: 채용 선발 / 장학금 심사)", value="", key="spec_decision_context")
        st.markdown("---")
        st.markdown("**Scope & Focus**")
        st.text_input("Time Scope", value="전체 학기", key="spec_time_scope")
        st.text_input("Comparison Target (optional)", value="", key="spec_comparison_target")
        st.markdown("---")
        st.markdown("**Style**")
        st.selectbox("Tone", ["neutral", "encouraging", "formal"], index=0, key="spec_tone")
        st.selectbox("Language", ["ko", "en"], index=0, key="spec_language")
        st.selectbox("Insight Style", ["descriptive","comparative","predictive"], index=0, key="spec_insight_style")
        st.selectbox("Report Format", ["markdown","html"], index=1, key="spec_report_format")
        saved = st.form_submit_button("💾 Save Settings")
        if saved:
            st.session_state.spec_saved = True
            asyncio.run(save_spec_to_backend())
            st.toast("Analyst settings saved + backend updated.", icon="✅")

report_placeholder = st.empty()
analyze_disabled = st.session_state.final_text is None
if st.button("🚀 Run Analyst and Build Report", type="primary", disabled=analyze_disabled):
    if analyze_disabled:
        st.warning("먼저 PDF를 업로드하고 파싱을 완료해 주세요.")
    else:
        with st.spinner("Running Analyst…"):
            transcript_payload = st.session_state.final_text
            if not isinstance(transcript_payload, dict):
                try:
                    transcript_payload = json.loads(transcript_payload)
                except Exception:
                    pass
            asyncio.run(run_analysis(transcript_payload, report_placeholder))
            st.success("✅ Analysis complete")

# 💰 비용 표시 (Analyst Settings & Run 섹션 바로 밑)
if "cost" in st.session_state:
    st.info(f"💰 Total analysis cost: **${st.session_state.cost:.4f}**")

st.divider()

st.header("3) Report Preview / Download")

report_format = st.session_state.get("spec_report_format", "html")

if st.session_state.analysis_report is not None:
    if st.session_state.analysis_report:
        report_content = st.session_state.analysis_report

        # Report Preview + Download (기존 그대로)
        if report_format == "markdown":
            st.markdown(report_content, unsafe_allow_html=False)
            st.download_button(
                "💾 Download report.md",
                report_content.encode("utf-8"),
                file_name="report.md",
                mime="text/markdown"
            )
        elif report_format == "html":
            st.components.v1.html(report_content, scrolling=True, height=800)
            st.download_button(
                "💾 Download report.html",
                report_content.encode("utf-8"),
                file_name="report.html",
                mime="text/html"
            )

        # PDF 변환 버튼
        try:
            if report_format == "html":
                html_for_pdf = report_content.replace(PUBLIC_BACKEND_URL, BACKEND_URL)
                pdf_bytes = HTML(string=html_for_pdf, base_url='.').write_pdf()
            else:
                # markdown → html 변환 후 PDF
                html_from_md = markdown.markdown(report_content)
                html_for_pdf = html_from_md.replace(PUBLIC_BACKEND_URL, BACKEND_URL)
                pdf_bytes = HTML(string=html_for_pdf, base_url='.').write_pdf()

            st.download_button(
                "📄 Download report.pdf",
                data=pdf_bytes,
                file_name="report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF 변환 중 오류 발생: {e}")

    else:
        st.info("No report text returned.")

    # Optional charts (base64) support
    visualizations = []
    try:
        visualizations = st.session_state.analysis_report.get("visualizations", [])
    except AttributeError:
        pass

    if visualizations:
        st.subheader("📊 Visualizations")
        for i, img_b64 in enumerate(visualizations, start=1):
            try:
                st.image(base64.b64decode(img_b64), caption=f"Chart {i}")
            except Exception:
                pass
else:
    st.info("분석 결과가 준비되면 이 영역에 리포트가 표시됩니다.")
