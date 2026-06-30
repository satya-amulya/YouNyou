CREATE DATABASE IF NOT EXISTS claude;
USE claude;

CREATE TABLE IF NOT EXISTS goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT 1,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    deadline DATETIME NOT NULL,
    status ENUM('active', 'completed', 'failed') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    goal_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    scheduled_date DATETIME NOT NULL,
    estimated_hours FLOAT NOT NULL,
    actual_hours FLOAT DEFAULT NULL,
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium',
    completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME DEFAULT NULL,
    timer_started_at DATETIME DEFAULT NULL,
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS future_states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT 1,
    goal_id INT NOT NULL,
    mood VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0.7,
    stress FLOAT DEFAULT 0.3,
    success_probability FLOAT DEFAULT 0.7,
    narrative TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT 1,
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM tasks;
SELECT * FROM future_states;