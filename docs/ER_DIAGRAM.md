# YONJIZ · ينجز — database design

![YONJIZ ER diagram](er_diagram.png)

The editable source is [er_diagram.svg](er_diagram.svg). The runnable schemas are [schema.sql](schema.sql) (SQLite) and [postgres_schema.sql](postgres_schema.sql) (PostgreSQL).

## The three entities

| Entity | Purpose | Key rules |
| --- | --- | --- |
| `users` | Accounts, authentication, roles and admin seats | `email` and `username` are unique. `role` is `user` or `admin`. An admin must hold one unique seat (`admin_slot` 1–3). Exactly one admin can be the protected main admin in seat 1. |
| `todos` | A user's tasks | `owner_id` references `users.id` and cascades on delete. `deadline` is nullable. `priority` is 1–5. |
| `admin_audit` | A lightweight trail of sensitive admin actions | `actor_id` is nullable and becomes `NULL` if the actor is deleted; the human-readable label remains. Appends only in the UI. |

## Relationship cardinality

- One **user** owns zero or many **todos** (`1 : N`).
- One **user** performs zero or many **admin_audit** entries (`1 : N`).
- A todo belongs to exactly one user.
- An audit entry belongs to at most one actor. Deleting the actor preserves the audit row with `actor_id = NULL`.
- There is no separate calendar table. The calendar is a view over `todos.deadline`.
- The clock is not stored at all; it reads the browser's clock.

```mermaid
erDiagram
    USERS ||--o{ TODOS : owns
    USERS ||--o{ ADMIN_AUDIT : performs

    USERS {
        integer id PK
        string email UK
        string username UK
        string first_name
        string last_name
        string hashed_password
        boolean is_active
        string role "user or admin"
        integer admin_slot UK "NULL for users; 1-3 for admins"
        boolean is_primary_admin "one protected main admin in seat 1"
        string phone_number "nullable"
        datetime created_at
        datetime last_login_at "nullable"
    }

    TODOS {
        integer id PK
        integer owner_id FK
        string title
        string description
        integer priority "1-5"
        boolean complete
        datetime created_at
        datetime updated_at
        datetime deadline "NULLABLE - optional deadline"
        datetime completed_at "nullable"
    }

    ADMIN_AUDIT {
        integer id PK
        integer actor_id FK "nullable"
        string action
        string target_label "nullable"
        datetime created_at
    }
```

## How the maximum of three admins is guaranteed

The application checks the number of seats before promoting someone, but the application check is not the real guarantee. The database does the enforcing:

```sql
admin_slot INTEGER,                    -- NULL for regular users
is_primary_admin BOOLEAN NOT NULL DEFAULT 0,
CONSTRAINT uq_users_admin_slot UNIQUE (admin_slot),
CONSTRAINT ck_users_admin_slot CHECK (
    (role = 'admin' AND admin_slot IS NOT NULL AND admin_slot BETWEEN 1 AND 3)
    OR
    (role = 'user' AND admin_slot IS NULL)
),
CONSTRAINT ck_users_primary_admin CHECK (
    NOT is_primary_admin
    OR (role = 'admin' AND admin_slot = 1 AND is_active)
);

CREATE UNIQUE INDEX uq_users_single_primary_admin
    ON users (is_primary_admin)
    WHERE is_primary_admin = 1;
```

Why this works:

1. A regular user must have `admin_slot = NULL`.
2. An admin must have `admin_slot` in `{1, 2, 3}`.
3. `UNIQUE(admin_slot)` allows only three non-null values.
4. PostgreSQL and SQLite both allow multiple `NULL`s in a unique column, which is exactly what regular users need.

This closes the race-condition gap that a plain `SELECT COUNT(*) < 3` check has: two concurrent promotions cannot both take seat 2, because the second `INSERT`/`UPDATE` conflicts. The app catches that database error and shows a friendly message.

