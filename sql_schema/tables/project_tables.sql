-- Project and task management tables

-- Projects table stores project information
CREATE TABLE "projects" (
    "id" SERIAL NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT,
    "status" PROJECT_STATUS_ENUM NOT NULL DEFAULT 'pending_approval',
    "start_date" TIMESTAMPTZ NOT NULL,
    "end_date" TIMESTAMPTZ NOT NULL,
    "manager_id" INTEGER,
    "budget" BIGINT NOT NULL DEFAULT 0,
    "priority" PRIORITY_ENUM NOT NULL DEFAULT 'medium',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    CONSTRAINT "valid_project_dates" CHECK ("end_date" > "start_date"),
    CONSTRAINT "non_negative_budget" CHECK ("budget" >= 0)
);

-- Tasks table for project tasks
CREATE TABLE "tasks" (
    "id" SERIAL NOT NULL UNIQUE,
    "project_id" INTEGER NOT NULL,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT,
    "status" TASK_STATUS_ENUM NOT NULL DEFAULT 'todo',
    "priority" PRIORITY_ENUM NOT NULL DEFAULT 'medium',
    "due_date" TIMESTAMPTZ NOT NULL,
    "created_by" INTEGER NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    CONSTRAINT "valid_task_due_date" CHECK ("due_date" > "created_at")
);

-- Project members mapping table
CREATE TABLE "project_members" (
    "id" SERIAL NOT NULL UNIQUE,
    "project_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "role" VARCHAR(255) NOT NULL,
    "joined_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    UNIQUE("project_id", "user_id")
);

-- Comments table for task discussions
CREATE TABLE "comments" (
    "id" SERIAL NOT NULL UNIQUE,
    "task_id" INTEGER NOT NULL,
    "user_id" INTEGER,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    CONSTRAINT "valid_comment_content" CHECK ("content" != '')
);

-- Task assignments mapping table
CREATE TABLE "task_assignments" (
    "id" SERIAL NOT NULL UNIQUE,
    "task_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "assigned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    UNIQUE("task_id", "user_id")
); 