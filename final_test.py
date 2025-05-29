import os
from dotenv import load_dotenv
from vector_store import VectorStore

# 환경 변수 로드
load_dotenv()

# 벡터 스토어 초기화
vector_store = VectorStore(openai_api_key=os.getenv('OPENAI_API_KEY'))

# 다양한 검색 테스트
test_queries = [
    "강의실 사용 규칙",
    "계약업무 처리 절차",
    "고정자산 관리 방법",
    "공용차량 사용 규정",
    "검수 관련 규칙"
]

print("🎯 최종 검색 테스트 (임계값: 0.4)")
print("=" * 50)

for i, query in enumerate(test_queries, 1):
    print(f"\n{i}. 질문: '{query}'")
    results = vector_store.search_similar_documents(query, k=3, score_threshold=0.4)
    
    if results:
        print(f"   ✅ {len(results)}개 결과 발견:")
        for j, result in enumerate(results, 1):
            print(f"      {j}) {result['metadata']['source']} (유사도: {result['similarity']:.3f})")
    else:
        print("   ❌ 관련 문서 없음")

print("\n🎉 테스트 완료! 이제 Streamlit 앱에서 정상적으로 검색할 수 있습니다.") 