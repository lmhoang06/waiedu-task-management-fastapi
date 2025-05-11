-- Core tables for user management and team organization

-- Users table stores all user information
CREATE TABLE "users" (
    "id" SERIAL NOT NULL UNIQUE,
    "username" VARCHAR(63) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) CHECK (email IS NULL OR email ~ '(?:[a-z0-9!#$%&''*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&''*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'),
    "full_name" VARCHAR(255),
    "role_id" INTEGER,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" USER_STATUS_ENUM NOT NULL DEFAULT 'pending_approval',
    "last_login" TIMESTAMPTZ,
    "avatar" VARCHAR(255),
    PRIMARY KEY("id")
);

-- Roles table defines user roles and their permissions
CREATE TABLE "roles" (
    "id" SERIAL NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "permissions" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id")
);

-- User tokens for authentication
CREATE TABLE "user_tokens" (
    "id" SERIAL NOT NULL UNIQUE,
    "user_id" INTEGER NOT NULL,
    "token" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP + INTERVAL '24 hours',
    PRIMARY KEY("id"),
    CONSTRAINT "expires_after_creation" CHECK ("expires_at" > "created_at")
);

-- Teams table for organizing users into groups
CREATE TABLE "teams" (
    "id" SERIAL NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT,
    "leader_id" INTEGER,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id")
);

-- Team members mapping table
CREATE TABLE "team_members" (
    "id" SERIAL NOT NULL UNIQUE,
    "team_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "role" VARCHAR(255) NOT NULL,
    "joined_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    UNIQUE("team_id", "user_id")
); 