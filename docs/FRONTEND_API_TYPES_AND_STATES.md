# Frontend API Types and State Values

이 문서는 프론트엔드가 백엔드와 연동할 때 바로 사용할 수 있도록
**API 타입, 쿼리 파라미터, 응답 형태, 상태값(enum)**
를 정리한 문서입니다.

- Base URL: `http://localhost:8000`
- API Prefix: `/api/v1`
- 공통 응답: `{ data, meta? }`
- 파일 업로드: `multipart/form-data`

---

## 1. 공통 타입

### 1.1 API 응답 래퍼

```ts
type ApiResponse<T> = {
  data: T;
};

type ListResponse<T, M = PaginationMeta> = {
  data: T[];
  meta: M;
};
```

### 1.2 에러 응답

백엔드는 FastAPI 표준 `detail` 응답 또는 프로젝트 내부 `error` 응답을 사용할 수 있습니다.
프론트에서는 둘 다 처리할 수 있게 만드는 것을 권장합니다.

```ts
type ApiErrorResponse = {
  detail?: string | Array<{ loc: unknown[]; msg: string; type: string }>;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};
```

### 1.3 공통 유틸 타입

```ts
type Id = string;
type ISODateString = string;
type Nullable<T> = T | null;
```

---

## 2. 상태값 Enum

백엔드 값과 정확히 맞춰야 하는 상태값입니다.

```ts
type UserRole = "admin" | "member";
type SignupRequestStatus = "pending" | "approved" | "rejected";
type DocumentStatus = "draft" | "published";
type ReactionType = "like";
```

문서 목록 정렬 값:

```ts
type DocumentSortKey = "createdAt" | "updatedAt" | "author";
type SortOrder = "asc" | "desc";
```

프론트 비동기 상태값 권장:

```ts
type RequestState = "idle" | "loading" | "success" | "error";
type LoadState = "idle" | "loading" | "empty" | "ready" | "error";
```

---

## 3. 문서 타입

### 3.1 작성자 정보

문서 응답은 작성자 정보를 flat 필드와 nested 필드 둘 다 제공합니다.

```ts
type DocumentOwner = {
  id: Id;
  name: string;
  avatarUrl: Nullable<string>;
};
```

### 3.2 문서 목록 카드 타입

목록 API는 카드 렌더링에 필요한 최소 필드만 내려줍니다.
`content` 전체 배열은 포함되지 않습니다.

```ts
type DocumentListItem = {
  id: Id;
  title: string;
  summary: Nullable<string>;
  contentText: string;
  categoryId: Nullable<Id>;
  ownerId: Id;
  ownerName: string;
  ownerAvatarUrl: Nullable<string>;
  createdAt: ISODateString;
  updatedAt: ISODateString;
  status: DocumentStatus;
};
```

### 3.3 문서 상세 타입

상세 API는 `content` 전체를 포함합니다.

```ts
type DocumentDetail = {
  id: Id;
  title: string;
  content: Array<Record<string, unknown>>;
  contentText: string;
  summary: Nullable<string>;
  categoryId: Nullable<Id>;
  ownerId: Id;
  ownerName: string;
  ownerAvatarUrl: Nullable<string>;
  owner: DocumentOwner;
  createdAt: ISODateString;
  updatedAt: ISODateString;
  status: DocumentStatus;
};
```

### 3.4 문서 생성/수정 타입

```ts
type DocumentCreateRequest = {
  title: string;
  content: Array<Record<string, unknown>>;
  categoryId?: Nullable<Id>;
  status?: DocumentStatus;
};

type DocumentUpdateRequest = {
  title?: string | null;
  content?: Array<Record<string, unknown>> | null;
  categoryId?: Nullable<Id>;
  summary?: string | null;
  status?: DocumentStatus | null;
};
```

---

## 4. 문서 목록 페이징 타입

### 4.1 Query state

프론트가 서버에 그대로 넘길 상태값입니다.

```ts
type DocumentListQueryState = {
  page: number;
  pageSize: number;
  q?: string;
  sort: DocumentSortKey;
  order: SortOrder;
  categoryId?: Nullable<Id>;
};
```

권장 기본값:

```ts
const defaultDocumentListQueryState: DocumentListQueryState = {
  page: 1,
  pageSize: 20,
  q: "",
  sort: "createdAt",
  order: "desc",
  categoryId: null,
};
```

### 4.2 Pagination meta

```ts
type PaginationMeta = {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
};
```

### 4.3 List response

```ts
type DocumentListResponse = ListResponse<DocumentListItem, PaginationMeta>;
```

---

## 5. 문서 목록 API 연동

### GET `/api/v1/documents`

Query:

```ts
type DocumentListQueryParams = {
  page?: number;
  pageSize?: number;
  q?: string;
  sort?: DocumentSortKey;
  order?: SortOrder;
  categoryId?: Nullable<Id>;
};
```

예시:

```ts
GET /api/v1/documents?page=1&pageSize=20&sort=createdAt&order=desc
GET /api/v1/documents?page=1&pageSize=20&q=회의록&sort=createdAt&order=desc
GET /api/v1/documents?page=1&pageSize=20&categoryId=cat-1&sort=updatedAt&order=asc
GET /api/v1/documents?page=1&pageSize=20&sort=author&order=desc
```

### 프론트 렌더링 포인트

