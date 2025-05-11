-- Foreign key constraints for all tables

-- User tokens constraints
ALTER TABLE "user_tokens"
ADD FOREIGN KEY("user_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

-- Teams constraints
ALTER TABLE "teams"
ADD FOREIGN KEY("leader_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE SET NULL;

-- Team members constraints
ALTER TABLE "team_members"
ADD FOREIGN KEY("team_id") REFERENCES "teams"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE "team_members"
ADD FOREIGN KEY("user_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

-- Project and task constraints
ALTER TABLE "tasks"
ADD FOREIGN KEY("project_id") REFERENCES "projects"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE "project_members"
ADD FOREIGN KEY("project_id") REFERENCES "projects"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE "project_members"
ADD FOREIGN KEY("user_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE "projects"
ADD FOREIGN KEY("manager_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE SET NULL;

-- User role constraint
ALTER TABLE "users"
ADD FOREIGN KEY("role_id") REFERENCES "roles"("id")
ON UPDATE CASCADE ON DELETE SET NULL;

-- Task creator constraint
ALTER TABLE "tasks"
ADD FOREIGN KEY("created_by") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE SET NULL;

-- Comment constraints
ALTER TABLE "comments"
ADD FOREIGN KEY("task_id") REFERENCES "tasks"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE "comments"
ADD FOREIGN KEY("user_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE SET NULL;

-- Task assignment constraints
ALTER TABLE "task_assignments"
ADD FOREIGN KEY("task_id") REFERENCES "tasks"("id")
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE "task_assignments"
ADD FOREIGN KEY("user_id") REFERENCES "users"("id")
ON UPDATE CASCADE ON DELETE CASCADE; 