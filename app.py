# SQLite3 호환성 패치 (Streamlit Cloud용)
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import os
import hashlib
import json
from dotenv import load_dotenv
from typing import List, Dict
import time
from openai import OpenAI
import google.generativeai as genai

from document_processor import DocumentProcessor
from vector_store import VectorStore

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="춘천문화원 규정 검색 시스템",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 (최소한으로 간소화)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

def get_documents_hash(data_folder: str = "./data") -> str:
    """data 폴더의 문서들로부터 해시값 생성"""
    if not os.path.exists(data_folder):
        return ""
    
    docx_files = [f for f in os.listdir(data_folder) if f.endswith('.docx')]
    if not docx_files:
        return ""
    
    # 파일명과 수정시간을 조합해서 해시 생성
    file_info = []
    for filename in sorted(docx_files):
        file_path = os.path.join(data_folder, filename)
        mtime = os.path.getmtime(file_path)
        file_info.append(f"{filename}:{mtime}")
    
    content = "|".join(file_info)
    return hashlib.md5(content.encode()).hexdigest()

def is_vectorstore_up_to_date() -> bool:
    """벡터 스토어가 최신 상태인지 확인"""
    hash_file = "./chroma_db/documents_hash.json"
    current_hash = get_documents_hash()
    
    if not os.path.exists(hash_file):
        return False
    
    try:
        with open(hash_file, 'r') as f:
            saved_data = json.load(f)
            return saved_data.get('hash') == current_hash
    except:
        return False

def save_documents_hash():
    """현재 문서 해시를 저장"""
    hash_file = "./chroma_db/documents_hash.json"
    current_hash = get_documents_hash()
    
    os.makedirs("./chroma_db", exist_ok=True)
    with open(hash_file, 'w') as f:
        json.dump({'hash': current_hash}, f)

def initialize_session_state():
    """세션 상태 초기화"""
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'document_processor' not in st.session_state:
        st.session_state.document_processor = DocumentProcessor()
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = None
    if 'gemini_model' not in st.session_state:
        st.session_state.gemini_model = None
    if 'indexed_documents' not in st.session_state:
        st.session_state.indexed_documents = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def check_api_keys():
    """API 키 확인 및 설정"""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    
    missing_keys = []
    
    if not openai_api_key or openai_api_key == 'your_openai_api_key_here':
        missing_keys.append("OpenAI")
    
    if not google_api_key or google_api_key == 'your_google_api_key_here':
        missing_keys.append("Google")
    
    if missing_keys:
        st.error(f"⚠️ {', '.join(missing_keys)} API 키가 설정되지 않았습니다!")
        st.info("""
        **API 키 설정 방법:**
        1. `.env` 파일을 생성하고 다음과 같이 입력하세요:
        ```
        OPENAI_API_KEY=your_actual_openai_api_key_here
        GOOGLE_API_KEY=your_actual_google_api_key_here
        ```
        2. OpenAI API 키: https://platform.openai.com/api-keys
        3. Google AI Studio API 키: https://aistudio.google.com/app/apikey
        """)
        return None, None
    
    return openai_api_key, google_api_key

