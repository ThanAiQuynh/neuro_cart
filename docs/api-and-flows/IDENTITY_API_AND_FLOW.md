# Identity API & Flow — Ecommerce + Agentic RAG MCP

Tài liệu này tổng hợp **API Identity** và **luồng hoạt động** cho hệ thống ecommerce bán đồ điện tử, tích hợp Agentic RAG/MCP. Nội dung bám sát monorepo đã thống nhất (FastAPI, SQLAlchemy, Alembic) và các bổ sung DB (sessions, refresh tokens, reset/verify, MFA…).

---

## 1) Mục tiêu

- Cung cấp bộ **Auth** đầy đủ (register/login/refresh/logout).
- Quản lý **tài khoản & địa chỉ** cho người dùng (FE).
- Cung cấp endpoints **admin** để quản trị user/roles.
- Hỗ trợ **khôi phục mật khẩu**, **xác thực email**, **MFA TOTP**, **OAuth/SSO** (tùy chọn).
- Sẵn sàng cho **API keys (MCP)** và audit/rate-limit.

---

## 2) Tóm tắt DB cần có

> Sử dụng `core` cho dữ liệu chính, `ops` cho vận hành/phiên.

### 2.1. Bổ sung cột `core.users`
- `email_verified_at TIMESTAMPTZ NULL`
- `password_changed_at TIMESTAMPTZ NULL`
- `failed_login_count INT NOT NULL DEFAULT 0`
- `lock_until TIMESTAMPTZ NULL`
- `last_login_at TIMESTAMPTZ NULL`
- `mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE`

### 2.2. Bảng phiên & refresh (schema `ops`)
- `ops.auth_sessions (id, user_id, created_at, last_seen_at, ip, user_agent, revoked_at)`  
  Index: `(user_id, last_seen_at desc)`, partial `revoked_at IS NULL`.
- `ops.refresh_tokens (id, session_id, user_id, family_id, jti, token_hash, issued_at, expires_at, revoked_at, replaced_by, ip, user_agent)`  
  Unique: `jti`; Partial unique `(family_id) WHERE revoked_at IS NULL`.

### 2.3. Rate-limit & audit (schema `ops`)
- `ops.login_attempts (id, email_canon CITEXT, ip INET, attempted_at)`.
- `ops.audit_events (id, user_id, event, meta JSONB, created_at)` (tuỳ chọn).

### 2.4. Reset/Verify/MFA/SSO/API keys (schema `core`)
- `core.password_resets (id, user_id, token_hash, expires_at, used_at, created_at)`.
- `core.email_verifications (id, user_id, token_hash, expires_at, used_at, created_at)`.
- `core.mfa_totp (user_id PK, secret_encrypted, recovery_codes_hash[], created_at, disabled_at)`.
- `core.oauth_accounts (id, user_id, provider, provider_user_id, access_token_encrypted, refresh_token_encrypted, expires_at)`.
- `core.api_keys (id, user_id, name, key_prefix, key_hash, scopes JSONB, created_at, last_used_at, expires_at, revoked_at)`.

> Alembic: ưu tiên **partial unique** & **index** như đã nêu (chi tiết xem migration gợi ý).

---

## 3) API Surface (nhóm chính)

### 3.1. Auth (public)
| Method | Path | Auth | Mô tả |
|---|---|---|---|
| POST | `/auth/register` | - | Tạo user + customer, role `customer` |
| POST | `/auth/login` | - | Phát hành **access** + **refresh** (cookie) |
| POST | `/auth/refresh` | Refresh cookie | **Rotate** refresh token, phát hành access mới |
| POST | `/auth/logout` | Refresh cookie | Thu hồi phiên hiện tại, xoá cookies |
| POST | `/auth/logout-all` | Bearer | Thu hồi tất cả phiên của user |

### 3.2. Account (yêu cầu đăng nhập)
| Method | Path | Mô tả |
|---|---|---|
| GET | `/auth/me` | Lấy thông tin user hiện tại (roles) |
| PATCH | `/users/{user_id}/profile` | Cập nhật profile (self/admin) |
| POST | `/users/{user_id}/change-password` | Đổi mật khẩu; revoke tất cả refresh-tokens |

