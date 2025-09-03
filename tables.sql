-- Chat Analysis Database Schema
-- PostgreSQL Database Tables

-- 유저 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 채팅방 테이블 (채팅방 삭제 시에도 데이터 보존을 위해 soft delete 사용)
CREATE TABLE IF NOT EXISTS chatrooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

-- 메시지 테이블
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(255) PRIMARY KEY,
    chatroom_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    data_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 봇 응답 테이블
CREATE TABLE IF NOT EXISTS bot_responses (
    id VARCHAR(255) PRIMARY KEY,
    message_id VARCHAR(255) NOT NULL,
    chatroom_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    content JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 채팅 히스토리 테이블 (채팅방 삭제되어도 보존)
CREATE TABLE IF NOT EXISTS chat_histories (
    chat_id SERIAL PRIMARY KEY,
    chatroom_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    chat_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 유저 스토리지 테이블 (세션 스토리지 대체)
CREATE TABLE IF NOT EXISTS user_storage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    session_id VARCHAR(255) NOT NULL,
    user_data JSONB NOT NULL,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chatrooms_user_id ON chatrooms(user_id);
CREATE INDEX IF NOT EXISTS idx_chatrooms_is_deleted ON chatrooms(is_deleted);
CREATE INDEX IF NOT EXISTS idx_messages_chatroom_id ON messages(chatroom_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_bot_responses_chatroom_id ON bot_responses(chatroom_id);
CREATE INDEX IF NOT EXISTS idx_bot_responses_user_id ON bot_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_histories_chatroom_id ON chat_histories(chatroom_id);
CREATE INDEX IF NOT EXISTS idx_chat_histories_user_id ON chat_histories(user_id);
CREATE INDEX IF NOT EXISTS idx_user_storage_user_id ON user_storage(user_id);
CREATE INDEX IF NOT EXISTS idx_user_storage_session_id ON user_storage(session_id);
CREATE INDEX IF NOT EXISTS idx_user_storage_is_active ON user_storage(is_active);

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chatrooms_updated_at BEFORE UPDATE ON chatrooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_storage_updated_at BEFORE UPDATE ON user_storage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰 생성: 활성 채팅방만 조회
CREATE OR REPLACE VIEW active_chatrooms AS
SELECT 
    id,
    name,
    user_id,
    created_at,
    updated_at
FROM chatrooms 
WHERE is_deleted = FALSE;

-- 뷰 생성: 유저별 채팅방 통계
CREATE OR REPLACE VIEW user_chatroom_stats AS
SELECT 
    u.user_id,
    u.username,
    COUNT(c.id) as total_chatrooms,
    COUNT(CASE WHEN c.is_deleted = FALSE THEN 1 END) as active_chatrooms,
    COUNT(ch.chat_id) as total_messages
FROM users u
LEFT JOIN chatrooms c ON u.user_id = c.user_id
LEFT JOIN chat_histories ch ON c.id = ch.chatroom_id
GROUP BY u.user_id, u.username;

-- 샘플 데이터 삽입 (개발용)
INSERT INTO users (user_id, username, email, full_name) VALUES 
('developer', 'developer', 'developer@example.com', 'Developer User')
ON CONFLICT (user_id) DO NOTHING;