def initialize_components(openai_api_key: str, google_api_key: str):
    """시스템 컴포넌트 초기화"""
    try:
        st.write("🔍 [DEBUG] initialize_components 시작")
        
        if st.session_state.vector_store is None:
            st.write("🔍 [DEBUG] VectorStore 생성 시작")
            st.write(f"🔍 [DEBUG] OpenAI API 키 존재: {bool(openai_api_key)}")
            st.write(f"🔍 [DEBUG] OpenAI API 키 길이: {len(openai_api_key) if openai_api_key else 0}")
            
            try:
                # VectorStore 생성 시도
                st.write("🔍 [DEBUG] VectorStore 객체 생성 시도...")
                vector_store = VectorStore(openai_api_key=openai_api_key)
                st.write("✅ [SUCCESS] VectorStore 객체 생성 완료")
                st.session_state.vector_store = vector_store
                st.write("✅ [SUCCESS] VectorStore 세션 상태에 저장 완료")
            except Exception as e:
                st.error(f"❌ [ERROR] VectorStore 생성 실패: {str(e)}")
                st.write(f"🔍 [DEBUG] VectorStore 오류 타입: {type(e).__name__}")
                st.write(f"🔍 [DEBUG] VectorStore 오류 상세: {e}")
                import traceback
                st.code(traceback.format_exc())
                return False
        else:
            st.write("ℹ️ [INFO] 기존 VectorStore 사용")
        
        if st.session_state.openai_client is None:
            st.write("🔍 [DEBUG] OpenAI 클라이언트 생성 시작")
            try:
                st.session_state.openai_client = OpenAI(api_key=openai_api_key)
                st.write("✅ [SUCCESS] OpenAI 클라이언트 생성 완료")
            except Exception as e:
                st.error(f"❌ [ERROR] OpenAI 클라이언트 생성 실패: {str(e)}")
                return False
        else:
            st.write("ℹ️ [INFO] 기존 OpenAI 클라이언트 사용")
        
        if st.session_state.gemini_model is None:
            st.write("🔍 [DEBUG] Gemini 모델 초기화 시작")
            try:
                genai.configure(api_key=google_api_key)
                st.session_state.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                st.write("✅ [SUCCESS] Gemini 모델 초기화 완료")
            except Exception as e:
                st.error(f"❌ [ERROR] Gemini 모델 초기화 실패: {str(e)}")
                return False
        else:
            st.write("ℹ️ [INFO] 기존 Gemini 모델 사용")
        
        st.write("🎉 [SUCCESS] 모든 컴포넌트 초기화 완료")
        return True
    except Exception as e:
        st.error(f"❌ [ERROR] 시스템 초기화 전체 오류: {str(e)}")
        st.write(f"🔍 [DEBUG] 전체 오류 타입: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return False

def index_documents():
    """문서 인덱싱 실행"""
    with st.spinner("문서를 처리하고 있습니다..."):
        # 디버깅: 파일 시스템 상태 확인
        import os
        st.write(f"🔍 현재 작업 디렉토리: {os.getcwd()}")
        
        data_path = "./data"
        st.write(f"🔍 data 폴더 경로: {os.path.abspath(data_path)}")
        st.write(f"🔍 data 폴더 존재 여부: {os.path.exists(data_path)}")
        
        if os.path.exists(data_path):
            files = os.listdir(data_path)
            docx_files = [f for f in files if f.endswith('.docx')]
            st.write(f"🔍 data 폴더 내 전체 파일 수: {len(files)}")
            st.write(f"🔍 data 폴더 내 docx 파일 수: {len(docx_files)}")
            if docx_files:
                st.write(f"🔍 첫 번째 docx 파일: {docx_files[0]}")
        else:
            st.error(f"❌ data 폴더가 존재하지 않습니다: {os.path.abspath(data_path)}")
            return False
        
        # 문서 처리
        try:
            documents = st.session_state.document_processor.process_documents(data_path)
            st.write(f"🔍 처리된 문서 청크 수: {len(documents) if documents else 0}")
        except Exception as e:
            st.error(f"❌ 문서 처리 중 오류: {str(e)}")
            st.write(f"🔍 오류 상세: {type(e).__name__}: {e}")
            return False
        
        if not documents:
            st.warning("⚠️ data 폴더에 처리할 docx 파일이 없거나 문서 처리에 실패했습니다.")
            return False
        
        # 벡터 스토어에 추가
        try:
            success = st.session_state.vector_store.update_documents(documents)
            st.write(f"🔍 벡터 스토어 업데이트 결과: {success}")
        except Exception as e:
            st.error(f"❌ 벡터 스토어 업데이트 중 오류: {str(e)}")
            st.write(f"🔍 오류 상세: {type(e).__name__}: {e}")
            return False
        
        if success:
            st.session_state.indexed_documents = True
            st.success(f"✅ {len(documents)}개의 문서 청크가 성공적으로 인덱싱되었습니다!")
            
            # 통계 정보 표시
            stats = st.session_state.document_processor.get_document_stats(documents)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 문서 수", stats['총_문서수'])
            with col2:
                st.metric("총 청크 수", stats['총_청크수'])
            with col3:
                st.metric("평균 청크 길이", f"{stats['평균_청크길이']} 문자")
            with col4:
                st.metric("총 문자 수", f"{stats['총_문자수']:,}")
            
            return True
        else:
            st.error("❌ 문서 인덱싱에 실패했습니다.")
            return False

def generate_answer(query: str, search_results: List[Dict]) -> str:
    """검색 결과를 바탕으로 답변 생성"""
    if not search_results:
        return "죄송합니다. 관련된 규정을 찾을 수 없습니다."
    
    # 컨텍스트 구성 (파일명 제외, 내용만 포함)
    context = "\n\n".join([
        result['content']
        for result in search_results
    ])
    
    # 프롬프트 구성
    prompt = f"""
주어진 춘천문화원 규정 문서들을 바탕으로 질문에 답변해주세요.

**질문:** {query}

**관련 규정 내용:**
{context}

**답변 가이드라인:**
1. 주어진 규정 내용만을 바탕으로 답변하세요
2. 구체적인 조항명, 조문, 항목 등 근거가 되는 조항은 명확히 인용해주세요
3. 예: "제3조 제2항에 따르면...", "운영규정 제15조에서..."
4. 정확한 정보가 없다면 "해당 내용을 찾을 수 없습니다"라고 답변하세요
5. 친절하고 이해하기 쉽게 설명해주세요
6. 파일명이나 문서명은 절대 언급하지 마세요
7. "안녕하세요", "춘천문화원 규정 전문가입니다" 등의 인사말은 사용하지 마세요
8. 바로 답변 내용으로 시작하세요

**답변:**
"""
    
    try:
        response = st.session_state.gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1000,
                candidate_count=1
            )
        )
        
        return response.text
        
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"

