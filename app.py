from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st


START_DATE = date(2026, 7, 27)
END_DATE = date(2026, 8, 7)
START_HOURS = (12, 13, 14, 15)
TIMEZONE = ZoneInfo("Asia/Seoul")


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


def script_url() -> str:
    return str(st.secrets["apps_script_url"]).strip()


def reserved_slots(selected_date: date) -> set[str]:
    response = requests.get(
        script_url(), params={"date": selected_date.isoformat()}, timeout=10
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("message", "예약 정보를 불러오지 못했습니다."))
    return set(payload.get("reserved", []))


def save_request(payload: dict) -> tuple[bool, str]:
    response = requests.post(script_url(), json=payload, timeout=15)
    response.raise_for_status()
    result = response.json()
    return bool(result.get("ok")), str(result.get("message", ""))


st.set_page_config(page_title="학생·학부모 상담 신청", page_icon="📅", layout="centered")
st.title("학생·학부모 상담 신청")
st.caption("상담 기간: 2026년 7월 27일(월) ~ 8월 7일(금), 평일 12:00~16:00")
st.info("상담은 한 시간 단위로 진행됩니다. 학부모 상담은 가급적 전화 상담을 권장합니다.")

try:
    script_url()
except Exception:
    st.error("상담 신청 저장소가 아직 설정되지 않았습니다.")
    st.stop()

student_name = st.text_input("학생 이름", placeholder="학생 이름을 정확히 입력해 주세요.", max_chars=20)
st.caption("학번은 입력한 이름을 비공개 명렬표와 확인하여 자동으로 기록됩니다.")

applicant = st.radio("신청자", ["학생 본인", "부", "모", "부·모 모두"], horizontal=True)
if applicant != "학생 본인":
    st.info("학부모 상담은 이동 부담을 줄이기 위해 전화 상담을 권장합니다.")

method = st.radio("상담 방식", ["전화 상담", "대면 상담"], horizontal=True)
available_dates = weekdays_between(START_DATE, END_DATE)
selected_date = st.selectbox("상담 희망 날짜", available_dates, format_func=date_label)

try:
    occupied = reserved_slots(selected_date)
    available_slots = [slot_label(hour) for hour in START_HOURS if slot_label(hour) not in occupied]
except Exception:
    available_slots = []
    st.error("현재 예약 현황을 불러오지 못했습니다. 잠시 후 새로고침해 주세요.")

if available_slots:
    selected_time = st.selectbox("상담 희망 시간", available_slots)
else:
    selected_time = None
    st.warning("선택한 날짜에는 남은 상담 시간이 없습니다. 다른 날짜를 선택해 주세요.")

phone = st.text_input("연락처", placeholder="전화 상담 또는 일정 확인에 사용할 번호")
note = st.text_area("상담 희망 내용", placeholder="상담하고 싶은 내용을 간단히 적어 주세요.", height=120)
consent = st.checkbox("상담 신청을 위해 위 개인정보를 제공하는 데 동의합니다.")
submitted = st.button("상담 신청", type="primary", use_container_width=True)

if submitted:
    if not student_name.strip():
        st.error("학생 이름을 입력해 주세요.")
    elif not phone.strip():
        st.error("연락처를 입력해 주세요.")
    elif selected_time is None:
        st.error("신청 가능한 날짜와 시간을 선택해 주세요.")
    elif not consent:
        st.error("개인정보 제공 동의가 필요합니다.")
    else:
        payload = {
            "submitted_at": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
            "student_name": student_name.strip(),
            "applicant": applicant,
            "method": method,
            "date": selected_date.isoformat(),
            "time": selected_time,
            "phone": phone.strip(),
            "note": note.strip(),
        }
        try:
            ok, message = save_request(payload)
            if ok:
                st.success(f"{date_label(selected_date)} {selected_time} 상담 신청이 완료되었습니다.")
                st.balloons()
            else:
                st.error(message or "해당 시간이 이미 신청되었습니다. 다른 시간을 선택해 주세요.")
        except Exception:
            st.error("신청을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.")
