INSERT INTO roles (role_name) VALUES 
('admin'),
('client')
ON CONFLICT (role_name) DO NOTHING;
