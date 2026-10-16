# ADR 0001: Use JWT bearer tokens instead of server-side sessions

**Status:** Accepted
**Date:** 2026-10-16

## Context

The Loan Application Service needs to authenticate customers and loan officers and
enforce role-based access (CUSTOMER vs OFFICER) on every endpoint. It is a stateless
JSON API consumed by Swagger, Postman and, later, a frontend or other services. It runs
in Docker and should be able to scale to several API containers behind a load balancer.

Two options were considered:

1. **Server-side sessions**: the server stores session data (in Postgres or Redis) and
   the client sends an opaque session ID in a cookie.
2. **JWT bearer tokens**: the server signs a token containing the user ID and role, and
   the client sends it in the `Authorization: Bearer` header.

## Decision

Use **short-lived JWT access tokens** (HS256, 30-minute expiry) issued by
`POST /auth/login` through FastAPI's OAuth2 password flow. The token carries `sub`
(user ID), `role`, `iat` and `exp`. On each request the API verifies the signature and
expiry, then loads the user from the database to confirm they still exist and are active.

## Consequences

**Positive**
- Stateless: no session store to run, and any API container can verify any token.
- Works naturally with non-browser clients (Swagger, Postman, other services).
- Fits FastAPI's built-in `OAuth2PasswordBearer` support and the OpenAPI docs.
- No cookies, so no CSRF protection is needed.

**Negative**
- A token can't be revoked before it expires. This is limited by the 30-minute expiry and
  by re-checking `is_active` in the database on every request.
- The signing secret (`JWT_SECRET_KEY`) is critical: if it leaks, anyone can forge tokens.
  It's supplied only through the environment, never committed.
- A role change only takes effect for the token's `role` claim after the user logs in
  again. Authorization reads the role from the database user, so this is mitigated.
- No refresh tokens yet: users must log in again every 30 minutes.

**Revisit if** we need instant logout or revocation, a browser-only client where
HTTP-only session cookies are simpler, or long-lived sessions (add refresh tokens).
