# 기억 검색·회수 계약

이 문서는 **MCP_memorizer 엔진**의 조회 알고리즘과 입력 계약을 설명한다. MAI의 `tool_manual`·이름 접두사 등은 [외부 연동](integrations.md)에서 다룬다.

## MCP `memory_search` 입력

| 입력 | 의미 |
|---|---|
| `keyword` + 선택적 양수 `limit` | 주제별 Fact/Utterance 조회, 최종 기억 개수 제한 |
| 선택자 없는 `limit` | 최근 목록. 명시적 `limit` 필수, 1~50 |
| `node_id` | 노드의 한 단계 이웃과 해당 사용자 Anchor 경로 확장 |

`node_id`와 `keyword`·`limit`을 함께 지정할 수 없다. 사용자 식별자는 호스트에서 바인딩하며 모델에게 `user_id` 인자를 주지 않는다.

## 주제 검색

```text
검색어 공백 분리 → 중복 검색 조각 제거
 → 조각별 Concept exact·SQLite FTS5 검색
 → 점수 높은 Concept 후보(기본 최대 12개)
 → 해당 Concept의 mentions 연결 노드
 → 사용자 소유 Fact·Utterance 선별
 → 최고 hit 점수·첫 발견 순서로 정렬
 → 선택적 limit 적용
 → 사용자 Anchor까지 경로 합성 → WorkingGraph
```

- 개념은 문자열 정확 일치 및 FTS5 어휘 인덱스로 찾는다. 임베딩 의미 유사도 검색은 제공하지 않는다.
- Concept 후보는 최고 점수를 우선하며, 동점에는 검색 순서와 노드 ID의 구조화된 순서가 적용된다.
- Concept 주변의 `mentions` 관계에 **실제로 연결된** Fact/Utterance만 수집한다. 이웃에 노드가 존재하기만 해서는 회수되지 않는다.
- 각 노드의 `payload.user_id`를 검사해 소유 범위를 좁힌다. Fact 점수는 연결된 후보 hit의 최고 점수이며 동점은 최초 발견 순서다.
- `limit`은 **Concept 후보 수가 아닌 최종 기억 순위**에 적용한다. 생략하면 일치 기억 전체가 대상이다.
- 노드에 대한 사용자 Anchor 최단 경로를 합성한다. 검색 결과에 Anchor의 일반 목록을 임의로 추가하지 않는다.

## 최근 목록

사용자 기준점에 `spoke` 또는 `asserted_fact`로 직접 연결된 기억을 `last_seen_at DESC, id DESC`로 조회한다. 검색어 일치를 요구하지 않지만 제한된 목록은 전체 기억과 같지 않다.

## 확장과 작업 그래프

`node_id` 지정 시 이웃 및 해당 사용자 Anchor와의 경로를 수집하고 요청 내 WorkingGraph에 합성한다. Anchor 확장은 별도 제한된 최근 내용 경로를 사용한다. 다른 사용자의 Anchor 확장은 차단한다.

모델에 전달되는 메모리 출력에서는 Fact·과거 Utterance와 `node_id`/`node_type`/`data`/`created_at`/`provenance`/`evidence_id` 등 내용 위주 필드를 노출하며 Concept 내부 연결은 숨길 수 있다. 새로운 Fact의 `evidence_id`는 비어 있을 수 있다.

## 시간·정정

조회 알고리즘은 **서로 모순되는 Fact들의 의미적 승자를 자동으로 판정하지 않는다**. `created_at`과 `last_seen_at`은 역할이 다르며, 최근 조회 순위가 곧 사실의 우선권은 아니다. 현재 사용자의 직접 정정·시간 범위는 호스트 모델/검증기의 정책으로 판단한다.

## 오류와 한계

검색 결과가 없으면 실제 기억 부재를 확정할 수 없다. FTS5 손상·사용자 범위 오류를 무시하거나 다른 결과로 조용히 우회하지 않는다. 한계, 계정 격리 및 영속성은 [엔진 구조](architecture.md)를 참고한다.
