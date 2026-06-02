# GAP Library Backend API Spec (Implemented)

이 문서는 **현재 백엔드 코드에 구현된 실제 API 동작**을 기준으로 작성되었습니다.
프론트엔드는 이 문서만 보고 연동할 수 있도록 요청/응답/인증/에러/주의사항을 포함합니다.

- Base URL: `http://localhost:8000`
- API Prefix: `/api/v1`
- Swagger: `/docs`
- OpenAPI JSON: `/openapi.json`
- Content-Type: `application/json` (파일 업로드 제외)

---

## 1. 인증

### 1.1 방식
- 보호 API는 `Authorization` 헤더가 필요합니다.
- 형식:
  - `Authorization: Bearer <accessToken>`

### 1.2 토큰
- Access Token 만료: 30분
- Refresh Token 만료: 14일
- Refresh 시 rotate(기존 토큰 revoke + 새 refresh 발급)

### 1.3 Swagger에서 인증
1. `POST /api/v1/auth/login` 호출
2. 응답의 `accessToken` 복사
3. 우측 상단 `Authorize` 클릭
4. `Bearer <accessToken>` 입력

---

## 2. 공통 응답 형식

### 2.1 성공
- 단건: `{ "data": { ... } }`
- 목록: `{ "data": [ ... ], "meta": { ... } }`

### 2.2 실패
```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "설명",
    "details": {}
  }
}
```

주요 코드 예시:
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `VALIDATION_ERROR` (422)
- `CONFLICT` (409)
- `INTERNAL_ERROR` (500)

---

## 3. Auth API

### POST `/api/v1/auth/login`
로그인

Request:
```json
{
  "email": "admin@gap.org",
  "password": "admin1234!"
}
```

Response:
```json
{
  "data": {
    "accessToken": "...",
    "refreshToken": "...",
    "user": {
      "id": "string",
      "name": "string",
      "email": "admin@gap.org",
      "role": "admin",
      "organization": "GAP",
      "avatarUrl": null,
      "createdAt": "2026-06-01T...Z"
    }
  }
}
```

비고:
- 성공 시 `users.last_login_at` 업데이트됩니다.

### POST `/api/v1/auth/refresh`
Request:
```json
{ "refreshToken": "..." }
```
Response:
```json
{
  "data": {
    "accessToken": "...",
    "refreshToken": "..."
  }
}
```

### POST `/api/v1/auth/logout`
Request:
```json
{ "refreshToken": "..." }
```
Response:
```json
{ "data": { "success": true } }
```

### GET `/api/v1/auth/me`
Bearer 필요

Response:
```json
{
  "data": {
    "id": "string",
    "name": "string",
    "email": "string",
    "role": "admin",
    "organization": "string",
    "avatarUrl": "string|null",
    "createdAt": "2026-06-01T...Z"
  }
}
```

---

## 4. Signup Request / Admin Approval

### POST `/api/v1/signup-requests`
Request:
```json
{
  "name": "홍길동",
  "email": "user@gap.org",
  "password": "pass1234",
  "inviteCode": "INVITE-2026"
}
```
Response:
```json
{
  "data": {
    "id": "string",
    "name": "홍길동",
    "email": "user@gap.org",
    "status": "pending",
    "requestedAt": "2026-06-01T...Z"
  }
}
```

### GET `/api/v1/admin/signup-requests`
admin 전용, pending 목록

### POST `/api/v1/admin/signup-requests/{requestId}/approve`
admin 전용
- `users` 계정 자동 생성
- 요청 상태 `approved`

### POST `/api/v1/admin/signup-requests/{requestId}/reject`
admin 전용
- 요청 상태 `rejected`

---

## 5. Users API

### GET `/api/v1/users/me`
Bearer 필요

### PATCH `/api/v1/users/me`
Request:
```json
{
  "name": "새 이름",
  "organization": "GAP",
  "avatarUrl": "https://..."
}
```

### POST `/api/v1/users/me/avatar`
- Content-Type: `multipart/form-data`
- field: `file`
- 서버 로컬 저장 위치: `uploads/avatars/{userId}/{filename}`

Response:
```json
{ "data": { "avatarUrl": "/uploads/avatars/{userId}/{filename}" } }
```

---

## 6. Admin Users API

### GET `/api/v1/admin/users`
admin 전용

Query:
- `q` (name/email 검색)
- `role` (`admin|member`)
- `page` (default 1)
- `pageSize` (default 20)

