import streamlit as st
import requests

# change this to your FastAPI backend URL
API_BASE = "http://localhost:8000"

st.set_page_config(page_title="VTOP Scraper", layout="wide")
st.title("VTOP Scraper")

# Session state for registration, login, etc.
if "reg_no" not in st.session_state:
    st.session_state["reg_no"] = ""
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "session_created" not in st.session_state:
    st.session_state["session_created"] = False
if "captcha_img" not in st.session_state:
    st.session_state["captcha_img"] = None
if "sem_list" not in st.session_state:
    st.session_state["sem_list"] = []

# --- Login Workflow --- #
st.header("1. Login to VTOP")

reg_no = st.text_input("Registration Number", st.session_state["reg_no"])

if st.button("Create Session"):
    res = requests.get(f"{API_BASE}/student/create_session", params={"reg_no": reg_no})
    if res.ok and res.json().get("success"):
        st.session_state["reg_no"] = reg_no
        st.session_state["session_created"] = True
        st.success("Session created successfully.")
    else:
        st.error(f"Failed to create session: {res.text}")

if st.session_state["session_created"]:
    st.write("**Step 2: Get Captcha & Prepare Login**")
    if st.button("Get Captcha"):
        try:
            response = requests.post(
                f"{API_BASE}/student/prepare_login",
                params={"reg_no": st.session_state["reg_no"]},
            )
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    st.session_state["captcha_img"] = data["image_code"]
                    st.success("Captcha loaded!")
                    st.rerun()
                else:
                    st.error("Failed to get captcha")
            else:
                st.error(f"Error: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
        else:
            st.error(f"Failed to get captcha: {res.text}")

    if st.session_state["captcha_img"]:
        st.image(
            st.session_state["captcha_img"], caption="Captcha", use_column_width=False
        )
        password = st.text_input("Password", type="password")
        captcha_text = st.text_input("Enter Captcha Shown Above")
        if st.button("Login"):
            data = {
                "reg_no": st.session_state["reg_no"],
                "password": password,
                "response_captcha": captcha_text,
            }
            res = requests.post(f"{API_BASE}/student/login", json=data)
            if res.ok and res.json().get("success"):
                st.session_state["logged_in"] = True
                st.success("Login successful!")
            else:
                msg = res.json().get("message", res.text)
                st.error(f"Login failed: {msg}")


# After login, allow access to LLM endpoints
def fetch_api(path, params=None):
    url = f"{API_BASE}{path}"
    try:
        res = requests.get(url, params=params, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


if st.session_state["logged_in"]:
    st.header("2. Student Dashboard")
    st.success(f"Logged in as: {st.session_state['reg_no']}")
    if st.button("Start Scraping & Refresh Data"):
        with st.spinner("Scraping student data from VTOP..."):
            resp = fetch_api(
                "/student/start-scraping",
                {"reg_no": st.session_state["reg_no"], "force_scrape": True},
            )
            if resp.get("success"):
                st.success(f"Scraping done. Name: {resp.get('name', 'N/A')}")
            else:
                st.error("Error scraping student data. Please try again.")
    # Fetch semesters for dropdowns
    if st.button("Load Semester List") or not st.session_state["sem_list"]:
        resp = fetch_api("/llm/semesters", {"reg_no": st.session_state["reg_no"]})
        if resp.get("success") and resp.get("data"):
            sems = resp["data"]
            st.session_state["sem_list"] = (
                list(sems.keys()) if isinstance(sems, dict) else sems
            )
            st.info(f"Semesters loaded: {st.session_state['sem_list']}")
        else:
            st.warning("Could not load semesters.")
    # Prepare tabs for each LLM endpoint
    tab_names = [
        "Profile",
        "Semesters",
        "Grade History",
        "Credits Info",
        "Grades Count",
        "CGPA Details",
        "Marks",
        "Attendance",
        "Timetable",
        "Courses",
    ]
    tabs = st.tabs(tab_names)
    with tabs[0]:  # Profile
        if st.button("Fetch Profile"):
            resp = fetch_api("/llm/profile", {"reg_no": st.session_state["reg_no"]})
            st.json(resp)
    with tabs[1]:  # Semesters
        if st.button("Fetch Semesters"):
            resp = fetch_api("/llm/semesters", {"reg_no": st.session_state["reg_no"]})
            st.json(resp)
    with tabs[2]:  # Grade History
        if st.button("Fetch Grade History"):
            resp = fetch_api(
                "/llm/grade_history", {"reg_no": st.session_state["reg_no"]}
            )
            st.json(resp)
    with tabs[3]:  # Credits Info
        if st.button("Fetch Credits Info"):
            resp = fetch_api(
                "/llm/credits_info", {"reg_no": st.session_state["reg_no"]}
            )
            st.json(resp)
    with tabs[4]:  # Grades Count
        if st.button("Fetch Grades Count"):
            resp = fetch_api(
                "/llm/grades_count", {"reg_no": st.session_state["reg_no"]}
            )
            st.json(resp)
    with tabs[5]:  # CGPA Details
        sem_id = st.selectbox(
            "Select Semester ID (or leave blank for all)",
            [""] + st.session_state["sem_list"],
            key="cgpa_sem",
        )
        if st.button("Fetch CGPA Details"):
            params = {"reg_no": st.session_state["reg_no"]}
            if sem_id:
                params["sem_id"] = sem_id
            resp = fetch_api("/llm/cgpa_details", params)
            st.json(resp)
    with tabs[6]:  # Marks
        sem_id = st.selectbox(
            "Select Semester ID (or leave blank for all)",
            [""] + st.session_state["sem_list"],
            key="marks_sem",
        )
        if st.button("Fetch Marks"):
            params = {"reg_no": st.session_state["reg_no"]}
            if sem_id:
                params["sem_id"] = sem_id
            resp = fetch_api("/llm/marks", params)
            st.json(resp)
    with tabs[7]:  # Attendance
        sem_id = st.selectbox(
            "Select Semester ID (or leave blank for all)",
            [""] + st.session_state["sem_list"],
            key="att_sem",
        )
        if st.button("Fetch Attendance"):
            params = {"reg_no": st.session_state["reg_no"]}
            if sem_id:
                params["sem_id"] = sem_id
            resp = fetch_api("/llm/attendance", params)
            st.json(resp)
    with tabs[8]:  # Timetable
        sem_id = st.selectbox(
            "Select Semester ID (or leave blank for all)",
            [""] + st.session_state["sem_list"],
            key="tt_sem",
        )
        if st.button("Fetch Timetable"):
            params = {"reg_no": st.session_state["reg_no"]}
            if sem_id:
                params["sem_id"] = sem_id
            resp = fetch_api("/llm/timetable", params)
            st.json(resp)
    with tabs[9]:  # Courses
        if st.button("Fetch Courses"):
            resp = fetch_api("/llm/courses", {"reg_no": st.session_state["reg_no"]})
            st.json(resp)
            st.markdown("---")
    if st.button("Logout"):
        resp = fetch_api("/student/logout", {"reg_no": st.session_state["reg_no"]})
        st.session_state["logged_in"] = False
        st.session_state["session_created"] = False
        st.session_state["captcha_img"] = None
        st.session_state["sem_list"] = []
        st.success("Logged out and data deleted.")
        st.rerun()
