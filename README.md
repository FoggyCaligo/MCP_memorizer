# MCP_memorizer — 독립 SQLite 장기기억 엔진

MAI에서 분리된 독립 기억 엔진이다. **검색 전용 MCP 도구**와 **최종 응답 확정 후 호스트가 호출하는 사실 추출·저장 SDK**를 제공한다.

메모리 그래프·개념 색인·조회·추출 구현은 이 저장소가 소유한다. 문자 경로 기반 분해기는 별도 원본 프로젝트인 [FoggyCaligo/Sentence_Breaker](https://github.com/FoggyCaligo/Sentence_Breaker)를 의존성으로 사용한다. Sentence_Breaker 역시 동일 개발자의 별도 프로젝트이며, 단순히 외부 의존성이라는 이유로 개발 주체가 다른 것은 아니다.

## 설치

```bash
git clone https://github.com/FoggyCaligo/MCP_memorizer.git
cd MCP_memorizer
git switch dev
pip install -e '.[mcp]'
python -m mcp_memorizer.mcp_server
```

Python 3.11 이상과 SQLite FTS5가 필요하다. `Sentence_Breaker`는 이 패키지의 의존성이며 호스트 에이전트가 직접 그 알고리즘을 구현할 필요는 없다.

## 기본 데이터 위치

독립 패키지 기본 경로는 `Memory_data/memory.sqlite3` 및 `Memory_data/sentence_breaker.sqlite3`다. 호스트 애플리케이션은 경로를 별도로 제공할 수 있으며 **MAI는 자신의 별도 개인 DB 경로를 사용**한다. 공개 Git에 개인정보가 담긴 SQLite 파일을 커밋하지 않는다.

## 읽기: MCP `memory_search`

```python
from mcp_memorizer import Memorizer

memory = Memorizer(data_dir="./Memory_data", user_id="local-user")
memory.search(keyword="project plans", limit=10)
memory.search(limit=10)
memory.search(node_id=123)
```

표준 입력/출력(stdio) 서버는 `python -m mcp_memorizer.mcp_server`로 실행한다. `MEMORIZER_USER_ID`, `MEMORIZER_DATA_DIR`를 호스트가 바인딩하며, 모델이 다른 사용자의 ID를 임의로 제공하도록 노출하지 않는다.

## 쓰기: 최종 응답 이후 호스트 호출

모델에게 `memory_save` 도구를 노출하지 않는다. 호스트가 최종 답변 확정 후 추출기와 저장 함수를 호출한다.

```python
from mcp_memorizer import Memorizer, ModelFactExtractor

class Adapter:
    async def extract(self, messages, schema):
        # 호스트 모델의 구조화 응답 호출
        ...

memory = Memorizer(extractor=ModelFactExtractor(Adapter()))
await memory.after_response(
    user_text=user_text,
    previous_assistant_message=previous_assistant_message,
    final_answer=final_answer,
    successful_tool_results=successful_non_recall_results,
)
```

이것은 **SDK 사용 예시**이며 모든 호스트의 실제 비동기 작업 구현이 같다는 뜻은 아니다. 오류를 숨기지 않으며, 프로세스 중단 후 정확히 한 번 기록을 재개하는 영속 큐는 보장하지 않는다.

## 연동 상태

MAI의 현재 `dev`는 이 패키지를 의존성으로 설치하고, 메모리 검색을 `memorizer__memory_search` MCP 도구로 제공한다. 응답 확정 후의 사실 추출·저장은 MAI 호스트 런타임이 독립 패키지를 호출해 관리한다. 따라서 과거 개발 알파 README에 있던 **“MAI가 아직 이 패키지로 전환되지 않았다”**는 설명은 더 이상 현재 MAI의 상태가 아니다.

Hermes 일반 플러그인은 실험적이며 실사용 검증이 완료됐다는 뜻이 아니다. OpenClaw 및 DeepSeek Harness의 호스트 생명주기 연동은 별도 구현·검증이 필요하다.

## 상세 문서

- [메모리 엔진 구조](docs/architecture.md)
- [검색·순위·확장](docs/recall.md)
- [사실 추출·저장](docs/extraction.md)
- [Sentence_Breaker 연동](docs/sentence-breaker.md)
- [호스트 에이전트 연동](docs/integrations.md)
- [Sentence_Breaker 원본 알고리즘](https://github.com/FoggyCaligo/Sentence_Breaker/blob/dev/docs/algorithm.md)

원본 MAI 프로젝트: [FoggyCaligo/MAI_MyAI_sllm](https://github.com/FoggyCaligo/MAI_MyAI_sllm). 라이선스: AGPL-3.0-only. Sentence_Breaker의 독립 라이선스는 해당 원본 저장소에서 확인한다.