### 3.3. Addresses (self)
| Method | Path | Mô tả |
|---|---|---|
| GET | `/me/addresses` | Danh sách địa chỉ |
| POST | `/me/addresses` | Thêm địa chỉ (có thể set default) |
| PATCH | `/me/addresses/{id}` | Sửa địa chỉ |
| DELETE | `/me/addresses/{id}` | Xoá địa chỉ |
| POST | `/me/addresses/{id}/make-default` | Đặt mặc định |

### 3.4. Email verify & password reset
| Method | Path | Mô tả |
|---|---|---|
| POST | `/auth/request-email-verify` | Gửi email xác thực |
| POST | `/auth/verify-email` | Xác thực token email |
| POST | `/auth/request-password-reset` | Gửi email reset |
| POST | `/auth/reset-password` | Đặt mật khẩu mới bằng token |

### 3.5. MFA (TOTP)
| Method | Path | Mô tả |
|---|---|---|
| POST | `/auth/mfa/setup` | Tạo secret + QR |
| POST | `/auth/mfa/verify` | Xác nhận bật MFA |
| POST | `/auth/mfa/disable` | Tắt MFA |
| POST | `/auth/mfa/login` | Bước 2 khi đăng nhập |

### 3.6. Admin users
| Method | Path | Mô tả |
|---|---|---|
| GET | `/admin/users?query=&page=&size=` | Liệt kê/paginate |
| GET | `/admin/users/{id}` | Chi tiết |
| POST | `/admin/users/{id}/roles` | Thêm role |
| DELETE | `/admin/users/{id}/roles/{code}` | Gỡ role |
| POST | `/admin/users/{id}/deactivate` | Vô hiệu hoá |
| POST | `/admin/users/{id}/reactivate` | Kích hoạt lại |

### 3.7. API Keys (MCP/Agent)
| Method | Path | Mô tả |
|---|---|---|
| GET | `/me/api-keys` | List keys |
| POST | `/me/api-keys` | Tạo key (trả secret **1 lần**) |
| DELETE | `/me/api-keys/{id}` | Revoke key |

---

## 4) JWT & Cookie Design

- **Access JWT** (ngắn hạn, 15–60 phút): claims `sub` (user_id), `sid` (session_id), `jti`, `iss/aud`, `iat/nbf/exp`, (tuỳ chọn) `roles`.
- **Refresh token** (dài hạn, 7–30 ngày): lưu **hash** ở `ops.refresh_tokens` với `jti` + `family_id`.
- **Cookies**:
  - `access_token`: `HttpOnly`, `Secure`, `SameSite=Lax|Strict`, `Path=/`, TTL ~ access TTL.
  - `refresh_token`: `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/auth`, TTL ~ refresh TTL.
- **Rotation**: `/auth/refresh` tạo RT mới, **revoke** RT cũ (`revoked_at`, `replaced_by`). Nếu phát hiện **token reuse** → revoke **toàn bộ family**.

---

## 5) Flows (chi tiết)

### 5.1. Register
1) Check trùng email → 409/400 nếu tồn tại.  
2) Hash mật khẩu (async).  
3) Tạo `user` (is_active=True) + gán role `customer`.  
4) Tạo `customer`.  
5) (Tuỳ chọn) phát hành email verification token & gửi mail.  ***later***
6) Trả `UserDTO`.

### 5.2. Login (password)
1) Ghi `ops.login_attempts(email, ip)`, kiểm tra rate-limit/lockout.  
2) Tìm user, verify mật khẩu (async).  
3) Nếu `mfa_enabled` → trả `requires_mfa`.  ***later***  
4) Tạo `ops.auth_sessions` (ip, ua).  
5) Issue **refresh** (jti, family_id) + lưu **hash** → `ops.refresh_tokens`.  
6) Issue **access JWT**.  
7) Update `users.last_login_at`.  
8) Set cookie `access_token` & `refresh_token`.

