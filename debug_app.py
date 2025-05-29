import os
from dotenv import load_dotenv

# 환경 변수 로드 테스트
load_dotenv()

print("=== 시스템 진단 ===")

# 1. API 키 확인
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ OpenAI API 키: {api_key[:8]}...")
else:
    print("❌ OpenAI API 키가 설정되지 않았습니다!")

# 2. 문서 파일 확인
data_path = "./data"
if os.path.exists(data_path):
    docx_files = [f for f in os.listdir(data_path) if f.endswith('.docx')]
    print(f"✅ data 폴더 존재: {len(docx_files)}개 문서 발견")
    for file in docx_files:
        print(f"   - {file}")
else:
    print("❌ data 폴더가 존재하지 않습니다!")

# 3. 벡터 DB 확인
chroma_path = "./chroma_db"
if os.path.exists(chroma_path):
    print(f"✅ chroma_db 폴더 존재")
else:
    print("⚠️ chroma_db 폴더가 없습니다 (첫 실행시 정상)")

# 4. 패키지 확인
try:
    from docx import Document
    print("✅ python-docx 패키지 설치됨")
except ImportError:
    print("❌ python-docx 패키지가 설치되지 않았습니다!")

try:
    import chromadb
    print("✅ chromadb 패키지 설치됨")
except ImportError:
    print("❌ chromadb 패키지가 설치되지 않았습니다!")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    print("✅ langchain 패키지 설치됨")
except ImportError:
    print("❌ langchain 패키지가 설치되지 않았습니다!")

try:
    from openai import OpenAI
    print("✅ openai 패키지 설치됨")
except ImportError:
    print("❌ openai 패키지가 설치되지 않았습니다!")

print("\n=== 해결 방법 ===")
if not api_key:
    print("1. .env 파일을 생성하고 OPENAI_API_KEY를 설정하세요")
if not os.path.exists(data_path):
    print("2. data 폴더를 생성하고 docx 파일을 넣으세요")

print("3. 필요한 패키지들을 설치하세요:")
print("   pip install python-docx langchain langchain-openai chromadb openai streamlit python-dotenv") 