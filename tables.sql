-- Chat Analysis Database Schema
-- PostgreSQL Database Tables

-- 유저 테이블
CREATE TABLE IF NOT EXISTS service_users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 채팅방 테이블 (채팅방 삭제 시에도 데이터 보존을 위해 soft delete 사용)
CREATE TABLE IF NOT EXISTS service_chatrooms (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

-- 메시지 테이블
CREATE TABLE IF NOT EXISTS service_messages (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chatroom_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    data_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 봇 응답 테이블
CREATE TABLE IF NOT EXISTS service_bot_responses (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id INTEGER NOT NULL,
    chatroom_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 채팅 히스토리 테이블 (채팅방 삭제되어도 보존)
CREATE TABLE IF NOT EXISTS service_chat_histories (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chatroom_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    chat_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 유저 스토리지 테이블 (세션 스토리지 대체)
CREATE TABLE IF NOT EXISTS service_user_storage (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    user_data JSONB NOT NULL,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 샘플 데이터 삽입 (개발용)
INSERT INTO service_users (user_id, username, email, full_name) VALUES 
('developer', 'developer', 'developer@example.com', 'Developer User')
ON CONFLICT (user_id) DO NOTHING;