# SQLite3 호환성 패치 (Streamlit Cloud용)
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import uuid

class VectorStore:
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "chuncheon_regulations",
                 openai_api_key: str = None):
        """
        벡터 스토어 초기화
        
        Args:
            persist_directory: 벡터 DB 저장 경로
            collection_name: 컬렉션 이름
            openai_api_key: OpenAI API 키
        """
        print(f"🔍 [DEBUG] VectorStore 초기화 시작")
        print(f"🔍 [DEBUG] persist_directory: {persist_directory}")
        print(f"🔍 [DEBUG] collection_name: {collection_name}")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # OpenAI 임베딩 모델 초기화
        try:
            print(f"🔍 [DEBUG] OpenAI 임베딩 모델 초기화 시작")
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=openai_api_key,
                model="text-embedding-3-small"
            )
            print(f"✅ [SUCCESS] OpenAI 임베딩 모델 초기화 완료")
        except Exception as e:
            print(f"❌ [ERROR] OpenAI 임베딩 모델 초기화 오류: {str(e)}")
            raise
        
        # Chroma 클라이언트 초기화
        try:
            print(f"🔍 [DEBUG] Chroma 클라이언트 초기화 시작")
            abs_path = os.path.abspath(persist_directory)
            print(f"🔍 [DEBUG] 절대 경로: {abs_path}")
            print(f"🔍 [DEBUG] 디렉토리 존재 여부: {os.path.exists(abs_path)}")
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(abs_path):
                print(f"🔍 [DEBUG] 디렉토리 생성 시도: {abs_path}")
                os.makedirs(abs_path, exist_ok=True)
                print(f"✅ [SUCCESS] 디렉토리 생성 완료")
            
            # 쓰기 권한 확인
            if os.access(abs_path, os.W_OK):
                print(f"✅ [SUCCESS] 디렉토리 쓰기 권한 확인")
            else:
                print(f"⚠️ [WARNING] 디렉토리 쓰기 권한 없음")
            
            self.client = chromadb.PersistentClient(path=persist_directory)
            print(f"✅ [SUCCESS] Chroma 클라이언트 초기화 완료")
        except Exception as e:
            print(f"❌ [ERROR] Chroma 클라이언트 초기화 오류: {str(e)}")
            print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
            import traceback
            print(f"🔍 [DEBUG] 스택 트레이스: {traceback.format_exc()}")
            raise
        
        # 벡터 스토어 초기화
        self.vectorstore = None
        self._initialize_vectorstore()
        print(f"🎉 [SUCCESS] VectorStore 초기화 완료")
    
    def _initialize_vectorstore(self):
        """벡터 스토어 초기화"""
        try:
            print(f"🔍 [DEBUG] _initialize_vectorstore 시작")
            
            # 기존 컬렉션이 있다면 로드
            collections = self.client.list_collections()
            print(f"🔍 [DEBUG] 기존 컬렉션 수: {len(collections)}")
            
            if collections:
                for col in collections:
                    print(f"🔍 [DEBUG] 기존 컬렉션: {col.name}")
            
            collection_exists = any(col.name == self.collection_name for col in collections)
            print(f"🔍 [DEBUG] 타겟 컬렉션 '{self.collection_name}' 존재 여부: {collection_exists}")
            
            if collection_exists:
                print(f"🔍 [DEBUG] 기존 컬렉션 로드 시도")
                self.vectorstore = Chroma(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
                print(f"✅ [SUCCESS] 기존 컬렉션 '{self.collection_name}'을 로드했습니다.")
            else:
                print(f"ℹ️ [INFO] 새로운 컬렉션 '{self.collection_name}'을 생성합니다.")
                
        except Exception as e:
            print(f"❌ [ERROR] 벡터 스토어 초기화 오류: {str(e)}")
            print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
            import traceback
            print(f"🔍 [DEBUG] 스택 트레이스: {traceback.format_exc()}")
    
    def add_documents(self, documents: List[Dict[str, str]]) -> bool:
        """
        문서들을 벡터 스토어에 추가 (배치 처리)
        
        Args:
            documents: 문서 리스트 (content와 metadata 포함)
            
        Returns:
            성공 여부
        """
        try:
            print(f"🔍 [DEBUG] add_documents 시작, 문서 수: {len(documents)}")
            
            if not documents:
                print("⚠️ [WARNING] 추가할 문서가 없습니다.")
                return False
            
            # Langchain Document 객체로 변환
            docs = []
            for i, doc in enumerate(documents):
                try:
                    langchain_doc = Document(
                        page_content=doc['content'],
                        metadata=doc['metadata']
                    )
                    docs.append(langchain_doc)
                except Exception as e:
                    print(f"❌ [ERROR] 문서 {i} 변환 오류: {str(e)}")
                    continue
            
            print(f"🔍 [DEBUG] Langchain Document 변환 완료: {len(docs)}개")
            
            # 배치 크기 설정 (토큰 한계를 고려하여 50개씩 처리)
            batch_size = 50
            total_docs = len(docs)
            
            print(f"📚 [INFO] 총 {total_docs}개 문서를 {batch_size}개씩 배치로 처리합니다...")
            
            # 벡터 스토어가 없다면 첫 번째 배치로 새로 생성
            if self.vectorstore is None:
                print(f"🔍 [DEBUG] 새로운 벡터 스토어 생성")
                first_batch = docs[:batch_size]
                print(f"🔍 [DEBUG] 첫 번째 배치 크기: {len(first_batch)}")
                
                try:
                    self.vectorstore = Chroma.from_documents(
                        documents=first_batch,
                        embedding=self.embeddings,
                        client=self.client,
                        collection_name=self.collection_name
                    )
                    print(f"✅ [SUCCESS] 새로운 벡터 스토어를 생성하고 {len(first_batch)}개 문서를 추가했습니다.")
                    
                    # 나머지 문서들을 배치로 처리
                    remaining_docs = docs[batch_size:]
                except Exception as e:
                    print(f"❌ [ERROR] 벡터 스토어 생성 오류: {str(e)}")
                    print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
                    import traceback
                    print(f"🔍 [DEBUG] 스택 트레이스: {traceback.format_exc()}")
                    return False
            else:
                remaining_docs = docs
            
            # 나머지 문서들을 배치 단위로 추가
            for i in range(0, len(remaining_docs), batch_size):
                batch_num = i//batch_size + 1
                batch = remaining_docs[i:i + batch_size]
                print(f"🔍 [DEBUG] 배치 {batch_num} 처리 시작: {len(batch)}개 문서")
                
                try:
                    self.vectorstore.add_documents(batch)
                    print(f"✅ [SUCCESS] 배치 {batch_num}: {len(batch)}개 문서 추가 완료")
                except Exception as e:
                    print(f"❌ [ERROR] 배치 {batch_num} 추가 오류: {str(e)}")
                    print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
                    return False
            
            print(f"🎉 [SUCCESS] 총 {total_docs}개 문서가 성공적으로 추가되었습니다.")
            return True
            
        except Exception as e:
            print(f"❌ [ERROR] add_documents 전체 오류: {str(e)}")
            print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
            import traceback
            print(f"🔍 [DEBUG] 스택 트레이스: {traceback.format_exc()}")
            return False
    
    def search_similar_documents(self, 
                               query: str, 
                               k: int = 5,
                               score_threshold: float = 0.7) -> List[Dict]:
        """
        유사한 문서 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            score_threshold: 유사도 임계값
            
        Returns:
            검색 결과 리스트
        """
        try:
            if self.vectorstore is None:
                print("벡터 스토어가 초기화되지 않았습니다.")
                return []
            
            # 유사도 검색 실행
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query, k=k
            )
            
            results = []
            for doc, score in docs_with_scores:
                # 점수를 유사도로 변환 (Chroma는 거리를 반환하므로)
                # 거리가 클수록 유사도가 낮아야 하므로 1/(1+score) 방식 사용
                similarity = 1 / (1 + score)
                
                if similarity >= score_threshold:
                    results.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'similarity': similarity
                    })
            
            print(f"검색 결과: {len(results)}개 문서 (임계값: {score_threshold})")
            return results
            
        except Exception as e:
            print(f"검색 오류: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        컬렉션 통계 정보 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        try:
            if self.vectorstore is None:
                return {'총_문서수': 0}
            
            # 컬렉션 정보 가져오기
            collection = self.client.get_collection(self.collection_name)
            count = collection.count()
            
            return {'총_문서수': count}
            
        except Exception as e:
            print(f"통계 정보 조회 오류: {str(e)}")
            return {'총_문서수': 0}
    
    def clear_collection(self) -> bool:
        """
        컬렉션의 모든 문서 삭제
        
        Returns:
            성공 여부
        """
        try:
            print(f"🔍 [DEBUG] clear_collection 시작")
            print(f"🔍 [DEBUG] persist_directory: {self.persist_directory}")
            print(f"🔍 [DEBUG] collection_name: {self.collection_name}")
            
            collections = self.client.list_collections()
            print(f"🔍 [DEBUG] 기존 컬렉션 수: {len(collections)}")
            
            collection_exists = any(col.name == self.collection_name for col in collections)
            print(f"🔍 [DEBUG] 타겟 컬렉션 존재 여부: {collection_exists}")
            
            if collection_exists:
                print(f"🔍 [DEBUG] 컬렉션 '{self.collection_name}' 삭제 시작")
                self.client.delete_collection(self.collection_name)
                print(f"✅ [SUCCESS] 컬렉션 '{self.collection_name}'을 삭제했습니다.")
            else:
                print(f"ℹ️ [INFO] 삭제할 컬렉션이 없습니다.")
            
            # 벡터 스토어 재초기화
            self.vectorstore = None
            self._initialize_vectorstore()
            
            print(f"✅ [SUCCESS] clear_collection 완료")
            return True
            
        except Exception as e:
            print(f"❌ [ERROR] 컬렉션 삭제 오류: {str(e)}")
            print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
            import traceback
            print(f"🔍 [DEBUG] 스택 트레이스: {traceback.format_exc()}")
            return False
    
    def update_documents(self, documents: List[Dict[str, str]]) -> bool:
        """
        문서 업데이트 (기존 문서 삭제 후 새로 추가)
        
        Args:
            documents: 새로운 문서 리스트
            
        Returns:
            성공 여부
        """
        try:
            print(f"🔍 [DEBUG] update_documents 시작, 문서 수: {len(documents)}")
            
            # 기존 컬렉션 삭제
            print(f"🔍 [DEBUG] 기존 컬렉션 삭제 시작")
            clear_result = self.clear_collection()
            print(f"🔍 [DEBUG] clear_collection 결과: {clear_result}")
            
            if clear_result:
                # 새 문서들 추가
                print(f"🔍 [DEBUG] 새 문서 추가 시작")
                add_result = self.add_documents(documents)
                print(f"🔍 [DEBUG] add_documents 결과: {add_result}")
                return add_result
            else:
                print(f"❌ [ERROR] 컬렉션 삭제 실패로 인한 업데이트 중단")
                return False
            
        except Exception as e:
            print(f"❌ [ERROR] update_documents 오류: {str(e)}")
            print(f"🔍 [DEBUG] 오류 타입: {type(e).__name__}")
            import traceback
            print(f"🔍 [DEBUG] 스택 트레이스: {traceback.format_exc()}")
            return False 