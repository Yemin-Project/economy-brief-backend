# Financial News Morning Brief MVP

네이버 뉴스 경제 섹션의 **헤드라인 뉴스만** 수집하고, 제목·설명문을 OpenAI 모델에 전달해 오늘의 경제 이슈를 Markdown 리포트로 생성하는 MVP입니다.

> 현재 목표: 뉴스 수집 → LLM 이슈 요약 → Markdown 리포트 생성을 안정적으로 완성한다.

## 흐름

```text
네이버 경제 섹션 헤드라인 10건 수집
→ 제목·설명문·출처·링크 정규화
→ OpenAI Structured Outputs로 이슈 1~5개 생성
→ 관련 기사 링크를 포함한 Markdown 리포트 저장
```

페이지에 섞여 있는 연재, 시세, AiRS 추천 뉴스는 수집하지 않습니다. 경제 섹션에서 편집 우선순위가 반영된 헤드라인만 사용합니다.

## 현재 구현 상태

| 기능 | 상태 | 설명 |
| --- | --- | --- |
| 네이버 경제 헤드라인 수집 | 완료 | `section/101`의 헤드라인 카드 10건을 수집한다. |
| 기사 메타데이터 정리 | 완료 | 제목, 설명문, 언론사, URL, 관련 뉴스 클러스터 수, 노출 순서를 추출한다. |
| LLM 경제 이슈 분석 | 완료 | 헤드라인을 같은 이슈로 묶고 핵심 이슈를 최대 5개 생성한다. |
| 관련 기사 링크 연결 | 완료 | LLM은 기사 ID만 반환하고, 애플리케이션이 원래 URL로 연결한다. |
| Markdown 리포트 저장 | 완료 | 실행마다 기사 원본 JSON과 리포트 Markdown을 `outputs/`에 저장한다. |
| 크롤러 파서 테스트 | 완료 | 샘플 HTML을 기반으로 헤드라인 추출을 검증한다. |

실제 실행으로 경제 헤드라인 10건 수집과 OpenAI 기반 리포트 생성까지 확인했습니다.

## 프로젝트 구조

```text
app/
  collector.py  # 네이버 경제 섹션 헤드라인 수집·정규화
  analyzer.py   # OpenAI 호출 및 구조화된 이슈 생성
  report.py     # Markdown 리포트 렌더링
  main.py       # 전체 실행 흐름
tests/
  test_collector.py
outputs/         # 실행 결과 (Git 제외)
```

## 시작하기

Python 3.11 이상을 권장합니다.

프로젝트를 내려받거나 복제한 폴더로 이동합니다.

```bash
cd mvp
```

처음 한 번만 가상환경을 만들고 필요한 패키지를 설치합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` 파일에서 OpenAI API 키와 모델을 설정합니다.

```env
OPENAI_API_KEY=발급받은-API-키
OPENAI_MODEL=gpt-5-nano
```

`gpt-5-nano`는 이 MVP의 기사 분류·요약 작업에 사용하기 좋은 저비용 기본 모델입니다.

이후부터는 새 터미널을 열 때마다 먼저 가상환경을 활성화하세요. `python`이 프로젝트의 `.venv` 경로를 가리키는지 확인한 다음 실행합니다.

```bash
cd mvp
source .venv/bin/activate
which python
python -m app.main
```

`which python`의 결과 끝부분은 아래와 같아야 합니다.

```text
mvp/.venv/bin/python
```

만약 가상환경 활성화가 되지 않거나 `openai` 모듈을 찾지 못한다면, 활성화 없이 아래 명령으로도 실행할 수 있습니다.

```bash
.venv/bin/python -m app.main
```

성공하면 `outputs/`에 아래 두 파일이 생성됩니다.

```text
articles_YYYYMMDD_HHMMSS.json
morning_brief_YYYYMMDD_HHMMSS.md
```

## 리포트 생성 기준

LLM에는 기사 본문 전체가 아니라 아래 메타데이터를 전달합니다.

```text
기사 ID, 헤드라인 여부, 노출 순서, 제목, 설명문, 언론사, 관련 뉴스 수
```

LLM은 JSON 형식으로 다음 결과만 반환합니다.

```text
overall_summary
issues[]
  - keyword
  - importance
  - summary
  - related_article_ids