def main():
    """메인 애플리케이션 - Streamlit 기본 기능 활용"""
    # 세션 상태 초기화
    initialize_session_state()
    
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>📋 춘천문화원 규정 검색 시스템</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # API 키 확인
    openai_api_key, google_api_key = check_api_keys()
    if not openai_api_key or not google_api_key:
        return
    
    # 컴포넌트 초기화
    if not initialize_components(openai_api_key, google_api_key):
        return
    
    # 스마트 문서 인덱싱 (필요한 경우에만 실행)
    if not st.session_state.indexed_documents:
        # 기존 벡터 스토어가 최신 상태인지 확인
        if is_vectorstore_up_to_date() and st.session_state.vector_store and st.session_state.vector_store.get_collection_stats().get('총_문서수', 0) > 0:
            # 기존 벡터 스토어 사용
            st.session_state.indexed_documents = True
            st.success("✅ 기존 인덱싱 데이터를 로드했습니다! 바로 검색을 시작할 수 있습니다.")
        else:
            # 새로 인덱싱 필요
            with st.spinner("📚 문서를 인덱싱하고 있습니다... (최초 1회 또는 문서 변경 시)"):
                success = index_documents()
                if success:
                    save_documents_hash()  # 해시 저장
                    st.success("✅ 문서 인덱싱이 완료되었습니다! 이제 검색을 시작할 수 있습니다.")
                else:
                    st.error("❌ 문서 인덱싱에 실패했습니다. data 폴더에 docx 파일이 있는지 확인해주세요.")
    
    # 검색 설정 기본값
    search_k = 5
    similarity_threshold = 0.4
    
    # 사이드바
    with st.sidebar:
        st.subheader("⚙️ 설정")
        
        # 초기화 버튼
        if st.button("🔄 대화 기록 초기화", use_container_width=True, type="secondary"):
            st.session_state.chat_history = []
            st.success("✅ 대화 기록이 초기화되었습니다!")
            st.rerun()
        
        st.divider()
        
        # 도움말
        st.subheader("💡 사용 방법")
        st.info("""
        💬 **Streamlit 채팅 인터페이스**
        
        1. 하단 채팅창에 질문 입력
        2. 엔터키로 검색 실행
        3. 답변이 채팅 형태로 표시
        4. 대화 기록 자동 누적
        """)
    
    # 채팅 메시지 표시 (Streamlit 기본 채팅 기능 사용)
    st.subheader("💬 규정 검색 채팅")
    
    # 채팅 기록 표시
    for message in st.session_state.chat_history:
        # 사용자 질문
        with st.chat_message("user"):
            st.write(message["query"])
        
        # AI 답변
        with st.chat_message("assistant"):
            if message["answer"].startswith("관련된 규정을 찾을 수 없습니다"):
                st.warning(message["answer"])
            else:
                st.write(message["answer"])
    
    # 채팅 입력창 (Streamlit 기본 기능 - 하단 고정)
    if prompt := st.chat_input("춘천문화원 규정에 대해 질문하세요..."):
        # 사용자 입력 즉시 표시
        with st.chat_message("user"):
            st.write(prompt)
        
        # AI 답변 생성 및 표시
        with st.chat_message("assistant"):
            if not st.session_state.indexed_documents:
                st.error("문서 인덱싱이 아직 완료되지 않았습니다. 잠시 후 다시 시도해주세요.")
            else:
                with st.spinner("검색 중..."):
                    # 유사 문서 검색
                    search_results = st.session_state.vector_store.search_similar_documents(
                        prompt, k=search_k, score_threshold=similarity_threshold
                    )
                    
                    if search_results:
                        # 답변 생성
                        answer = generate_answer(prompt, search_results)
                        st.write(answer)
                    else:
                        answer = "관련된 규정을 찾을 수 없습니다. 다른 키워드로 검색해보세요."
                        st.warning(answer)
                    
                    # 채팅 기록에 추가
                    st.session_state.chat_history.append({
                        "query": prompt,
                        "answer": answer,
                        "timestamp": time.time()
                    })

if __name__ == "__main__":
    main() 