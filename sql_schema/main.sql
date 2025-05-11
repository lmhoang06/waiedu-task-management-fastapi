-- Main SQL file for the task management system
-- This file imports all other SQL files in the correct order

-- Import enums first as they are used by tables
\i enums/enums.sql

-- Import core tables
\i tables/core_tables.sql

-- Import project and task tables
\i tables/project_tables.sql

-- Insert initial data (roles and users)
\i tables/initial_data.sql

-- Import foreign key constraints
\i constraints/foreign_keys.sql

-- Import functions
\i functions/functions.sql

-- Import triggers
\i triggers/triggers.sql 