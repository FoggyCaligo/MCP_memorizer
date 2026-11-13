# Sentence_Breaker 연동과 알고리즘 소유권

**Sentence_Breaker는 같은 개발자가 별도 저장소에서 개발한 독립 알고리즘·패키지다.** 저장소: [FoggyCaligo/Sentence_Breaker](https://github.com/FoggyCaligo/Sentence_Breaker). 프로젝트 `pyproject.toml`의 작성자는 `bigla`로 기재되어 있다.

알고리즘의 **원본 구조·문자 경로·동적 계획법·동점 순서·학습 순서·독립 DB**에 관한 권위 문서는 [Sentence_Breaker 알고리즘](https://github.com/FoggyCaligo/Sentence_Breaker/blob/dev/docs/algorithm.md)이다. 여기서는 MCP_memorizer가 그 결과를 어떻게 쓰는지만 설명한다.

## 연결 구조

`mcp_memorizer/memory/segmenter.py`의 `SentenceBreakerSegmenter`는 `sentence_breaker.LanguageGraph`를 생성한다. 호스트에서 전달받은 `db_path`가 있으면 명시적으로 사용하고, 없으면 라이브러리 기본 경로를 따른다.

- `segment(text)`는 공백만 있는 입력을 거부한다.
- `LanguageGraph.segment_text` 결과에서 공백만 있는 조각은 제외한다.
- 나머지 조각은 Concept 생성에 쓰이며, Graph의 Fact/Utterance와 `mentions`로 연결될 수 있다.
- `close()`는 분해기가 사용하는 연결을 종료한다.

분해기 자체 DB는 Concept 그래프 DB와 별개다. **이미 학습된 경로를 재현하려면 분해기 누적 DB도 함께 보존**해야 한다. MAI 설치에서는 사용자별 `sentence_breaker.sqlite3` 경로를 별도로 제공하며, 독립 MCP_memorizer의 기본 데이터 경로와 혼동하지 않는다.

## 구현 경계

- Sentence_Breaker: 문자 경로 분할 알고리즘, 누적 DB 스키마, 분할 API
- MCP_memorizer: 분할 결과 Concept 정규화·연결·FTS5 검색 색인
- MAI 등 호스트: 실제 DB 위치, 사용자 권한, 응답 종료 후 호출 시점

Sentence_Breaker의 [LANG_GRAPH_LAYER_DESIGN.md](https://github.com/FoggyCaligo/Sentence_Breaker/blob/dev/LANG_GRAPH_LAYER_DESIGN.md)는 향후 설계 아이디어도 포함한다. 해당 설계의 모든 선택적 기능이 현재 구현된 것으로 설명하지 않는다.

## 성능·오류

매우 긴 입력 및 많은 과거 연결에서는 계산량이 증가할 수 있다. 알고리즘 변경은 Sentence_Breaker 저장소에서 구현 및 회귀 검증해야 하며, MCP_memorizer가 입력 문자열을 임의 휴리스틱으로 조각 내어 대체하면 안 된다. 누적 DB나 종속성 로딩 실패를 조용히 무시하지 않는다.
