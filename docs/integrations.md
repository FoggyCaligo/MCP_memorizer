# 호스트 에이전트 통합 계약

MCP_memorizer는 자체 추론 모델을 포함하지 않는다. 호스트 에이전트가 사실 추출에 사용할 모델 어댑터, 인증된 사용자 식별자, 응답 확정 시점과 오류 처리 방법을 제공한다.

## 공통 경계

- 모델에게 공개하는 MCP 도구는 **읽기 전용 `memory_search`**다. 모델 호출 인수로 `user_id`를 선택하게 하지 않는다.
- 쓰기는 최종 답변이 확정된 **후**에 호스트가 추출기·기억 저장 API를 호출한다. 스트리밍 중간 출력이나 임시 답변을 확정 답변으로 간주하지 않는다.
- 추출기는 호스트가 제공하는 `extract(messages, schema)` 비동기 어댑터를 사용하며, 추출 프롬프트는 `mcp_memorizer/extraction/prompt.py`가 소유한다.
- MCP 검색만 연결한 호스트는 **자동 저장이 보장되지 않는다**. 응답 완료 생명주기 연동이 필요하다.
- 사용자별 DB·실행 오류·개인 데이터 백업은 해당 호스트의 관리 정책이 우선한다.

[엔진 구조](architecture.md), [기억 검색](recall.md), [사실 추출](extraction.md), [Sentence_Breaker 연동](sentence-breaker.md)을 참고한다.

## MAI

현재 MAI의 `dev`는 외부 `MCP_memorizer` 패키지를 실제 의존성으로 사용한다. 모델에 노출하는 검색 도구는 `memorizer__memory_search`이고, MAI의 MCP Connection Manager가 서버 발견·도구 활성화를 담당한다. 메모리 사용자 ID는 로그인 권한과 `db_id`에서 유도하며 모델 호출 인수로 노출하지 않는다.

응답 확정 후 사실 추출과 저장은 MAI의 `mai/app/runtime.py`에서 독립 패키지 서비스를 호출하는 비동기 후처리로 관리한다. **MAI가 SDK 예시의 `Memorizer.after_response`를 그대로 호출하는 것과 동등하다고 추측하면 안 된다.** 실제 런타임 호출·기록 방식과 SDK API는 구분한다.

이 패키지에 `mcp_memorizer.integrations.mai.MAIExtractionAdapter` 및 과거 네이티브 도구 등록용 `register_memory_search_tool` 헬퍼가 남아 있지만, **현재 MAI의 모델 가시 경로는 MCP 서버 네임스페이스 도구**다. 네이티브 헬퍼의 존재가 MAI에서 해당 경로를 활성화했다는 뜻은 아니다.

MAI 전용 사용자·Verifier·실행 순서 정책은 [MAI 기억 연동](https://github.com/FoggyCaligo/MAI_MyAI_sllm/blob/dev/docs/memory.md), MCP 활성화 계약은 [MAI MCP 문서](https://github.com/FoggyCaligo/MAI_MyAI_sllm/blob/dev/docs/mcp-lazy-loading.md)를 따른다.

## Hermes

`integrations/hermes/`에는 실험적인 일반 플러그인이 포함되어 있다. `post_llm_call`의 최종 응답 성공 시점과 구조화 출력 함수를 사용하려는 설계이며, 도구 실행 성공 여부를 독립적으로 확인하지 못하면 도구 근거를 추가하지 않는다. 사용자 설치 경로·Hermes 자체 도구와의 충돌 문제를 검토해야 한다.

**실제 Hermes 호스트에서 종단간 검증을 완료했다는 의미는 아니다.** 모델·플러그인 이벤트·배포 버전에 따라 실제 호환성을 별도 확인해야 한다.

## OpenClaw

읽기 전용 도구 연동 외에 `agent_end` 등 확정된 종료 이벤트에서 답변 후 저장 작업을 준비해야 한다. 프로세스가 살아 있을 것이라 가정해 일시적인 종료 콜백만으로 정확히 한 번 저장을 보장하지 않는다. 이미 다른 기억 플러그인이 있다면 중복 저장이나 공유 DB 충돌을 명시적으로 처리한다.

이 설명은 **연동 설계**이며 기본 설치된 완성 플러그인의 작동 검증 결과가 아니다.

## DeepSeek Harness

Cordis 기반 플러그인 또는 세션 이벤트 구조를 사용해 검색 도구와 응답 확정 시점을 연결할 수 있다. 구체적인 이벤트 계약과 도구 API는 설치한 Harness 버전에서 재검증해야 한다. 스트리밍 출력이 끝났다는 사실만으로 저장 확정을 추정하지 않는다.

이 설명도 **설계 방향**이지 실제 연동 검증 완료를 의미하지 않는다.

## 데이터 보안·내구성

인증된 호스트가 사용자별 메모리 식별자를 설정해야 한다. 모델이 지정한 임의 ID·세션 키를 그대로 신뢰하지 않는다. 재시작 후 작업 복원과 중복 저장 방지는 영속적인 완료 기록 및 멱등성 키가 필요하며, 현재 프로세스 내부 deduplication만으로 장애 상황의 정확히 한 번 기록을 보장할 수 없다. 개인 대화 DB는 호스트 소유이며 공개 저장소로 옮기지 않는다.
