

import ast
import io
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from google import genai


st.set_page_config(
    page_title="Project Genesis",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = APP_DIR / "genesis_projects"
PROJECTS_DIR.mkdir(exist_ok=True)

CURRENT_APP = APP_DIR / "generated_app.py"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

defaults = {
    "generated_code": "",
    "generated_filename": "generated_app.py",
    "idea": "",
    "editor_code": "",
    "doctor_review": "",
    "fixed_code": "",
    "requirements_text": "streamlit\ngoogle-genai"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


TEMPLATES = {
    "Student Expense Tracker":
        "Create a student expense tracker. Include adding expenses, "
        "categories, dates, total spending, monthly summaries and charts.",

    "Student Management System":
        "Create a student management system. Include adding, editing, "
        "searching and deleting student records, with name, roll number, "
        "course and contact information.",

    "Attendance Management System":
        "Create an attendance management system. Include student records, "
        "attendance marking, attendance percentages and summary reports.",

    "AI Chatbot":
        "Create a chatbot interface with a chat history, user input, "
        "and a clean conversational UI. Use a placeholder response function "
        "that can later be connected to an AI API.",

    "To-Do List":
        "Create a task management application. Include adding tasks, "
        "marking tasks complete, deleting tasks, priorities and due dates.",

    "Personal Portfolio":
        "Create a personal portfolio website using Streamlit. Include "
        "an introduction, skills, projects, education and contact section.",

    "Data Analytics Dashboard":
        "Create a data analytics dashboard. Include CSV upload, data "
        "preview, summary statistics, filters and interactive charts.",

    "Library Management System":
        "Create a library management system. Include adding books, "
        "searching books, issuing books, returning books and book records."
}


def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""

    return key or os.getenv("GEMINI_API_KEY", "")


def ask_gemini(prompt):
    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "Gemini API key not found. Check .streamlit/secrets.toml."
        )

    client = genai.Client(api_key=api_key)

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            return response.text

        except Exception as error:
            message = str(error).lower()

            if attempt < 2 and any(
                word in message for word in
                ["503", "429", "unavailable", "resource_exhausted"]
            ):
                time.sleep(4 * (attempt + 1))
            else:
                raise error


def clean_code(code):
    code = code.strip()
    code = re.sub(r"^```(?:python)?\s*", "", code, flags=re.I)
    code = re.sub(r"\s*```$", "", code)
    return code.strip()


def check_code(code):
    try:
        ast.parse(code)
        return None
    except SyntaxError as error:
        return f"Line {error.lineno}: {error.msg}"


def safe_filename(name):
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.lower())
    return (name.strip("_")[:45] or "generated_project") + ".py"


def save_project(code, filename):
    if not code.strip():
        raise ValueError("There is no code to save.")

    filename = safe_filename(filename.replace(".py", ""))

    (PROJECTS_DIR / filename).write_text(
        code, encoding="utf-8"
    )

    CURRENT_APP.write_text(code, encoding="utf-8")

    return filename


def get_projects():
    return sorted(
        PROJECTS_DIR.glob("*.py"),
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )


def make_project_zip(code, filename, requirements):
    readme = f"""# Project Genesis Application

## About
This application was generated using Project Genesis.

## Installation

1. Install Python.
2. Open a terminal in this folder.
3. Install dependencies:

    pip install -r requirements.txt

4. Run the application:

    streamlit run {filename}

## Requirements
Check requirements.txt for dependencies.

## Note
Review generated code before running it.
"""

    memory_file = io.BytesIO()

    with zipfile.ZipFile(
        memory_file, "w", zipfile.ZIP_DEFLATED
    ) as archive:
        archive.writestr(filename, code)
        archive.writestr("requirements.txt", requirements)
        archive.writestr("README.md", readme)

    memory_file.seek(0)
    return memory_file.getvalue()


def download_python(code, filename, key):
    st.download_button(
        "⬇️ Download Python Code",
        data=code,
        file_name=filename,
        mime="text/x-python",
        key=key,
        use_container_width=True
    )


def show_code_status(code):
    error = check_code(code)

    if error:
        st.error(f"Syntax issue detected: {error}")
    else:
        st.success("Python syntax check passed.")

    return error


