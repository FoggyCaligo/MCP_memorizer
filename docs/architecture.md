# 메모리 엔진 구조와 책임

MCP_memorizer는 MAI에서 출발해 독립 패키지로 분리된 **SQLite 기반 장기기억 엔진**이다. 그래프·사실 추출·개념 색인·회수·작업 그래프의 구현을 소유한다. MAI는 이 엔진을 사용하는 **호스트 에이전트**이며, 개인 대화 DB·로그인·최종 응답 확정·원격 도구는 MAI의 책임이다.

## 구성

```text
호스트 에이전트(예: MAI)
 ├─ 최종 답변 확정 후 추출기 호출 → 사실 목록
 ├─ 사용자별 DB 경로·정체성 제공
 └─ MCP read-only memory_search 호출
              │
        MCP_memorizer
 ├─ 추출: 팩트 JSON 계약·실행 서비스
 ├─ Graph: 기준점·Fact·Concept·Evidence·관계 저장
 ├─ Index: exact + SQLite FTS5
 ├─ Recall: 개념 후보 → 사용자 소유 기억 회수
 ├─ WorkingGraph: 조회 결과 누적·모델 출력
 └─ Segmenter → 독립 Sentence_Breaker
```

## 데이터 모델

| 구성 요소 | 의미 |
|---|---|
| 사용자 Anchor | 사용자별 검색·저장 경계. MAI 로그인 ID와 별도로 전달받는 `user_id` 사용 |
| Fact | 승인된 입력에서 추출한 재사용 가능한 사용자 사실 |
| Concept | Sentence_Breaker가 만드는 정규화 조각, 검색 좌표 |
| Evidence | 사용자 원문 등 독립적인 근거 기록 |
| Utterance | 기존 데이터에 존재할 수 있는 과거 발화 노드 |
| WorkingGraph | 요청별 회수 노드·관계와 확장 상태 |

주요 테이블은 `nodes`, `user_anchors`, `edges`, `evidence`, `memory_concept_exact`, `memory_concept_fts`다. 사용자→Fact는 `asserted_fact`, Fact/Utterance→Concept는 `mentions` 관계로 연결한다. 관계 방향·출처는 런타임의 구조화 로직이 결정하며, 모델 출력에서 받은 임의 관계를 실행하지 않는다.

기준점의 식별은 `anchor:user:<user_id>` 형태로 이뤄진다. 간선 중복은 `from_node_id`, `to_node_id`, `relation` 조합을 기준으로 방지한다. 원문 Evidence를 저장했다고 해서 **각 Fact가 Evidence 번호를 통해 완전히 역추적된다는 뜻은 아니다.**

## 사실 저장

호스트가 완료된 응답과 근거를 전달하면 메모리 엔진은 [추출·저장](extraction.md)의 계약으로 Facts를 결정하고 사용자 기준점에 저장한다. Fact의 Concept 연결은 [Sentence_Breaker 연동](sentence-breaker.md)을 참고한다. 같은 정규화 Concept는 재사용하며, Fact 동일성은 현재 정확 문자열 기준이다. 의미가 비슷하다는 이유만으로 Fact를 자동 병합하거나 서로 다른 시점의 사실을 삭제하지 않는다.

## 조회

[검색·회수](recall.md)에 설명한 대로 `keyword`, `limit` 목록, `node_id` 확장 모드를 제공한다. 최근 목록과 어휘 검색은 다르다. 엔진 검색이 의미적 충돌의 자동 해결이나 임베딩 검색을 보장하지 않는다.

## 외부 프로젝트 경계

- **Sentence_Breaker:** 독립 원본 프로젝트 [FoggyCaligo/Sentence_Breaker](https://github.com/FoggyCaligo/Sentence_Breaker). 작성자 `bigla`; 이 패키지는 어댑터를 통해 사용한다.
- **MAI:** [MAI 연동](integrations.md). 모델 선택, 사용자 권한·런타임 DB 경로, 비동기 실행, MCP 도구 카탈로그와 최종 답변 검증을 소유한다.
- **그 밖의 에이전트:** 별도 어댑터가 최종 응답 확정 시점과 계정 경계를 제공해야 한다. 검색 MCP만 연결한다고 자동 저장 수명주기가 생기지는 않는다.

## 구현 위치

| 범위 | 파일 |
|---|---|
| 그래프 스키마·저장소 | `mcp_memorizer/memory/graph/schema.py`, `repository.py` |
| 기억 실행 | `mcp_memorizer/memory/runtime.py` |
| 사실 추출 | `mcp_memorizer/extraction/prompt.py`, `mcp_memorizer/memory/extraction/` |
| 색인 | `mcp_memorizer/memory/index/` |
| 검색 | `mcp_memorizer/memory/recall/service.py` |
| 작업 그래프 | `mcp_memorizer/memory/working.py` |
| 분해기 어댑터 | `mcp_memorizer/memory/segmenter.py` |

## 한계

기억 검색 결과가 비었다고 실제 기억이 없다는 뜻은 아니다. 표현 차이·인덱스 범위·사용자 범위·상한 때문일 수 있다. 다중 사용자 그래프 경계의 추가 보안 감사, 재시작 후 자동 저장의 영속 큐 및 장애 후 정확히 한 번 저장 보장은 별도 검증·구현 대상이다.
