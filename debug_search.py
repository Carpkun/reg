import os
from dotenv import load_dotenv
from vector_store import VectorStore

# 환경 변수 로드
load_dotenv()

# API 키 확인
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ OpenAI API 키가 설정되지 않았습니다!")
    exit()

print("=== 벡터 검색 디버깅 ===")

# 벡터 스토어 초기화
vector_store = VectorStore(openai_api_key=api_key)

# 테스트 쿼리
test_query = "강의실 사용 규칙"
print(f"🔍 검색 쿼리: '{test_query}'")

try:
    # 원시 검색 결과 확인 (임계값 없이)
    if vector_store.vectorstore is None:
        print("❌ 벡터 스토어가 초기화되지 않았습니다!")
        exit()
    
    # similarity_search_with_score로 직접 검색
    docs_with_scores = vector_store.vectorstore.similarity_search_with_score(
        test_query, k=5
    )
    
    print(f"\n📊 원시 검색 결과 ({len(docs_with_scores)}개):")
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        similarity = 1 - score  # 기존 변환 방식
        print(f"{i}. 원시 점수: {score:.4f}")
        print(f"   변환된 유사도: {similarity:.4f}")
        print(f"   문서: {doc.metadata.get('source', 'Unknown')}")
        print(f"   내용 미리보기: {doc.page_content[:100]}...")
        print()
    
    # 다른 유사도 변환 방식들 시도
    print("🧪 다양한 유사도 변환 방식:")
    for i, (doc, score) in enumerate(docs_with_scores[:3], 1):
        print(f"{i}번 문서 (원시 점수: {score:.4f}):")
        print(f"   방식1 (1-score): {1-score:.4f}")
        print(f"   방식2 (1/(1+score)): {1/(1+score):.4f}")
        print(f"   방식3 (exp(-score)): {2.718**(-score):.4f}")
        print(f"   방식4 (그대로): {score:.4f}")
        print()
        
    # 임계값 0.0으로 실제 검색 테스트
    print("🔍 임계값 0.0으로 검색 테스트:")
    results = vector_store.search_similar_documents(test_query, k=5, score_threshold=0.0)
    print(f"결과: {len(results)}개")
    
    if results:
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. 유사도: {result['similarity']:.4f}")
            print(f"   출처: {result['metadata']['source']}")
            print()
    else:
        print("❌ 임계값 0.0에서도 결과 없음!")
        
except Exception as e:
    print(f"❌ 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc() 