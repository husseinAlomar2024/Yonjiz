-- ============================================================
-- Migrate an older Daymark/PostgreSQL database to this schema.
-- Target: PostgreSQL 14+. Review against your actual schema first;
-- this has not been run against your live database.
--
-- This script refuses to continue if more than three existing
-- accounts have role = 'admin'. Demote the extras manually first:
--
--   SELECT id, username, email FROM users WHERE role = 'admin' ORDER BY id;
--   UPDATE users SET role = 'user' WHERE id IN (...);
--
-- Always take a backup first:
--   pg_dump -Fc your_database > daymark-before-migration.dump
-- ============================================================

BEGIN;

-- 1. Users: add columns that the new application needs.
ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_slot SMALLINT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE
    DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC');
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITHOUT TIME ZONE;

-- 2. Normalize old values before adding strict constraints.
UPDATE users SET role = 'user' WHERE role IS NULL OR role NOT IN ('user', 'admin');
UPDATE users SET is_active = TRUE WHERE is_active IS NULL;
UPDATE users SET created_at = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') WHERE created_at IS NULL;

-- 3. Enforce the seat rule. This block refuses to guess who should lose admin.
DO $$
DECLARE
    admin_total INTEGER;
BEGIN
    SELECT COUNT(*) INTO admin_total FROM users WHERE role = 'admin';
    IF admin_total > 3 THEN
        RAISE EXCEPTION
            'Found % administrators. Demote all but three before running this migration.',
            admin_total;
    END IF;
END $$;

ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE users ALTER COLUMN is_active SET NOT NULL;
ALTER TABLE users ALTER COLUMN role SET NOT NULL;

-- Give the remaining admins seats 1..N (never more than 3 because of the block above).
UPDATE users SET admin_slot = NULL;
WITH ranked AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS seat
    FROM users
    WHERE role = 'admin'
)
UPDATE users AS u
SET admin_slot = ranked.seat
FROM ranked
WHERE u.id = ranked.id;

ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role;
ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_admin_slot;
ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_users_admin_slot;
ALTER TABLE users ADD CONSTRAINT ck_users_role
    CHECK (role IN ('user', 'admin'));
ALTER TABLE users ADD CONSTRAINT ck_users_admin_slot
    CHECK (
        (role = 'admin' AND admin_slot IS NOT NULL AND admin_slot BETWEEN 1 AND 3)
        OR
        (role = 'user' AND admin_slot IS NULL)
    );
ALTER TABLE users ADD CONSTRAINT uq_users_admin_slot UNIQUE (admin_slot);

-- Drop old unique constraints only if they differ; the new schema still keeps
-- email and username unique. These statements are safe to skip if your existing
-- constraints already have these names.
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_idx ON users (email);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_idx ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_role_admin_slot ON users (role, admin_slot);

-- 4. Todos: add the optional deadline, timestamps and completion time.
ALTER TABLE todos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE todos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE todos ADD COLUMN IF NOT EXISTS deadline TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE todos ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;

UPDATE todos SET title = 'Untitled task' WHERE title IS NULL OR btrim(title) = '';
UPDATE todos SET description = '' WHERE description IS NULL;
UPDATE todos SET priority = 3 WHERE priority IS NULL OR priority < 1 OR priority > 5;
UPDATE todos SET complete = FALSE WHERE complete IS NULL;
UPDATE todos SET created_at = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') WHERE created_at IS NULL;
UPDATE todos SET updated_at = created_at WHERE updated_at IS NULL;
UPDATE todos SET completed_at = updated_at WHERE complete = TRUE AND completed_at IS NULL;

-- Refuse to silently delete tasks whose owner no longer exists.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM todos t
        LEFT JOIN users u ON u.id = t.owner_id
        WHERE t.owner_id IS NULL OR u.id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Some tasks have a missing or invalid owner_id. Repair them before migrating.';
    END IF;
END $$;

ALTER TABLE todos ALTER COLUMN title SET NOT NULL;
ALTER TABLE todos ALTER COLUMN description SET NOT NULL;
ALTER TABLE todos ALTER COLUMN priority SET NOT NULL;
ALTER TABLE todos ALTER COLUMN complete SET NOT NULL;
ALTER TABLE todos ALTER COLUMN owner_id SET NOT NULL;
ALTER TABLE todos ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE todos ALTER COLUMN updated_at SET NOT NULL;

ALTER TABLE todos DROP CONSTRAINT IF EXISTS ck_todos_priority;
ALTER TABLE todos ADD CONSTRAINT ck_todos_priority CHECK (priority BETWEEN 1 AND 5);

-- Replace the old owner foreign key with one that cascades on account deletion.
DO $$
DECLARE
    fk_name TEXT;
    owner_attnum SMALLINT;
BEGIN
    SELECT attnum INTO owner_attnum
    FROM pg_attribute
    WHERE attrelid = 'todos'::regclass AND attname = 'owner_id';

    FOR fk_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'todos'::regclass
          AND contype = 'f'
          AND owner_attnum = ANY (conkey)
    LOOP
        EXECUTE format('ALTER TABLE todos DROP CONSTRAINT %I', fk_name);
    END LOOP;
END $$;

ALTER TABLE todos ADD CONSTRAINT fk_todos_owner
    FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS ix_todos_owner_id ON todos (owner_id);
CREATE INDEX IF NOT EXISTS ix_todos_owner_complete ON todos (owner_id, complete);
CREATE INDEX IF NOT EXISTS ix_todos_owner_deadline ON todos (owner_id, deadline);

-- 5. Audit trail used by the admin console.
CREATE TABLE IF NOT EXISTS admin_audit (
    id           INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    actor_id     INTEGER,
    action       VARCHAR(60) NOT NULL,
    target_label VARCHAR(180),
    created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL
                 DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT fk_admin_audit_actor
        FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_admin_audit_created_at ON admin_audit (created_at);

COMMIT;

-- Verification:
--   SELECT id, username, role, admin_slot FROM users ORDER BY admin_slot NULLS LAST;
--   SELECT COUNT(*) AS admin_count FROM users WHERE role = 'admin';  -- must be <= 3
--   SELECT id, title, deadline FROM todos ORDER BY id;
