-- Database triggers for automatic timestamp management and data validation

-- Triggers for updating updated_at timestamp
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to prevent manual updates to joined_at
CREATE TRIGGER prevent_team_member_joined_at_update
    BEFORE UPDATE ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION prevent_joined_at_manual_update();

CREATE TRIGGER prevent_project_member_joined_at_update
    BEFORE UPDATE ON project_members
    FOR EACH ROW
    EXECUTE FUNCTION prevent_joined_at_manual_update();

-- Triggers to prevent manual updates to created_at
CREATE TRIGGER prevent_users_created_at_update
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER prevent_roles_created_at_update
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER prevent_user_tokens_created_at_update
    BEFORE UPDATE ON user_tokens
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER prevent_teams_created_at_update
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER prevent_projects_created_at_update
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER prevent_tasks_created_at_update
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER prevent_comments_created_at_update
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

-- Triggers to handle joined_at during INSERT
CREATE TRIGGER handle_team_member_joined_at_insert
    BEFORE INSERT ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION handle_joined_at_insert();

CREATE TRIGGER handle_project_member_joined_at_insert
    BEFORE INSERT ON project_members
    FOR EACH ROW
    EXECUTE FUNCTION handle_joined_at_insert();

-- Triggers for created_at handling during INSERT
CREATE TRIGGER handle_users_created_at_insert
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

CREATE TRIGGER handle_roles_created_at_insert
    BEFORE INSERT ON roles
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

CREATE TRIGGER handle_user_tokens_created_at_insert
    BEFORE INSERT ON user_tokens
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

CREATE TRIGGER handle_teams_created_at_insert
    BEFORE INSERT ON teams
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

CREATE TRIGGER handle_projects_created_at_insert
    BEFORE INSERT ON projects
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

CREATE TRIGGER handle_tasks_created_at_insert
    BEFORE INSERT ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

CREATE TRIGGER handle_comments_created_at_insert
    BEFORE INSERT ON comments
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

-- Triggers for assigned_at handling
CREATE TRIGGER handle_task_assignments_assigned_at_insert
    BEFORE INSERT ON task_assignments
    FOR EACH ROW
    EXECUTE FUNCTION handle_assigned_at_insert();

CREATE TRIGGER prevent_task_assignments_assigned_at_update
    BEFORE UPDATE ON task_assignments
    FOR EACH ROW
    EXECUTE FUNCTION prevent_assigned_at_manual_update();

-- Triggers for forgot_password_requests table
CREATE TRIGGER update_forgot_password_requests_updated_at
    BEFORE UPDATE ON forgot_password_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER prevent_forgot_password_requests_created_at_update
    BEFORE UPDATE ON forgot_password_requests
    FOR EACH ROW
    EXECUTE FUNCTION prevent_created_at_manual_update();

CREATE TRIGGER handle_forgot_password_requests_created_at_insert
    BEFORE INSERT ON forgot_password_requests
    FOR EACH ROW
    EXECUTE FUNCTION handle_created_at_insert();

-- Triggers for updated_at handling during INSERT
CREATE TRIGGER handle_users_updated_at_insert
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert();

CREATE TRIGGER handle_roles_updated_at_insert
    BEFORE INSERT ON roles
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert();

CREATE TRIGGER handle_teams_updated_at_insert
    BEFORE INSERT ON teams
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert();

CREATE TRIGGER handle_projects_updated_at_insert
    BEFORE INSERT ON projects
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert();

CREATE TRIGGER handle_tasks_updated_at_insert
    BEFORE INSERT ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert();

CREATE TRIGGER handle_comments_updated_at_insert
    BEFORE INSERT ON comments
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert();

CREATE TRIGGER handle_forgot_password_requests_updated_at_insert
    BEFORE INSERT ON forgot_password_requests
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at_insert(); 