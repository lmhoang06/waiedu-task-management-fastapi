# API Backend TODO (RESTful & CRUD-complete)

## 1. Users
- [x] GET    /users           - List users
- [x] POST   /users           - Create user
- [x] GET    /users/{id}      - Get user detail
- [x] PATCH  /users/{id}      - Update user
- [x] DELETE /users/{id}      - Delete user

## 2. Roles
- [x] GET    /roles           - List roles
- [x] POST   /roles           - Create role
- [x] GET    /roles/{id}      - Get role detail
- [x] PATCH  /roles/{id}      - Update role
- [x] DELETE /roles/{id}      - Delete role

## 3. Teams
- [x] GET    /teams           - List teams
- [x] POST   /teams           - Create team
- [x] GET    /teams/{team_id}      - Get team detail
- [x] PUT    /teams/{team_id}      - Update team
- [x] DELETE /teams/{team_id}      - Delete team

## 4. Team Members
- [x] GET    /teams/{team_id}/members         - List team members
- [x] POST   /teams/{team_id}/members         - Add member to team
- [x] DELETE /teams/{team_id}/members/{user_id} - Remove member from team

## 5. Projects
- [x] GET    /projects           - List projects
- [x] POST   /projects           - Create project
- [x] GET    /projects/{id}      - Get project detail
- [x] PATCH  /projects/{id}      - Update project (including status)
- [x] DELETE /projects/{id}      - Delete project

## 6. Project Members
- [x] GET    /projects/{project_id}/members         - List project members
- [x] POST   /projects/{project_id}/members         - Add member to project
- [x] DELETE /projects/{project_id}/members/{user_id} - Remove member from project

## 7. Tasks
- [x] GET    /tasks           - List tasks
- [x] POST   /tasks           - Create task
- [x] GET    /tasks/{task_id} - Get task detail
- [x] PATCH  /tasks/{task_id} - Update task
- [x] DELETE /tasks/{task_id} - Delete task

## 8. Task Assignments
- [x] GET    /tasks/{task_id}/assignees         - List assignees for a task
- [x] POST   /tasks/{task_id}/assignees         - Assign user to task
- [x] DELETE /tasks/{task_id}/assignees/{user_id} - Unassign user from task

## 9. Comments
- [x] GET    /tasks/{task_id}/comments           - List comments for a task
- [x] POST   /tasks/{task_id}/comments           - Create comment for a task
- [x] GET    /comments/{id}                      - Get comment detail
- [x] PATCH  /comments/{id}                      - Update comment
- [x] DELETE /comments/{id}                      - Delete comment

## 10. Auth & Account
- [x] POST   /auth/login         - User login
- [x] POST   /auth/logout        - User logout
- [x] POST   /auth/forgot-password - Forgot password

## 11. Roles & Permissions (extra)
- [x] POST   /roles/{id}/assign      - Assign role to user
- [ ] POST   /permissions/check      - Check permission

## 12. Dashboard & Reports
- [ ] GET    /dashboard/summary         - Dashboard summary
- [ ] GET    /dashboard/recent-activities - Recent activities
- [ ] GET    /dashboard/stats           - Quick stats
- [ ] GET    /reports/project-stats     - Project statistics
- [ ] GET    /reports/user-stats        - User statistics
- [ ] GET    /reports/team-stats        - Team statistics
- [ ] GET    /reports/export            - Export report

## 12. Admin Requests
- [ ] GET    /admin/requests                                      - List all admin requests (all types)
- [x] forgot-password
    - [x] GET    /admin/requests/forgot-password                       - List all forgot password requests
    - [x] GET    /admin/requests/forgot-password/{request_id}          - Get forgot password request detail
    - [x] POST   /admin/requests/forgot-password/{request_id}/approve  - Approve forgot password request
    - [x] POST   /admin/requests/forgot-password/{request_id}/reject   - Reject forgot password request

### Note: Each admin request type (e.g., forgot-password, project, etc.) should have its own handler/module for processing. The admin request process is designed to support multiple request types, each with its own logic and endpoints as needed.

---

# Database Architecture (PostgreSQL)

## Core Tables
- **users**: id, username, password, email, full_name, role_id, created_at, updated_at, status, last_login, avatar
- **roles**: id, name, description, permissions, created_at, updated_at
- **user_tokens**: id, user_id, token, created_at, expires_at
- **teams**: id, name, description, leader_id, created_at, updated_at
- **team_members**: id, team_id, user_id, role, joined_at
- **forgot_password_requests**: id, user_id, new_password, status, created_at, updated_at

## Project Management
- **projects**: id, name, description, status, start_date, end_date, manager_id, budget, priority, created_at, updated_at
- **project_members**: id, project_id, user_id, role, joined_at
- **tasks**: id, project_id, name, description, status, priority, due_date, created_by, created_at, updated_at
- **task_assignments**: id, task_id, user_id, assigned_at
- **comments**: id, task_id, user_id, content, created_at, updated_at 