-- Test SQL script to create a sample table and test the MCP toolbox

-- 1. Create a table with user and agent responses
CREATE TABLE IF NOT EXISTS conversation_log (
    id SERIAL PRIMARY KEY,
    user_response TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Insert sample data
INSERT INTO conversation_log (user_response, agent_response) VALUES
('Hello, how are you?', 'I am doing well, thank you! How can I help you today?'),
('What is the weather?', 'I can check the weather for you. Which location?'),
('Tell me a joke', 'Why did the database administrator leave his wife? She had one-to-many relationships!');

-- 3. Query the data
SELECT * FROM conversation_log;
