from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
import streamlit as st


START_DATE = date(2026, 7, 27)
END_DATE = date(2026, 8, 7)
START_HOURS = (12, 13, 14, 15)
TIMEZONE = ZoneInfo("Asia/Seoul")
WORKSHEET_NAME = "신청내역"
HEADERS = [
    "신청일시",
    "학번",
    "학생 이름",
    "신청자",
    "상담 방식",
    "상담 날짜",
    "상담 시간",
    "연락처",
    "상담 희망 내용",
]


def weekdays_between(start: date, end: date) -> list[date]:
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def date_label(value: date) -> str:
    weekday = "월화수목금토일"[value.weekday()]
    return f"{value.month}월 {value.day}일 ({weekday})"


def slot_label(hour: int) -> str:
    return f"{hour:02d}:00 ~ {hour + 1:02d}:00"


@st.cache_resource
def worksheet():
    credentials = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(credentials)
    book = client.open_by_url(st.secrets["sheet_url"])
    try:
        sheet = book.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=WORKSHEET_NAME, rows=200, cols=len(HEADERS))
    if not sheet.row_values(1):
        sheet.append_row(HEADERS)
        sheet.freeze(rows=1)
    return sheet


def reserved_slots(selected_date: date) -> set[str]:
    records = worksheet().get_all_records()
    key = selected_date.isoformat()
    return {
        str(record.get("상담 시간", "")).strip()
        for record in records
        if str(record.get("상담 날짜", "")).strip() == key
    }


def save_request(values: list[str]) -> bool:
    sheet = worksheet()
    # 제출 직전에 다시 조회하여 동시에 들어온 중복 신청을 한 번 더 차단합니다.
    rows = sheet.get_all_records()
    wanted_date, wanted_time = values[5], values[6]
    duplicate = any(
        str(row.get("상담 날짜", "")).strip() == wanted_date
        and str(row.get("상담 시간", "")).strip() == wanted_time
        for row in rows
    )
    if duplicate:
        return False
    sheet.append_row(values, value_input_option="USER_ENTERED")
    return True


st.set_page_config(page_title="학생·학부모 상담 신청", page_icon="📅", layout="centered")
st.title("학생·학부모 상담 신청")
st.caption("상담 기간: 2026년 7월 27일(월) ~ 8월 7일(금), 평일 12:00~16:00")

st.info("상담은 한 시간 단위로 진행됩니다. 학부모 상담은 가급적 전화 상담을 권장합니다.")

try:
    worksheet()
except Exception:
    st.error("현재 신청 저장소에 연결할 수 없습니다. 잠시 후 다시 접속해 주세요.")
    st.stop()

with st.form("consultation_request"):
    left, right = st.columns(2)
    with left:
        student_number = st.text_input("학번", placeholder="예: 30601", max_chars=10)
    with right:
        student_name = st.text_input("학생 이름", max_chars=20)

    applicant = st.radio(
        "신청자",
        ["학생 본인", "부", "모", "부·모 모두"],
        horizontal=True,
    )
    if applicant != "학생 본인":
        st.info("학부모 상담은 이동 부담을 줄이기 위해 전화 상담을 권장합니다.")

    method = st.radio("상담 방식", ["전화 상담", "대면 상담"], horizontal=True)
    available_dates = weekdays_between(START_DATE, END_DATE)
    selected_date = st.selectbox("상담 희망 날짜", available_dates, format_func=date_label)

    occupied = reserved_slots(selected_date)
    available_slots = [slot_label(hour) for hour in START_HOURS if slot_label(hour) not in occupied]
    if available_slots:
        selected_time = st.selectbox("상담 희망 시간", available_slots)
    else:
        selected_time = None
        st.warning("선택한 날짜에는 남은 상담 시간이 없습니다. 다른 날짜를 선택해 주세요.")

    phone = st.text_input("연락처", placeholder="전화 상담 또는 일정 확인에 사용할 번호")
    note = st.text_area("상담 희망 내용", placeholder="상담하고 싶은 내용을 간단히 적어 주세요.", height=120)
    consent = st.checkbox("상담 신청을 위해 위 개인정보를 제공하는 데 동의합니다.")
    submitted = st.form_submit_button("상담 신청", type="primary", use_container_width=True)

if submitted:
    if not student_number.strip() or not student_name.strip():
        st.error("학번과 학생 이름을 모두 입력해 주세요.")
    elif not phone.strip():
        st.error("연락처를 입력해 주세요.")
    elif selected_time is None:
        st.error("신청 가능한 날짜와 시간을 선택해 주세요.")
    elif not consent:
        st.error("개인정보 제공 동의가 필요합니다.")
    else:
        now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        row = [
            now,
            student_number.strip(),
            student_name.strip(),
            applicant,
            method,
            selected_date.isoformat(),
            selected_time,
            phone.strip(),
            note.strip(),
        ]
        try:
            if save_request(row):
                st.success(f"{date_label(selected_date)} {selected_time} 상담 신청이 완료되었습니다.")
                st.balloons()
            else:
                st.error("방금 다른 신청자가 해당 시간을 선택했습니다. 새로고침 후 다른 시간을 선택해 주세요.")
        except Exception:
            st.error("신청을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.")

