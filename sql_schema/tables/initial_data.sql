-- Initial data for roles and users

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
  ('Admin', 'Administrator with full access', ''),
  ('Manager', 'Project manager with elevated permissions', ''),
  ('Member', 'Regular team member', '');

-- Insert mock users with hashed passwords (NHH@2025)
INSERT INTO users (username, password, email, full_name, role_id, status)
VALUES
  ('adminuser', '$2a$12$em3Y6VvIgyqXuQXjR9kEA.XMpFerlow4UjqpJuVOvUS2Nrz5z174O', 'admin@example.com', 'Alice Admin', 1, 'active'),
  ('manageruser', '$2a$12$CU9mnZneuQmM3X892xPUauaO9LOJ8n9dDCuURXdHtbAzxXmEO0i9a', 'manager@example.com', 'Bob Manager', 2, 'active'),
  ('member1', '$2a$12$4CPV7L5eFYhfZ6BpRtTOEu95Zn4RRutubW5bejVM0qhwl3qO6jBoy', 'member1@example.com', 'Charlie Member', 3, 'active'),
  ('member2', '$2a$12$A3mANe9YDuG6OU8MYbEh3etyCxxx7NlhuZJRe0YKRdC/hbq9hPtYO', 'member2@example.com', 'Dana Member', 3, 'active');

-- Insert teams with admin as leader
INSERT INTO teams (name, description, leader_id) VALUES
  ('Development', 'Software development and engineering team', 1),
  ('Design', 'UI/UX and graphic design team', 1),
  ('Marketing', 'Marketing and promotional activities team', 1),
  ('Sales', 'Sales and business development team', 1),
  ('Finance', 'Financial management and accounting team', 1),
  ('HR', 'Human resources and personnel management team', 1),
  ('IT', 'Information technology and infrastructure team', 1),
  ('Market Research', 'Market analysis and research team', 1);