st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 10% 10%, #30205a55, transparent 30%),
        radial-gradient(circle at 90% 20%, #173c6a44, transparent 30%),
        linear-gradient(135deg, #101126, #191538, #101a35);
    color: #f5f3ff;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c0d20, #191538, #111b35);
    border-right: 1px solid #7957ff88;
}

h1, h2, h3 {
    color: white !important;
}

h1 {
    text-shadow: 0 0 18px #9b5cff88;
    font-weight: 800 !important;
}

p, label, li {
    color: #e4def7;
}

[data-testid="stRadio"] label {
    background: #211b43;
    border: 1px solid #7957ff55;
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 6px;
}

[data-testid="stRadio"] label:hover {
    border-color: #c084fc;
    background: #2b2052;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    background: #17172f !important;
    color: white !important;
    border-radius: 12px !important;
}

.stTextInput input,
.stTextArea textarea {
    border: 1px solid #7957ff99 !important;
}

.stButton button,
.stDownloadButton button {
    background: linear-gradient(100deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: 1px solid #a78bfa !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    min-height: 42px;
    box-shadow: 0 0 13px #7c3aed55;
    transition: 0.2s;
}

.stButton button:hover,
.stDownloadButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 22px #a855f799;
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, #211747, #172554);
    border: 1px solid #7957ff77;
    border-radius: 15px;
    padding: 16px;
}

.genesis-hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(120deg, #211747, #172554);
    border: 1px solid #9b5cff;
    box-shadow: 0 0 25px #7c3aed55;
    margin-bottom: 25px;
}

.genesis-card {
    padding: 22px;
    min-height: 160px;
    border-radius: 16px;
    background: linear-gradient(135deg, #211747, #172554);
    border: 1px solid #7957ff88;
    box-shadow: 0 0 16px #7c3aed33;
    transition: 0.25s;
}

.genesis-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0 23px #a855f799;
    border-color: #c084fc;
}

.genesis-card h3 {
    color: white;
}

.genesis-card p {
    color: #cbd5e1;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("# 🚀 Project Genesis")
    st.caption("Turn your ideas into applications.")
    st.markdown("---")

    page = st.radio(
        "NAVIGATION",
        [
            "🏠 Home",
            "⚡ AI App Generator",
            "🩺 AI App Doctor",
            "📁 My Projects"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption(f"AI Model: {MODEL}")
    st.caption("Powered by Python, Streamlit & Gemini")


if page == "🏠 Home":

    projects = get_projects()

    st.markdown("""
    <div class="genesis-hero">
        <div style="color:#c4b5fd; letter-spacing:3px;">
            YOUR AI DEVELOPMENT PARTNER
        </div>
        <h1 style="font-size:38px;">Welcome to Project Genesis 🚀</h1>
        <p>Turn your ideas into working applications with AI.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Saved Projects", len(projects))

    with col2:
        st.metric("AI Features", "3")

    with col3:
        st.metric("Templates", len(TEMPLATES))

    st.markdown("---")
    st.subheader("✨ Explore Genesis")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="genesis-card">
            <h3>⚡ AI App Generator</h3>
            <p>Describe your idea and generate a Python application.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="genesis-card">
            <h3>🩺 AI App Doctor</h3>
            <p>Analyze code, find issues and generate corrections.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="genesis-card">
            <h3>📁 My Projects</h3>
            <p>Manage, edit, download and export your applications.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🚀 Start building")
    st.write(
        "Open AI App Generator from the sidebar, choose a template "
        "or describe your own application."
    )


elif page == "⚡ AI App Generator":

    st.title("⚡ AI App Generator")
    st.write("Build applications using your ideas and AI.")

    st.subheader("Choose a starting point")

    template_name = st.selectbox(
        "Ready-made templates",
        ["Choose a template"] + list(TEMPLATES.keys())
    )

    if st.button("Use Selected Template"):
        if template_name != "Choose a template":
            st.session_state["idea"] = TEMPLATES[template_name]
            st.rerun()

    idea = st.text_area(
        "Describe your application",
        value=st.session_state["idea"],
        height=140,
        placeholder="Example: Create a student attendance management system..."
    )

    app_name = st.text_input(
        "Application name",
        placeholder="Example: Student Attendance System"
    )

    with st.expander("⚙️ Advanced options"):
        extra_requirements = st.text_area(
            "Additional instructions",
            placeholder="Example: Use charts, add search, use a dark theme..."
        )

    if st.button("✨ Generate My Application", use_container_width=True):

        if not idea.strip():
            st.warning("Please describe your application.")

        elif not get_api_key():
            st.error("Gemini API key is missing. Check secrets.toml.")

        else:
            prompt = f"""
You are an expert Python and Streamlit developer.

Build a complete, functional Python Streamlit application.

APPLICATION IDEA:
{idea}

ADDITIONAL REQUIREMENTS:
{extra_requirements}

RULES:
1. Return complete Python source code.
2. Include all required imports.
3. Make buttons and features functional.
4. Use Streamlit for the interface.
5. Handle errors properly.
6. Use beginner-friendly code.
7. Do not use fake API keys or credentials.
8. Do not leave important features as placeholders.
9. Return Python code only, without Markdown fences.
"""

            with st.spinner("🚀 Genesis is building your application..."):

                try:
                    result = ask_gemini(prompt)
                    code = clean_code(result)
                    error = check_code(code)

                    st.session_state["generated_code"] = code
                    st.session_state["editor_code"] = code
                    st.session_state["idea"] = idea

                    filename = safe_filename(
                        app_name or idea.split("\n")[0]
                    )

                    st.session_state["generated_filename"] = filename

                    if error:
                        st.warning(
                            f"Generated code has a syntax issue: {error}"
                        )
                    else:
                        save_project(code, filename)
                        st.success("Your application has been generated!")

                except Exception as error:
                    st.error(f"Generation failed: {error}")

    code = st.session_state.get("generated_code", "")

    if code:

        st.markdown("---")
        st.subheader("🎉 Your Generated Application")

        show_code_status(code)

        st.info(
            "You can edit the code below. Save your changes before exporting "
            "or running your application."
        )

        edited_code = st.text_area(
            "Built-in Code Editor",
            key="editor_code",
            height=420
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Changes", use_container_width=True):
                error = check_code(edited_code)

                if error:
                    st.error(f"Fix the syntax issue first: {error}")
                else:
                    filename = save_project(
                        edited_code,
                        st.session_state["generated_filename"]
                    )
                    st.session_state["generated_code"] = edited_code
                    st.success(f"Saved as {filename}")

        with col2:
            download_python(
                edited_code,
                st.session_state["generated_filename"],
                "download_generated"
            )

        st.markdown("### 📦 Export Complete Project")

        requirements = st.text_area(
            "Project dependencies (one per line)",
            key="requirements_text",
            height=90
        )

        zip_data = make_project_zip(
            edited_code,
            st.session_state["generated_filename"],
            requirements
        )

        st.download_button(
            "📦 Download Complete Project (ZIP)",
            data=zip_data,
            file_name="Genesis_Project.zip",
            mime="application/zip",
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("🧪 Code Testing")

        error = check_code(edited_code)

        if st.button("Run Python Syntax Test", use_container_width=True):
            if error:
                st.error(f"Syntax test failed: {error}")
            else:
                st.success("Passed! Python can parse this code.")

        st.caption(
            "This checks Python syntax only. It does not guarantee "
            "that every feature or external dependency will work."
        )

        st.warning(
            "Only run code you trust. AI-generated code can contain "
            "bugs or unsafe operations."
        )

        if st.button("▶️ Launch Generated Application", use_container_width=True):

            if error:
                st.error("Fix the syntax issue before launching.")
            else:
                try:
                    save_project(
                        edited_code,
                        st.session_state["generated_filename"]
                    )

                    subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "streamlit",
                            "run",
                            str(CURRENT_APP)
                        ],
                        cwd=str(APP_DIR)
                    )

                    st.success(
                        "Launch command started. Check your VS Code terminal "
                        "for the local application URL."
                    )

                except Exception as launch_error:
                    st.error(f"Could not launch application: {launch_error}")


elif page == "🩺 AI App Doctor":

    st.title("🩺 AI App Doctor")
    st.write("Your AI coding assistant for code analysis and debugging.")

    doctor_code = st.text_area(
        "Paste your Python code",
        height=300,
        placeholder="Paste your Python code here..."
    )

    if doctor_code.strip():
        show_code_status(doctor_code)

    col1, col2 = st.columns(2)

    with col1:
        analyze = st.button("🔍 Analyze Code", use_container_width=True)

    with col2:
        fix = st.button("🛠️ Fix My Code", use_container_width=True)

    if analyze or fix:

        if not doctor_code.strip():
            st.warning("Please paste your code first.")

        elif not get_api_key():
            st.error("Gemini API key is missing.")

        else:

            if analyze:
                prompt = f"""
You are an expert Python code reviewer.

Analyze this code:
{doctor_code}

Explain:
1. What the code does.
2. Bugs and errors.
3. Possible improvements.
4. Security concerns.
5. How a beginner can understand and improve it.

Do not claim that you executed the code.
"""

            else:
                prompt = f"""
You are an expert Python developer.

Fix and improve this code:
{doctor_code}

Preserve the original purpose and features.
Include required imports.
Return complete corrected Python code only.
Do not use Markdown code fences.
Do not add fake API keys.
"""

            with st.spinner("🩺 AI App Doctor is working..."):

                try:
                    result = ask_gemini(prompt)

                    if analyze:
                        st.session_state["doctor_review"] = result
                        st.session_state["fixed_code"] = ""

                    else:
                        st.session_state["fixed_code"] = clean_code(result)
                        st.session_state["doctor_review"] = ""

                except Exception as error:
                    st.error(f"Doctor could not complete the request: {error}")

    review = st.session_state.get("doctor_review", "")

    if review:
        st.markdown("---")
        st.subheader("📋 Doctor's Analysis")
        st.markdown(review)

    fixed = st.session_state.get("fixed_code", "")

    if fixed:
        st.markdown("---")
        st.subheader("✨ Corrected Code")

        show_code_status(fixed)

        st.code(fixed, language="python", line_numbers=True)

        download_python(
            fixed,
            "fixed_app.py",
            "download_fixed"
        )

        if st.button("💾 Save Corrected Code", use_container_width=True):
            try:
                save_project(fixed, "fixed_app.py")
                st.success("Corrected code saved in My Projects.")
            except Exception as error:
                st.error(str(error))


elif page == "📁 My Projects":

    st.title("📁 My Projects")
    st.write("Manage all your saved Genesis applications.")

    projects = get_projects()

    st.metric("Total Saved Projects", len(projects))

    if not projects:
        st.info("No projects saved yet. Generate your first application!")

    else:

        project_names = [project.name for project in projects]

        selected = st.selectbox(
            "Select a project",
            project_names
        )

        selected_path = PROJECTS_DIR / selected

        if selected_path.exists():

            code = selected_path.read_text(encoding="utf-8")

            st.markdown("---")
            st.subheader(f"📄 {selected}")

            modified = datetime.fromtimestamp(
                selected_path.stat().st_mtime
            ).strftime("%d %b %Y, %I:%M %p")

            st.caption(f"Last modified: {modified}")

            st.code(
                code,
                language="python",
                line_numbers=True
            )

            download_python(
                code,
                selected,
                "download_saved_project"
            )

            st.markdown("### ✏️ Rename Project")

            new_name = st.text_input(
                "New project name (without .py)",
                value=selected.replace(".py", ""),
                key="rename_project_input"
            )

            if st.button("Rename Project"):
                new_filename = safe_filename(new_name)
                new_path = PROJECTS_DIR / new_filename

                if new_path.exists() and new_path != selected_path:
                    st.error("A project with that name already exists.")

                elif new_path == selected_path:
                    st.info("The project already has that name.")

                else:
                    selected_path.rename(new_path)
                    st.success("Project renamed successfully!")
                    st.rerun()

            st.markdown("---")
            st.subheader("📦 Export Project")

            requirements = st.text_area(
                "Dependencies for this project",
                value="streamlit\ngoogle-genai",
                key="project_requirements"
            )

            zip_data = make_project_zip(
                code,
                selected,
                requirements
            )

            st.download_button(
                "📦 Export as ZIP",
                data=zip_data,
                file_name=selected.replace(".py", "") + ".zip",
                mime="application/zip",
                use_container_width=True
            )

            st.markdown("---")
            st.subheader("🗑️ Delete Project")

            confirm_delete = st.checkbox(
                f"I understand that I want to delete {selected}.",
                key="confirm_delete"
            )

            if st.button(
                "Delete Selected Project",
                disabled=not confirm_delete,
                use_container_width=True
            ):
                selected_path.unlink()
                st.success("Project deleted.")
                st.rerun()

            st.markdown("---")
            st.subheader("📝 Open Project in Editor")

            if st.button("Load This Project into Generator"):
                st.session_state["generated_code"] = code
                st.session_state["editor_code"] = code
                st.session_state["generated_filename"] = selected
                st.session_state["open_loaded_project"] = True
                st.success(
                    "Project loaded. Select AI App Generator in the sidebar "
                    "to edit it."
                )


st.markdown("---")

st.markdown("""
<div style="text-align:center; padding:15px;">
    <h3>🚀 Project Genesis</h3>
    <p>From idea to application.</p>
    <p style="color:#a78bfa;">
        Built with Python, Streamlit and Gemini
    </p>
</div>
""", unsafe_allow_html=True)