The old `role = 'admin'` string alone was not enough. Before this schema, any direct SQL insert could create an unlimited number of admins.

### Seat lifecycle

| Action | Database change |
| --- | --- |
| Promote | `role = 'admin'`, `admin_slot` = first free seat (1, 2 or 3) |
| Demote | `role = 'user'`, `admin_slot = NULL` |
| Delete an admin | Row disappears, seat is freed |
| Deactivate an admin | Not allowed until the admin is demoted, so an unavailable account cannot hold a seat hostage |
| Delete an ordinary user | Cascades their todos; audit labels remain |

Self-protection rules: an admin cannot demote, deactivate or delete their own account, and the last admin cannot be removed.

## The protected main admin

`users.is_primary_admin` marks the one permanent main admin.

- Seat 1 is reserved for that account.
- A partial unique index (`WHERE is_primary_admin = 1`) allows only one such row.
- A `CHECK` requires the main admin to be active, role `admin`, and `admin_slot = 1`.
- No other admin can demote, deactivate or delete this account. The rule is enforced in `admin_service.py`, not only by hiding buttons.
- The main admin can promote a user to admin and demote another admin; those are the “hire” and “kick” actions.
- The main admin cannot remove itself either, which keeps the workspace from ending up without its anchor.

Bootstrap it once with:

```powershell
python manage.py create-main-admin
```

Existing installations can designate one seat-1 admin with the SQL in [migrate_existing_postgres.sql](migrate_existing_postgres.sql).

## Optional deadlines

`todos.deadline` is deliberately nullable:

```python
deadline = Column(DateTime, nullable=True)
```

- `NULL` means the task is **open-ended** — not that data is missing.
- The UI has a switch. When it is off, the datetime input is disabled and the API payload sends `deadline: null`.
- The API schema is `deadline: Optional[datetime] = None`.
- The calendar simply skips tasks with a `NULL` deadline. There is nothing to show on the grid.
- Deadline values are stored as **naive UTC** for portability. The browser converts them to the user's local timezone for display and due-state calculation.
- `completed_at` records when a task was finished; it does not replace `deadline`.

## What to edit to add the calendar, clock and optional deadline

If you are retrofitting the original project (or your own copy) rather than using this repository as-is, these are the exact touch points.

### 1. Database / models

| File | Edit |
| --- | --- |
| `models.py` | Define one `User` model (the original file had `Users` commented out while `auth.py` imported it) and one `Todo` model (the original file defined `Todos` twice). Add `Todo.deadline = Column(DateTime, nullable=True)`, `created_at`, `updated_at`, `completed_at`; add `User.admin_slot`, `User.is_primary_admin`, the check constraints and the unique constraints. |
| `docs/schema.sql` / `docs/postgres_schema.sql` | Create the three tables and their indexes. |
| `docs/migrate_existing_postgres.sql` | Apply the columns and constraints to an existing PostgreSQL database. |
| `database.py` | Point `DATABASE_URL` at the database. The supplied app used a hard-coded PostgreSQL URL; this version reads `DATABASE_URL` and defaults to local SQLite. |

For PostgreSQL, install `psycopg[binary]`, then set:

```env
DATABASE_URL=postgresql+psycopg://postgres:1234@localhost/postgres
```

### 2. Backend API

| File | Edit |
| --- | --- |
| `schemas.py` | `deadline: Optional[datetime] = None`; serialize datetimes as UTC ISO strings ending in `Z`. |
| `routers/todos.py` | On create and update, normalize the deadline to UTC and store `None` when absent. Set `completed_at` when `complete` changes. Keep every query owner-scoped. |

### 3. Calendar

| File | Edit |
| --- | --- |
| `static/js/calendar.js` | Render a month grid, collect deadlines from the `data-deadline` attributes on the task cards, mark days with dots, and emit a date-selection event. |
| `static/js/dashboard.js` | Listen for the selected date, hide tasks whose local deadline day differs, update stats, and dispatch `daymark:todos-changed` after every CRUD action. |
| `templates/dashboard.html` | Add the calendar panel and the month navigation buttons. |
| `static/css/app.css` | Add the calendar grid, dot, today, selected-day and responsive styles. |

