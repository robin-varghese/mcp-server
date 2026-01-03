-- Demo: A-Level Students at John Henry Newman School
-- Create students table with subject marks

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    school VARCHAR(100) DEFAULT 'John_Henry_Newman',
    mathematics INTEGER CHECK (mathematics >= 0 AND mathematics <= 100),
    physics INTEGER CHECK (physics >= 0 AND physics <= 100),
    chemistry INTEGER CHECK (chemistry >= 0 AND chemistry <= 100),
    biology INTEGER CHECK (biology >= 0 AND biology <= 100),
    english INTEGER CHECK (english >= 0 AND english <= 100),
    enrollment_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample student data
INSERT INTO students (student_name, mathematics, physics, chemistry, biology, english, enrollment_year) VALUES
('Emma Watson', 92, 88, 90, 85, 94, 2023),
('James Chen', 95, 92, 89, 78, 82, 2023),
('Sofia Rodriguez', 78, 75, 82, 88, 91, 2023),
('Mohammed Ali', 88, 90, 87, 82, 79, 2023),
('Olivia Smith', 91, 85, 88, 92, 89, 2023),
('Liam O''Connor', 82, 79, 76, 81, 85, 2024),
('Amara Johnson', 94, 91, 93, 89, 90, 2024),
('Ethan Brown', 76, 72, 78, 74, 80, 2024),
('Isabella Garcia', 89, 87, 91, 90, 88, 2024),
('Noah Patel', 93, 94, 92, 85, 87, 2024);

-- Verify data
SELECT COUNT(*) as total_students FROM students;
SELECT * FROM students ORDER BY student_name;