Response:
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "email": "string",
      "role": "admin",
      "organization": "string|null",
      "avatarUrl": "string|null",
      "createdAt": "2026-06-01T...Z"
    }
  ],
  "meta": { "page": 1, "pageSize": 20, "total": 12 }
}
```

### PATCH `/api/v1/admin/users/{userId}/role`
admin 전용

Request:
```json
{ "role": "admin" }
```

제약:
- 마지막 admin 강등 금지
- 자기 자신 admin 강등 금지

---

## 7. Documents API

### GET `/api/v1/documents`
Query:
- `q`
- `categoryId`
- `ownerId`
- `status` (`draft|published`)
- `page` (default 1)
- `pageSize` (default 20)

### POST `/api/v1/documents`
Bearer 필요

Request:
```json
{
  "title": "새 문서",
  "content": [],
  "categoryId": null,
  "status": "draft"
}
```

### GET `/api/v1/documents/{documentId}`

### PATCH `/api/v1/documents/{documentId}`
Bearer 필요, owner 또는 admin

Request 예시:
```json
{
  "title": "수정 제목",
  "content": [{"type":"paragraph","content":[{"type":"text","text":"본문"}]}],
  "categoryId": "...",
  "summary": "요약",
  "status": "published"
}
```

비고:
- `content` 바뀌면 `contentText` 자동 재생성

### DELETE `/api/v1/documents/{documentId}`
Bearer 필요, owner 또는 admin

### POST `/api/v1/documents/{documentId}/open`
- `lastOpenedAt` 갱신

---

## 8. Categories API

### GET `/api/v1/categories/tree`
Response:
```json
{
  "data": [
    {
      "id": "string",
      "name": "운영",
      "parentId": null,
      "order": 0,
      "createdAt": "...",
      "updatedAt": "..."
    }
  ]
}
```

### POST `/api/v1/categories`
```json
{ "name": "운영", "parentId": null }
```

### PATCH `/api/v1/categories/{categoryId}`
```json
{ "name": "새 이름" }
```

### DELETE `/api/v1/categories/{categoryId}`

### POST `/api/v1/categories/{categoryId}/move`
```json
{
  "newParentId": null,
  "newOrder": 3,
  "includeChildren": true
}
```

---

## 9. Templates API

### GET `/api/v1/templates`
### POST `/api/v1/templates` (Bearer 필요)
Request:
```json
{ "name": "회의록", "content": "# 제목\n본문" }
```

### GET `/api/v1/templates/{templateId}`
### PATCH `/api/v1/templates/{templateId}`
```json
{ "name": "새 이름", "content": "수정 내용" }
```

### DELETE `/api/v1/templates/{templateId}`

### POST `/api/v1/templates/{templateId}/apply`
Request:
```json
{ "documentId": "doc-id" }
```

현재 구현 동작:
- 템플릿 `content(markdown 문자열)`을 문서 `content`에 paragraph 1개 형태로 반영
- `contentText`도 템플릿 문자열로 갱신

---

## 10. Reactions / Comments API

### POST `/api/v1/documents/{documentId}/reactions`
Bearer 필요
```json
{ "type": "like" }
```

### DELETE `/api/v1/documents/{documentId}/reactions`
Bearer 필요

### GET `/api/v1/documents/{documentId}/reactions`
Bearer 필요
Response:
```json
{ "data": { "likeCount": 10, "likedByMe": true } }
```

### GET `/api/v1/documents/{documentId}/comments`
Response:
```json
{
  "data": [
    {
      "id": "string",
      "documentId": "string",
      "authorId": "string",
      "content": "좋은 문서입니다.",
      "createdAt": "...",
      "updatedAt": "..."
    }
  ]
}
```

### POST `/api/v1/documents/{documentId}/comments`
Bearer 필요
```json
{ "content": "좋은 문서입니다." }
```

### PATCH `/api/v1/comments/{commentId}`
Bearer 필요, author 또는 admin
```json
{ "content": "수정된 댓글" }
```

### DELETE `/api/v1/comments/{commentId}`
Bearer 필요, author 또는 admin

---

## 11. Stats API

### GET `/api/v1/stats/dashboard`
Bearer 필요

Response:
```json
{
  "data": {
    "totalDocuments": 120,
    "myDocuments": 18,
    "recentEditedDocuments": [
      { "id": "doc-1", "title": "...", "updatedAt": "...", "ownerName": "ownerId" }
    ],
    "uploadTrend": {
      "unit": "week",
      "points": [
        { "label": "2026-W20", "userName": "ownerId", "count": 5 }
      ]
    }
  }
}
```

### GET `/api/v1/stats/mypage`
Bearer 필요

Response:
```json
{
  "data": {
    "uploadedFileCount": 24,
    "recentUploads": [
      { "documentId": "doc-3", "title": "...", "updatedAt": "..." }
    ],
    "myUploadTrend": {
      "unit": "month",
      "points": [
        { "label": "2026-01", "count": 3 }
      ]
    }
  }
}
```

---

## 12. 프론트 연동 체크리스트

1. 로그인 성공 후 `accessToken` 메모리/스토리지 저장
2. 모든 보호 API에 `Authorization: Bearer <accessToken>` 첨부
3. 401 시 `refreshToken`으로 `/auth/refresh` 호출 후 access 재시도
4. `content`는 JSON 그대로 round-trip
5. 날짜는 ISO 문자열로 렌더링
6. 관리자 화면은 admin 계정으로만 접근

---

## 13. 현재 구현상 주의사항 (프론트 참고)

1. 템플릿 apply는 markdown 정교 파싱이 아니라 단순 paragraph 반영입니다.
2. avatar 업로드는 로컬 파일 저장 방식입니다 (S3/MinIO 아님).
3. 통계의 `ownerName/userName`은 현재 user id 기반으로 채워집니다.
4. 카테고리/템플릿 권한은 현재 완전한 admin 제한이 아니라 기본 접근 가능 형태입니다(필요 시 정책 강화 가능).

---

## 14. 빠른 테스트 시나리오

1. `POST /signup-requests` 생성
2. admin 로그인
3. `POST /admin/signup-requests/{id}/approve`
4. 승인된 계정 로그인
5. 문서 생성 -> 댓글/공감 -> 템플릿 적용 -> 통계 조회

