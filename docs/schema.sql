-- YONJIZ · ينجز database schema — SQLite
-- This is a full, from-scratch schema for the SQLite database used by default.
-- For PostgreSQL, use docs/postgres_schema.sql.
--
-- How the three-admin limit is guaranteed:
--   1. Every admin must occupy exactly one of the seats 1, 2 or 3.
--   2. admin_slot is UNIQUE, so no two accounts can share a seat.
--   3. A CHECK constraint refuses an "admin" without a valid seat.
-- The result is at most three admins, even for direct SQL inserts.
--
-- The protected main admin:
--   1. is_primary_admin = 1 marks the one main admin.
--   2. A partial unique index permits only one such row.
--   3. A CHECK requires that main admin to be active and in seat 1.

PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE users (
    id              INTEGER      NOT NULL,
    email           VARCHAR(254) NOT NULL,
    username        VARCHAR(30)  NOT NULL,
    first_name      VARCHAR(60)  NOT NULL,
    last_name       VARCHAR(60)  NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    role            VARCHAR(20)  NOT NULL DEFAULT 'user',
    admin_slot      INTEGER,
    is_primary_admin BOOLEAN     NOT NULL DEFAULT 0,
    phone_number    VARCHAR(25),
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at   DATETIME,

    PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT ck_users_role CHECK (role IN ('user', 'admin')),
    CONSTRAINT ck_users_admin_slot CHECK (
        (role = 'admin' AND admin_slot IS NOT NULL AND admin_slot BETWEEN 1 AND 3)
        OR
        (role = 'user' AND admin_slot IS NULL)
    ),
    CONSTRAINT ck_users_primary_admin CHECK (
        NOT is_primary_admin
        OR (role = 'admin' AND admin_slot = 1 AND is_active)
    ),
    CONSTRAINT uq_users_admin_slot UNIQUE (admin_slot)
);

CREATE INDEX ix_users_role_admin_slot ON users (role, admin_slot);
CREATE UNIQUE INDEX uq_users_single_primary_admin
    ON users (is_primary_admin)
    WHERE is_primary_admin = 1;

CREATE TABLE todos (
    id           INTEGER       NOT NULL,
    title        VARCHAR(120)  NOT NULL,
    description  VARCHAR(1000) NOT NULL DEFAULT '',
    priority     INTEGER       NOT NULL DEFAULT 3,
    complete     BOOLEAN       NOT NULL DEFAULT 0,
    owner_id     INTEGER       NOT NULL,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deadline     DATETIME,                 -- NULL = no deadline (optional)
    completed_at DATETIME,

    PRIMARY KEY (id),
    CONSTRAINT ck_todos_priority CHECK (priority BETWEEN 1 AND 5),
    CONSTRAINT fk_todos_owner
        FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_todos_owner_id ON todos (owner_id);
CREATE INDEX ix_todos_owner_complete ON todos (owner_id, complete);
CREATE INDEX ix_todos_owner_deadline ON todos (owner_id, deadline);

CREATE TABLE admin_audit (
    id           INTEGER      NOT NULL,
    actor_id     INTEGER,
    action       VARCHAR(60)  NOT NULL,
    target_label VARCHAR(180),
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    CONSTRAINT fk_admin_audit_actor
        FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_admin_audit_created_at ON admin_audit (created_at);

COMMIT;
