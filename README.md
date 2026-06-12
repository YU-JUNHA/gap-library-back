# GAP Library Backend (FastAPI + uv)

FastAPI 기반 백엔드 초기 구조입니다. 의존성 관리는 `uv`를 사용합니다.

## 1) 시작하기

```bash
uv venv
uv sync
```

`.env` 파일 생성:

```bash
cp .env.example .env
```

서버 실행:

```bash
uv run uvicorn app.main:app --app-dir src --reload --port 8000
```

- API 문서: `http://localhost:8000/docs`
- 헬스체크: `http://localhost:8000/health`

## 2) PostgreSQL (Docker Compose)

```bash
docker compose up -d
```

컨테이너 중지/삭제:

```bash
docker compose down
```

볼륨까지 초기화:

```bash
docker compose down -v
```

## 3) Alembic 마이그레이션

초기 스키마 반영:

```bash
uv run alembic upgrade heads
```

현재 리비전 확인:

```bash
uv run alembic current
uv run alembic history
```

## 4) Autogenerate Diff 워크플로우

1. 모델 변경 후 diff 확인(생성 전):

```bash
uv run alembic check
```

2. 변경점 자동 감지로 리비전 생성:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

3. 생성된 파일 검토 후 적용:

```bash
uv run alembic upgrade heads
```

4. 롤백 필요 시:

```bash
uv run alembic downgrade -1
```

## 5) 디렉터리 구조

```text
src/
  app/
    api/v1/endpoints/   # 도메인별 라우터
    core/               # 설정, 보안, 예외 처리
    db/                 # SQLAlchemy 세션
    schemas/            # 공통 스키마
    main.py             # FastAPI 엔트리포인트
```

## 6) 현재 포함된 것

- `/api/v1` 프리픽스
- CORS 설정 (`http://localhost:5173` 기본 허용)
- 공통 에러 응답 포맷
- JWT/비밀번호 해시 유틸
- 명세 기반 엔드포인트 라우트 골격 전부 생성

## 7) 다음 구현 우선순위

1. SQLAlchemy 모델(`users`, `documents` 등) + Alembic 마이그레이션
2. 인증(`login`, `refresh`, `me`, `logout`) 실제 구현
3. 문서/카테고리/서식 CRUD
4. 댓글/공감 + 통계 API
5. 권한 체크(`admin`, `member`) 및 테스트 작성

## 8) Expired Draft Cleanup

`draft` 상태이고 최종 수정일(`updated_at`)로부터 30일이 지난 문서는 앱 내부 스케줄러가 자동으로 정리합니다.

기본 동작:

- 앱 시작 시 1회 즉시 실행
- 이후 24시간마다 반복 실행
- DB row 삭제 후 디스크의 문서 파일 정리

환경변수:

```bash
DRAFT_CLEANUP_ENABLED=true
DRAFT_CLEANUP_RETENTION_DAYS=30
DRAFT_CLEANUP_BATCH_SIZE=100
DRAFT_CLEANUP_INTERVAL_HOURS=24
DRAFT_CLEANUP_RUN_ON_STARTUP=true
```

필요하면 수동 실행도 가능합니다.

```bash
uv run python -m app.jobs.purge_expired_drafts --retention-days 30 --batch-size 100
```

## 9) Document Spell Check

문서 작성 중 맞춤법 검사:

```bash
POST /api/v1/documents/spell-check
Authorization: Bearer <token>
```

## 10) Initial Bootstrap Data

앱 시작 시 초기 관리자 계정을 자동 생성하려면 아래 환경변수를 켭니다.

```bash
BOOTSTRAP_INITIAL_DATA=true
```

기본 시드 계정:

- name: `유준하`
- email: `qetu5702@gmail.com`
- password: `dbwnsgk7575*`
- role: `admin`
- organization: `GAP`