No extra database table is needed. If the dataset grows large, replace the "render all tasks + client filter" approach with a month query:

```sql
SELECT id, title, deadline, complete
FROM todos
WHERE owner_id = :user_id
  AND deadline >= :month_start_utc
  AND deadline <  :next_month_start_utc
ORDER BY deadline;
```

### 4. Clock

| File | Edit |
| --- | --- |
| `static/js/clock.js` | Read `new Date()`, update the digital time each second and rotate the analog hands. |
| `templates/dashboard.html` | Add the clock markup (`#clock-time`, `#clock-seconds`, `#clock-period`, hands). |
| `static/css/app.css` | Add the clock face and hand CSS. |

The clock has **zero database impact**. It uses the browser's local timezone and never sends a request.

### 5. Optional deadline UI

| File | Edit |
| --- | --- |
| `templates/dashboard.html` | Add the task dialog with `#has-deadline` switch and `<input type="datetime-local" id="task-deadline">`. |
| `templates/partials/task_card.html` | Add `data-deadline="{{ todo.deadline | utc_iso }}"`, a "No deadline" fallback, and a state badge. |
| `static/js/dashboard.js` | Toggle `deadlineInput.disabled`; send `null` when off; format deadline and due-state in local time. |
| `routers/todos.py` / `schemas.py` | Accept `null` and store `NULL`, not a sentinel date. |

## Useful queries

```sql
-- Admin count and occupied seats
SELECT role, admin_slot, COUNT(*)
FROM users
GROUP BY role, admin_slot
ORDER BY admin_slot NULLS LAST;

-- The first free seat, if any
SELECT MIN(seat) AS free_seat
FROM generate_series(1, 3) AS seat
WHERE seat NOT IN (
    SELECT admin_slot FROM users
    WHERE role = 'admin' AND admin_slot IS NOT NULL
);

-- Today's tasks for one user (UTC bounds; compute these in the app for local time)
SELECT id, title, complete, deadline
FROM todos
WHERE owner_id = :user_id
  AND deadline >= :start_utc
  AND deadline <  :end_utc
ORDER BY complete, deadline;

-- Overdue open tasks
SELECT id, title, deadline
FROM todos
WHERE owner_id = :user_id
  AND complete = FALSE
  AND deadline IS NOT NULL
  AND deadline < :now_utc
ORDER BY deadline;
```

## Migration notes

- **New install:** do nothing. `Base.metadata.create_all()` creates the schema on first run.
- **Existing PostgreSQL database:** back it up, read [migrate_existing_postgres.sql](migrate_existing_postgres.sql), and run it. It refuses to proceed if more than three existing admins are found, so you can decide who keeps a seat.
- **Existing SQLite database:** because SQLite cannot add a `CHECK` or change a constraint in place, the cleanest route is to start a new database and copy accounts/tasks into it. The provided `testdb.db` was empty, so a fresh start is safe there.
- **Old passwords:** this build uses bcrypt hashes compatible with the previous `$2b$...` hashes.
- **Rename from `Todos`/`Users` classes:** table names remain `todos` and `users`, so existing rows are preserved when the model classes are renamed.

## Security notes for the admin model

- Role is read from the **database on every request**, not trusted from the JWT. A demoted admin loses access immediately even if their token has not expired.
- Registration forces `role = 'user'`, regardless of any posted `role` field.
- The developer key upgrades only the signed-in account and is rate-limited.
- Admin actions are recorded in `admin_audit`.
- For production: set `SECRET_KEY`, `ADMIN_ACCESS_KEY`, use PostgreSQL, set `COOKIE_SECURE=true`, and serve over HTTPS.
