# Frontend Avatar Upload Request

## Goal

아바타 이미지는 프론트에서 base64 문자열로 보내지 말고, 파일 업로드로 서버에 전송합니다.
서버는 이미지를 스토리지에 저장하고, DB에는 이미지 경로만 저장합니다.

## Current Contract

### Upload avatar

`POST /api/v1/users/me/avatar`

Request:

`multipart/form-data`

Field:

`file`: image file

Response:

```json
{
  "data": {
    "avatarUrl": "/uploads/avatars/user-id/generated-file-name.png"
  }
}
```

### Update profile text fields

`PATCH /api/v1/users/me`

Request body:

```json
{
  "name": "홍길동",
  "organization": "GAP"
}
```

주의:

- `avatarUrl`는 더 이상 `PATCH /users/me`로 보내지 않습니다.
- 아바타 변경은 반드시 `POST /users/me/avatar`로만 처리합니다.

## Frontend Changes

1. 프로필 편집 화면에서 이미지 선택 입력을 `input[type="file"]` 또는 동일한 파일 선택 컴포넌트로 변경합니다.
2. 선택된 이미지는 `FormData`에 담아서 `POST /api/v1/users/me/avatar`로 전송합니다.
3. 응답의 `avatarUrl`을 사용자 상태에 반영합니다.
4. 이미지 렌더링 시에는 서버가 반환한 경로를 그대로 쓰되, 필요하면 API base URL을 앞에 붙입니다.
5. 프로필 이름/조직 수정은 기존처럼 `PATCH /api/v1/users/me`를 사용합니다.

## Validation Recommendations

- 이미지 파일만 허용합니다.
- 업로드 전 프론트에서 미리보기와 용량 제한을 넣는 것을 권장합니다.
- 가능하면 2MB 또는 서비스 정책에 맞는 상한을 두는 게 좋습니다.

## Storage Notes

현재 백엔드는 로컬 파일 시스템 기준으로 구현되어 있지만, `FILE_STORAGE_ROOT`만 NAS나 공유 스토리지의 마운트 경로로 바꾸면 같은 코드로 운영할 수 있습니다.

예:

- 로컬: `storage/uploads`
- NAS: `/mnt/nas/uploads`
- 공유 스토리지 마운트: `/data/shared/uploads`

즉, 프론트는 저장소 종류를 알 필요가 없고, 응답으로 받은 `avatarUrl`만 사용하면 됩니다.