### 5.3. Refresh
1) Đọc cookie `refresh_token`, tìm `jti`.  
2) Nếu token **revoked/expired** → 401 (và có thể revoke family).  
3) **Rotate**: tạo token mới, revoke token cũ.  
4) Issue access mới, cập nhật `auth_sessions.last_seen_at`.  
5) Set cookies mới.

### 5.4. Logout / Logout-all
- **Logout**: revoke refresh hiện tại (+/− revoke session), xoá cookies.  
- **Logout-all**: revoke theo `user_id` (tất cả sessions/tokens).

### 5.5. Password reset
- **Request**: tạo `core.password_resets` (hash token), gửi mail.  
- **Reset**: xác thực token, update `users.password_hash`, set `password_changed_at`, **revoke all refresh tokens**.

### 5.6. Email verify
- **Request**: tạo `core.email_verifications` (hash token), gửi mail.  
- **Verify**: set `users.email_verified_at`, đánh dấu token `used_at`.

### 5.7. Addresses
- CRUD như bảng 3.3; **make-default** dùng `AddressRepo.set_default` (atomic).

### 5.8. Admin
- List/filter/paginate users, chỉnh role, deactivate/reactivate; ghi `ops.audit_events`.

---

## 6) Bảo mật & vận hành

- **Rate-limit** `/auth/login`: theo `email` + `ip` (cửa sổ 5–15 phút).  
- **Lockout**: quá N lần thất bại → `users.lock_until = now() + X`.  
- **Token reuse detection** với refresh rotation.  
- **Audit** tất cả sự kiện quan trọng (login, logout, role, reset…).  
- **CSRF**: nếu access dùng cookie → áp dụng **double-submit token** cho POST/PATCH/DELETE.  
- **Observability**: log `sid`, `jti`, `user_id`, `ip`, `ua`.

---

## 7) Mapping Kiến trúc (Clean Architecture)

- **Application / Use-cases**:  
  `RegisterUser`, `LoginUser`, `RefreshSession`, `Logout`, `LogoutAll`,  
  `UpdateProfile`, `ChangePassword`,  
  `AddAddress`, `UpdateAddress`, `DeleteAddress`, `MakeDefaultAddress`,  
  `RequestPasswordReset`, `ResetPassword`,  
  `RequestEmailVerify`, `VerifyEmail`,  
  `MfaSetup`, `MfaVerify`, `MfaDisable`,  
  `ListUsers`, `GetUser`, `AddUserRole`, `RemoveUserRole`, `DeactivateUser`, `ReactivateUser`.

- **Ports**:  
  Identity repos (User/Role/Customer/Address + *Sessions/Refresh/Audit/Resets/Verifications/MFA/OAuth/APIKey*),  
  Security async (`IAsyncPasswordHasher`, `IAsyncTokenService`).

- **Infra**:  
  Repo implementations (SQLAlchemy), Async security adapters (bcrypt/argon2, JWT).

- **API (FastAPI)**:  
  Routers: `identity.py`, `identity_tokens.py`, `identity_recovery.py`, `identity_mfa.py`, `admin_users.py`.

---

## 8) Response mẫu

```jsonc
// POST /auth/login
{
  "user": {
    "id": "uuid",
    "email": "a@b.com",
    "full_name": "A B",
    "phone": null,
    "is_active": true,
    "roles": ["customer"]
  },
  "token": {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
}
```

---

## 9) Ưu tiên triển khai tiếp theo

1) Thêm routers: `/auth/refresh`, `/auth/logout(-all)` và hoàn thiện Address `PATCH/DELETE/make-default`.  
2) Repos + use-cases cho **Sessions/Refresh/Reset/Verify**.  
3) Rate-limit & Audit.  
4) Admin user routes cơ bản.  
5) (Tuỳ chọn) MFA & OAuth.

> Khi cần, có thể tách docs này thành **OpenAPI** mô tả chi tiết từng schema input/output để auto-gen `packages/ts-sdk/` cho FE.