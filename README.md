# 학생·학부모 상담 신청 Streamlit 앱

2026년 7월 27일부터 8월 7일까지 평일 상담을 신청받는 앱입니다. 상담 시간은 12:00부터 16:00까지 한 시간 단위이며, 같은 시간의 중복 신청을 막습니다.

## 신청 항목

- 학번과 학생 이름
- 신청자: 학생 본인, 부, 모, 부·모 모두
- 상담 방식: 전화 상담, 대면 상담
- 상담 날짜와 시간
- 연락처와 상담 희망 내용

학부모 신청 화면에는 전화 상담 권장 안내가 표시됩니다.

## Google Sheet 준비

1. 상담 신청을 저장할 비공개 Google Sheet를 만듭니다.
2. Google Cloud에서 서비스 계정을 만들고 Google Sheets API를 활성화합니다.
3. 서비스 계정 이메일에 해당 시트의 편집 권한을 부여합니다.
4. `.streamlit/secrets.toml.example`을 참고해 Streamlit Community Cloud의 **Secrets**에 `sheet_url`과 서비스 계정 정보를 등록합니다.

서비스 계정 인증키는 GitHub 저장소에 커밋하지 마세요. 실제 `secrets.toml`은 `.gitignore`에 포함되어 있습니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

## Streamlit Community Cloud 배포

1. 이 폴더를 비공개 GitHub 저장소에 올립니다.
2. Streamlit Community Cloud에서 저장소와 `app.py`를 선택합니다.
3. 앱 설정의 Secrets에 Google 서비스 계정 정보를 입력합니다.
4. 생성된 앱 링크를 학생과 학부모에게 공유합니다.

