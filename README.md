# 춘천문화원 규정 검색 시스템

춘천문화원의 규정 문서들을 검색하고 질의응답할 수 있는 AI 기반 시스템입니다.

## 기능
- docx 형식의 규정 문서 자동 처리
- OpenAI 임베딩을 이용한 의미론적 검색
- Google Gemini 2.0 Flash를 활용한 질의응답
- Streamlit 기반의 사용자 친화적 웹 인터페이스

## 설치 방법

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정:
`.env` 파일을 생성하고 API 키들을 추가:
```
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

## API 키 발급 방법

### OpenAI API 키 (임베딩용)
1. [OpenAI 공식 사이트](https://platform.openai.com/) 접속
2. 계정 생성 또는 로그인
3. 우측 상단 프로필 클릭 → "View API keys" 선택
4. "Create new secret key" 클릭하여 새 API 키 생성
5. 생성된 키를 복사하여 `.env` 파일에 저장

### Google AI Studio API 키 (LLM용)
1. [Google AI Studio](https://aistudio.google.com/) 접속
2. Google 계정으로 로그인
3. "Get API key" 클릭
4. "Create API key" 선택하여 새 프로젝트 또는 기존 프로젝트에서 키 생성
5. 생성된 키를 복사하여 `.env` 파일에 저장

## 사용 방법

1. `data` 폴더에 검색하고 싶은 docx 파일들을 추가
2. 시스템 실행:
```bash
streamlit run app.py
```
3. 웹 브라우저에서 http://localhost:8501 접속
4. "문서 인덱싱" 버튼을 클릭하여 문서들을 벡터DB에 저장
5. 질문을 입력하여 규정 내용 검색

## 디렉토리 구조
```
reg/
├── app.py              # Streamlit 메인 애플리케이션
├── document_processor.py  # 문서 처리 모듈
├── vector_store.py     # 벡터 스토어 관리
├── requirements.txt    # 의존성
├── .env               # 환경 변수 (API 키)
├── data/              # 규정 문서들 (docx 파일)
└── chroma_db/         # 벡터 데이터베이스 저장소 