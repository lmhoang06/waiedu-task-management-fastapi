-- Enum types for the task management system
-- These enums define the possible states and priorities for various entities

-- User status enum defines possible states for user accounts
CREATE TYPE "user_status_enum" AS ENUM (
    'banned',           -- User is banned from the system
    'active',           -- User is active and can use the system
    'inactive',         -- User account is inactive
    'pending_approval', -- User registration is pending approval
    'rejected'          -- User registration was rejected
);

-- Project status enum defines possible states for projects
CREATE TYPE "project_status_enum" AS ENUM (
    'cancelled',        -- Project has been cancelled
    'completed',        -- Project has been completed
    'rejected',         -- Project proposal was rejected
    'on_hold',          -- Project is temporarily on hold
    'pending_approval'  -- Project is waiting for approval
    'in_progress'      -- Project is in progress
);

-- Priority enum defines task and project priority levels
CREATE TYPE "priority_enum" AS ENUM (
    'very_low',         -- Very low priority
    'low',              -- Low priority
    'medium',           -- Medium priority
    'high',             -- High priority
    'critical'          -- Critical priority
);

-- Task status enum defines possible states for tasks
CREATE TYPE "task_status_enum" AS ENUM (
    'completed',        -- Task has been completed
    'cancelled',        -- Task has been cancelled
    'todo',             -- Task is in todo state
    'in_progress'       -- Task is currently being worked on
);

-- Forgot password request status enum defines possible states for password reset requests
CREATE TYPE "forgot_password_request_enum" AS ENUM (
    'pending_approval', -- Request is pending admin approval
    'approved',         -- Request has been approved
    'denied'            -- Request has been denied
); 