- 카드 목록은 `DocumentListItem[]`만 사용합니다.
- 카드 클릭 시 `GET /api/v1/documents/{documentId}`로 상세를 가져옵니다.
- 검색어 변경, 폴더 변경, 정렬 변경 시 `page = 1`로 초기화하는 것을 권장합니다.
- `hasNext`, `hasPrev`로 페이지 버튼 활성화를 제어할 수 있습니다.

---

## 6. 문서 상세 API

### GET `/api/v1/documents/{documentId}`

Response:

```ts
type DocumentDetailResponse = ApiResponse<DocumentDetail>;
```

### 프론트 사용 포인트

- 편집기 초기값은 상세 응답의 `content`를 사용합니다.
- 목록 카드에는 상세 응답 전체를 유지할 필요가 없습니다.
- `summary`가 비어 있으면 카드에서는 `contentText` 일부를 preview로 사용할 수 있습니다.

---

## 7. 문서 생성/수정 API

### POST `/api/v1/documents`

```ts
type DocumentCreateResponse = ApiResponse<DocumentDetail>;
```

### PATCH `/api/v1/documents/{documentId}`

```ts
type DocumentUpdateResponse = ApiResponse<DocumentDetail>;
```

권장 동작:

- 저장 성공 후 서버 응답으로 목록/상세 상태를 갱신합니다.
- `content`가 바뀌면 서버가 `contentText`를 다시 계산합니다.

---

## 8. 아바타 업로드 API

### POST `/api/v1/users/me/avatar`

`multipart/form-data`

Field:

```ts
type AvatarUploadForm = {
  file: File;
};
```

Response:

```ts
type AvatarUploadResponse = ApiResponse<{
  avatarUrl: string;
}>;
```

프론트 주의사항:

- `avatarUrl`를 `PATCH /api/v1/users/me`로 보내지 않습니다.
- 아바타 업로드 성공 후 받은 `avatarUrl`을 유저 상태에 반영합니다.
- 서버가 반환한 경로는 상대 경로일 수 있으므로, 이미지 렌더링 시 API base URL 결합이 필요할 수 있습니다.

---

## 9. 인증/사용자 타입

### 9.1 로그인 응답

```ts
type AuthUser = {
  id: Id;
  name: string;
  email: string;
  role: UserRole;
  organization: Nullable<string>;
  avatarUrl: Nullable<string>;
  createdAt: ISODateString;
};

type LoginResponse = ApiResponse<{
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
}>;
```

### 9.2 내 정보

```ts
type MeResponse = ApiResponse<AuthUser>;
```

### 9.3 프로필 수정

```ts
type UserProfileUpdateRequest = {
  name?: string | null;
  organization?: string | null;
};
```

주의:

- 아바타는 위 요청에 포함하지 않습니다.
- 아바타는 별도 업로드 API만 사용합니다.

---

## 10. 댓글/반응 타입

### Reaction

```ts
type ReactionSummary = {
  likeCount: number;
  likedByMe: boolean;
};
```

### Comment

```ts
type CommentItem = {
  id: Id;
  documentId: Id;
  authorId: Id;
  authorName: string;
  authorAvatarUrl?: string | null;
  authorOrganization?: string | null;
  content: string;
  createdAt: ISODateString;
  updatedAt: ISODateString;
};
```

### Request

```ts
type CommentCreateRequest = {
  content: string;
};

type ReactionCreateRequest = {
  type: ReactionType;
};
```

---

## 11. 권장 프론트 상태 설계

문서 자료실 페이지는 아래 상태를 분리해서 관리하는 것을 권장합니다.

```ts
type DocumentListState = {
  query: DocumentListQueryState;
  items: DocumentListItem[];
  meta: PaginationMeta;
  loadingState: LoadState;
  errorMessage: string | null;
};
```

추천 UI 동작:

1. 초기 진입 시 `page = 1`, `sort = createdAt`, `order = desc`
2. 검색어 입력 시 debounce 후 `q` 갱신
3. `sort`, `order`, `categoryId` 변경 시 `page = 1`
4. API 요청 중에는 `loadingState = loading`
5. 결과 0건이면 `loadingState = empty`
6. 에러 시 `loadingState = error`

---

## 12. 정렬 옵션 UI 매핑

프론트 드롭다운은 아래 값으로 서버 파라미터에 매핑하면 됩니다.

```ts
type DocumentSortOption =
  | { label: "생성일 내림차순", sort: "createdAt", order: "desc" }
  | { label: "생성일 오름차순", sort: "createdAt", order: "asc" }
  | { label: "수정일 내림차순", sort: "updatedAt", order: "desc" }
  | { label: "수정일 오름차순", sort: "updatedAt", order: "asc" }
  | { label: "작성자별", sort: "author", order: "desc" };
```

작성자별 정렬은 서버가 안정 정렬까지 처리합니다.

---

## 13. 구현 체크리스트

1. `DocumentListItem`와 `DocumentDetail` 타입을 분리합니다.
2. 목록 페이지는 `DocumentListResponse`만 사용합니다.
3. 상세 페이지/에디터는 `DocumentDetail`을 사용합니다.
4. 프로필 이미지는 `POST /users/me/avatar`로 업로드합니다.
5. `page`, `pageSize`, `q`, `sort`, `order`, `categoryId`는 URL query 또는 상태 store에 유지합니다.
6. API 실패 시 `ApiErrorResponse`를 공통 처리합니다.
