### API Backend cần triển khai

1. **API Dự án**
   - [ ] `api/projects/list.php` - Lấy danh sách dự án
   - [ ] `api/projects/detail.php` - Lấy chi tiết dự án
   - [ ] `api/projects/create.php` - Tạo dự án mới
   - [ ] `api/projects/update.php` - Cập nhật dự án
   - [ ] `api/projects/delete.php` - Xóa dự án

2. **API Công việc**
   - [ ] `api/tasks/list.php` - Lấy danh sách công việc
   - [ ] `api/tasks/detail.php` - Lấy chi tiết công việc
   - [ ] `api/tasks/create.php` - Tạo công việc mới
   - [ ] `api/tasks/update.php` - Cập nhật công việc
   - [ ] `api/tasks/delete.php` - Xóa công việc

3. **API Thành viên**
   - [ ] `api/members/list.php` - Lấy danh sách thành viên
   - [ ] `api/members/update.php` - Cập nhật thông tin thành viên
   - [ ] `api/members/delete.php` - Xóa thành viên

4. **API Quản lý tài khoản**
   - [ ] `api/forgot-password.php` - Quên mật khẩu
   - [ ] `api/reset-password.php` - Đặt lại mật khẩu
   - [ ] `api/profile-update.php` - Cập nhật thông tin cá nhân

5. **API Vai trò và Phân quyền**
   - [ ] `api/roles/list.php` - Lấy danh sách vai trò
   - [ ] `api/roles/create.php` - Tạo vai trò mới
   - [ ] `api/roles/update.php` - Cập nhật vai trò
   - [ ] `api/roles/delete.php` - Xóa vai trò
   - [ ] `api/roles/assign.php` - Gán vai trò cho người dùng
   - [ ] `api/permissions/check.php` - Kiểm tra quyền hạn

6. **API Thông báo**
   - [ ] `api/notifications/list.php` - Lấy danh sách thông báo
   - [ ] `api/notifications/mark-read.php` - Đánh dấu đã đọc
   - [ ] `api/notifications/create.php` - Tạo thông báo mới
   - [ ] `api/notifications/delete.php` - Xóa thông báo

7. **API Lịch và Sự kiện**
   - [ ] `api/calendar/events.php` - Lấy danh sách sự kiện
   - [ ] `api/calendar/create-event.php` - Tạo sự kiện mới
   - [ ] `api/calendar/update-event.php` - Cập nhật sự kiện
   - [ ] `api/calendar/delete-event.php` - Xóa sự kiện

8. **API Báo cáo và Thống kê**
   - [ ] `api/reports/project-stats.php` - Thống kê dự án
   - [ ] `api/reports/user-stats.php` - Thống kê người dùng
   - [ ] `api/reports/team-stats.php` - Thống kê nhóm
   - [ ] `api/reports/export.php` - Xuất báo cáo

9. **API Quản lý Tệp**
   - [ ] `api/files/upload.php` - Tải tệp lên
   - [ ] `api/files/download.php` - Tải tệp xuống
   - [ ] `api/files/list.php` - Danh sách tệp
   - [ ] `api/files/delete.php` - Xóa tệp
   - [ ] `api/files/share.php` - Chia sẻ tệp

10. **API Chấm công**
    - [ ] `api/attendance/check-in.php` - API chấm công vào
    - [ ] `api/attendance/check-out.php` - API chấm công ra
    - [ ] `api/attendance/list.php` - Danh sách chấm công
    - [ ] `api/attendance/report.php` - Báo cáo chấm công

11. **API Bình luận và Trao đổi**
    - [ ] `api/comments/list.php` - Lấy danh sách bình luận
    - [ ] `api/comments/create.php` - Tạo bình luận mới
    - [ ] `api/comments/update.php` - Cập nhật bình luận
    - [ ] `api/comments/delete.php` - Xóa bình luận

12. **API Dashboard**
    - [ ] `api/dashboard/summary.php` - Tổng quan dashboard
    - [ ] `api/dashboard/recent-activities.php` - Hoạt động gần đây
    - [ ] `api/dashboard/stats.php` - Thống kê nhanh

## Cơ sở dữ liệu

### Cấu trúc bảng

1. **users** - Thông tin người dùng
   - id, username, email, password, full_name, role_id, avatar, created_at, updated_at, last_login, status

2. **roles** - Vai trò người dùng
   - id, name, description, permissions, created_at, updated_at

3. **projects** - Thông tin dự án
   - id, name, description, status, start_date, end_date, manager_id, client_id, budget, priority, created_at, updated_at

4. **tasks** - Công việc trong dự án
   - id, project_id, name, description, status, priority, due_date, assigned_to, created_by, created_at, updated_at

5. **project_members** - Thành viên dự án
   - id, project_id, user_id, role, joined_at

6. **comments** - Bình luận về công việc
   - id, task_id, user_id, content, created_at, updated_at

7. **files** - Tệp đính kèm
   - id, name, path, size, type, uploaded_by, project_id, task_id, uploaded_at

8. **notifications** - Thông báo
   - id, user_id, type, content, is_read, related_id, created_at

9. **events** - Sự kiện lịch
   - id, title, description, start_time, end_time, location, created_by, project_id, created_at, updated_at

10. **attendance** - Chấm công
    - id, user_id, date, check_in, check_out, total_hours, status, note

11. **teams** - Nhóm làm việc
    - id, name, description, leader_id, created_at, updated_at

12. **team_members** - Thành viên nhóm
    - id, team_id, user_id, role, joined_at