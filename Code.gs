const SPREADSHEET_ID = '여기에_관리_시트_ID를_입력하세요';
const SHEET_NAME = '신청내역';
const ROSTER_SHEET_NAME = '학생명렬';
const ALLOWED_DATES = [
  '2026-07-27', '2026-07-28', '2026-07-29', '2026-07-30', '2026-07-31',
  '2026-08-03', '2026-08-04', '2026-08-05', '2026-08-06', '2026-08-07'
];
const ALLOWED_TIMES = ['12:00 ~ 13:00', '13:00 ~ 14:00', '14:00 ~ 15:00', '15:00 ~ 16:00'];
const ALLOWED_APPLICANTS = ['학생 본인', '부', '모', '부·모 모두'];
const ALLOWED_METHODS = ['전화 상담', '대면 상담'];

function jsonResponse(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function sheet() {
  return SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
}

function rosterSheet() {
  return SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(ROSTER_SHEET_NAME);
}

function findStudent(name) {
  const normalized = String(name || '').trim();
  if (!normalized) return null;
  const rows = rosterSheet().getDataRange().getDisplayValues().slice(1);
  const match = rows.find(row => String(row[1] || '').trim() === normalized);
  return match ? {number: String(match[0] || '').trim(), name: String(match[1] || '').trim()} : null;
}

function safeText(value, maxLength) {
  let text = String(value || '').trim().slice(0, maxLength);
  if (/^[=+\-@]/.test(text)) text = "'" + text;
  return text;
}

function doGet(e) {
  const requestedDate = String((e.parameter || {}).date || '');
  if (!ALLOWED_DATES.includes(requestedDate)) {
    return jsonResponse({ok: false, message: '허용되지 않은 상담 날짜입니다.'});
  }
  const values = sheet().getDataRange().getDisplayValues();
  const reserved = values.slice(1)
    .filter(row => row[5] === requestedDate)
    .map(row => row[6])
    .filter(time => ALLOWED_TIMES.includes(time));
  return jsonResponse({ok: true, reserved: [...new Set(reserved)]});
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const data = JSON.parse((e.postData || {}).contents || '{}');
    const isCustom = data.schedule_type === '다른 일정 요청';
    const customSchedule = safeText(data.custom_schedule, 100);
    if (isCustom && !customSchedule) {
      return jsonResponse({ok: false, message: '기타 희망 일정을 입력해 주세요.'});
    }
    if (!isCustom && (!ALLOWED_DATES.includes(data.date) || !ALLOWED_TIMES.includes(data.time))) {
      return jsonResponse({ok: false, message: '허용되지 않은 상담 날짜 또는 시간입니다.'});
    }
    if (!ALLOWED_APPLICANTS.includes(data.applicant) || !ALLOWED_METHODS.includes(data.method)) {
      return jsonResponse({ok: false, message: '신청자 또는 상담 방식이 올바르지 않습니다.'});
    }
    const studentName = safeText(data.student_name, 20);
    const student = findStudent(studentName);
    const phone = safeText(data.phone, 30);
    if (!student || !phone) {
      return jsonResponse({ok: false, message: '명렬표의 학생 이름과 연락처를 정확히 입력해 주세요.'});
    }

    lock.waitLock(10000);
    const target = sheet();
    const rows = target.getDataRange().getDisplayValues();
    const duplicate = !isCustom && rows.slice(1).some(row => row[5] === data.date && row[6] === data.time);
    if (duplicate) {
      return jsonResponse({ok: false, message: '방금 다른 신청자가 해당 시간을 선택했습니다.'});
    }
    target.appendRow([
      safeText(data.submitted_at, 30), student.number, student.name, data.applicant,
      data.method, isCustom ? '' : data.date, isCustom ? '기타 일정 요청' : data.time,
      phone, safeText(data.note, 1000), customSchedule
    ]);
    return jsonResponse({ok: true});
  } catch (error) {
    return jsonResponse({ok: false, message: '신청을 처리하지 못했습니다.'});
  } finally {
    try { lock.releaseLock(); } catch (error) {}
  }
}
