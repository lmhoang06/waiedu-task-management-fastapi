-- Database functions for automatic timestamp management and data validation

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to prevent manual updates to joined_at timestamp
CREATE OR REPLACE FUNCTION prevent_team_member_joined_at_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.joined_at IS DISTINCT FROM NEW.joined_at THEN
        RAISE EXCEPTION 'Direct updates to joined_at are not allowed';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to prevent manual updates to created_at timestamp
CREATE OR REPLACE FUNCTION prevent_created_at_manual_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION 'Direct updates to created_at are not allowed';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to handle joined_at during INSERT with warning
CREATE OR REPLACE FUNCTION handle_joined_at_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.joined_at IS NOT NULL THEN
        RAISE WARNING 'Attempted to set custom joined_at timestamp. Resetting to CURRENT_TIMESTAMP.';
    END IF;
    NEW.joined_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to handle created_at during INSERT with warning
CREATE OR REPLACE FUNCTION handle_created_at_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.created_at IS NOT NULL THEN
        RAISE WARNING 'Attempted to set custom created_at timestamp. Resetting to CURRENT_TIMESTAMP.';
    END IF;
    NEW.created_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to handle assigned_at during INSERT with warning
CREATE OR REPLACE FUNCTION handle_assigned_at_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.assigned_at IS NOT NULL THEN
        RAISE WARNING 'Attempted to set custom assigned_at timestamp. Resetting to CURRENT_TIMESTAMP.';
    END IF;
    NEW.assigned_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to prevent manual updates to assigned_at timestamp
CREATE OR REPLACE FUNCTION prevent_assigned_at_manual_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.assigned_at IS DISTINCT FROM NEW.assigned_at THEN
        RAISE WARNING 'Attempted to set custom assigned_at timestamp. Resetting to CURRENT_TIMESTAMP.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql; 