```

요약은 전체 및 이슈별로 4문장으로 생성합니다. 입력 기사에 없는 사실이나 수치, 투자 매수·매도 의견은 작성하지 않도록 프롬프트를 제한했습니다.

## 검증

크롤링 파서의 기본 검증은 다음처럼 실행합니다.

```bash
python -m pytest
```

정상 실행 예시:

```text
경제 섹션 헤드라인을 수집합니다...
헤드라인 10건을 수집했습니다.
LLM으로 경제 브리프를 생성합니다...
완료: outputs/morning_brief_YYYYMMDD_HHMMSS.md
```

## 로컬 API

FastAPI 서버는 저장된 Markdown 리포트를 프론트엔드에 전달하고, 필요할 때 새 리포트 생성을 요청할 수 있는 로컬 HTTP 인터페이스입니다.

가상환경을 활성화한 뒤 서버를 실행합니다.

```bash
source .venv/bin/activate
uvicorn app.api:app --reload
```

서버가 실행되면 Swagger UI에서 모든 API를 버튼으로 테스트할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

### `GET /health`

서버가 실행 중인지 확인합니다. 외부 뉴스 수집이나 OpenAI 호출은 하지 않습니다.

```json
{"status": "ok"}
```

### `POST /batch/run`

새 Morning Brief를 생성합니다.

```text
네이버 경제 헤드라인 수집
→ OpenAI 요약 생성
→ outputs/에 JSON·Markdown 저장
→ 생성 파일명 반환
```

이 요청은 외부 뉴스 수집과 OpenAI API 호출을 수행하므로 실행 시간과 API 비용이 발생합니다.

응답 예시:

```json
{
  "status": "completed",
  "article_count": 10,
  "articles_file": "articles_YYYYMMDD_HHMMSS.json",
  "report_file": "morning_brief_YYYYMMDD_HHMMSS.md"
}
```

### `GET /reports/latest`

`outputs/` 폴더에서 가장 최근에 생성된 Markdown 리포트를 찾아 프론트엔드에 반환합니다. 리포트 생성이나 외부 API 호출은 하지 않습니다.

```json
{
  "filename": "morning_brief_YYYYMMDD_HHMMSS.md",
  "created_at": "2026-08-17T07:00:00+09:00",
  "content": "# 경제 Morning Brief..."
}
```

리포트가 아직 없으면 `404 Not Found`를 반환합니다.

### 터미널에서 테스트하기

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/reports/latest
curl -X POST http://127.0.0.1:8000/batch/run
```

## Docker Compose 실행

Docker Desktop을 실행한 뒤, 프로젝트 폴더에서 아래 명령으로 API를 컨테이너로 실행합니다.

```bash
docker compose up --build
```

백그라운드 실행은 아래 명령을 사용합니다.

```bash
docker compose up --build -d
```

컨테이너가 실행된 뒤에도 API 주소는 동일합니다.

```text
http://127.0.0.1:8000/docs
```

`outputs/` 폴더는 컨테이너와 로컬 폴더를 공유합니다. 따라서 `POST /batch/run`으로 생성한 Markdown·JSON 리포트는 컨테이너를 종료해도 로컬 `outputs/`에 남습니다.

컨테이너 중지는 다음과 같이 합니다.

```bash
docker compose down
```

## 현재 범위

- 헤드라인 메타데이터 기반 이슈 요약만 제공
- 본문 크롤링 없음
- 데이터베이스와 스케줄러 없음
- FastAPI로 상태 확인, 리포트 생성, 최신 리포트 조회 제공
- 기사 카드의 제목·설명문에만 근거하므로, 세부 사실을 본문과 교차 검증하지 않음

## 다음 단계

1. 기사와 리포트를 PostgreSQL에 저장
2. 스케줄러로 매일 자동 실행
3. 대표 기사 본문을 추가 수집해 요약 정확도 비교
