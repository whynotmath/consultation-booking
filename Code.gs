const SPREADSHEET_ID = '여기에_관리_시트_ID를_입력하세요';
const SHEET_NAME = '신청내역';
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
    if (!ALLOWED_DATES.includes(data.date) || !ALLOWED_TIMES.includes(data.time)) {
      return jsonResponse({ok: false, message: '허용되지 않은 상담 날짜 또는 시간입니다.'});
    }
    if (!ALLOWED_APPLICANTS.includes(data.applicant) || !ALLOWED_METHODS.includes(data.method)) {
      return jsonResponse({ok: false, message: '신청자 또는 상담 방식이 올바르지 않습니다.'});
    }
    const studentNumber = safeText(data.student_number, 10);
    const studentName = safeText(data.student_name, 20);
    const phone = safeText(data.phone, 30);
    if (!studentNumber || !studentName || !phone) {
      return jsonResponse({ok: false, message: '학번, 학생 이름, 연락처를 모두 입력해 주세요.'});
    }

    lock.waitLock(10000);
    const target = sheet();
    const rows = target.getDataRange().getDisplayValues();
    const duplicate = rows.slice(1).some(row => row[5] === data.date && row[6] === data.time);
    if (duplicate) {
      return jsonResponse({ok: false, message: '방금 다른 신청자가 해당 시간을 선택했습니다.'});
    }
    target.appendRow([
      safeText(data.submitted_at, 30), studentNumber, studentName, data.applicant,
      data.method, data.date, data.time, phone, safeText(data.note, 1000)
    ]);
    return jsonResponse({ok: true});
  } catch (error) {
    return jsonResponse({ok: false, message: '신청을 처리하지 못했습니다.'});
  } finally {
    try { lock.releaseLock(); } catch (error) {}
  }
}
