<template>
  <div class="chat-room-list">
    <div class="chat-room-header">
      <h3>채팅방 목록</h3>
      <button @click="createNewChat" class="new-chat-btn">
        <span>+</span>
      </button>
    </div>
    
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>채팅방 목록을 불러오는 중...</p>
    </div>
    
    <div v-else-if="chatRooms.length === 0" class="empty-state">
      <div class="empty-icon">💬</div>
      <p>채팅방이 없습니다</p>
      <button @click="createNewChat" class="create-first-chat-btn">
        첫 번째 채팅방 만들기
      </button>
    </div>
    
    <div v-else class="chat-rooms">
      <div 
        v-for="room in chatRooms" 
        :key="room.id"
        :class="['chat-room-item', { 'active': room.id === activeChatId }]"
        @click="selectChatRoom(room.id)"
      >
        <div class="chat-room-info">
          <div class="chat-room-title">
            <span class="room-icon">💬</span>
            <span class="room-name">{{ room.name }}</span>
          </div>
          <div class="chat-room-meta">
            <span class="room-type">{{ room.dataType.toUpperCase() }}</span>
            <span class="room-time">{{ formatTime(room.lastMessageTime) }}</span>
          </div>
          <div class="chat-room-preview">
            {{ room.lastMessage || '새로운 채팅방입니다.' }}
          </div>
        </div>
        <div class="chat-room-actions">
          <button 
            @click.stop="deleteChatRoom(room.id)" 
            class="delete-room-btn"
            title="채팅방 삭제"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'

export default defineComponent({
  name: 'ChatRoomList',
  props: {
    activeChatId: {
      type: String,
      default: null
    },
    chatRooms: {
      type: Array,
      default: () => []
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select-room', 'create-room', 'delete-room'],
  setup(props, { emit }) {


    const formatTime = (timestamp) => {
      const now = new Date()
      const diff = now - timestamp
      const minutes = Math.floor(diff / (1000 * 60))
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))

      if (minutes < 60) {
        return `${minutes}분 전`
      } else if (hours < 24) {
        return `${hours}시간 전`
      } else {
        return `${days}일 전`
      }
    }

    const selectChatRoom = (roomId) => {
      emit('select-room', roomId)
    }

    const createNewChat = () => {
      // 데이터 타입 선택을 위한 간단한 모달이나 드롭다운이 필요할 수 있지만,
      // 일단 기본값으로 'pcm'을 사용
      const newRoom = {
        dataType: 'pcm'  // 기본값으로 PCM 설정
      }
      emit('create-room', newRoom)
    }

    const deleteChatRoom = (roomId) => {
      emit('delete-room', roomId)
    }

    return {
      formatTime,
      selectChatRoom,
      createNewChat,
      deleteChatRoom
    }
  }
})
</script>

<style scoped>
.chat-room-list {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.chat-room-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.new-chat-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  transition: transform 0.2s ease;
}

.new-chat-btn:hover {
  transform: scale(1.1);
}

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chat-rooms {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.chat-room-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 0.5rem;
  border: 1px solid transparent;
}

.chat-room-item:hover {
  background: #f8f9fa;
  border-color: #e0e0e0;
}

.chat-room-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.chat-room-item.active .chat-room-meta .room-type {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.chat-room-item.active .chat-room-meta .room-time {
  color: rgba(255, 255, 255, 0.8);
}

.chat-room-item.active .chat-room-preview {
  color: rgba(255, 255, 255, 0.9);
}

.chat-room-info {
  flex: 1;
  min-width: 0;
  max-width: 220px; /* 최대 너비 제한 */
  overflow: hidden; /* 넘치는 내용 숨김 */
}

.chat-room-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.room-icon {
  font-size: 1rem;
}

.room-name {
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-room-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.room-type {
  padding: 0.125rem 0.375rem;
  background: #667eea;
  color: white;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}

.room-time {
  color: #666;
  font-size: 0.75rem;
}

.chat-room-preview {
  color: #666;
  font-size: 0.8rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
  max-width: 200px; /* 최대 너비 제한 */
  word-break: break-all; /* 긴 단어 강제 줄바꿈 */
}

.chat-room-actions {
  margin-left: 0.5rem;
}

.delete-room-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(220, 53, 69, 0.1);
  color: #dc3545;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  transition: all 0.2s ease;
  opacity: 0;
}

.chat-room-item:hover .delete-room-btn {
  opacity: 1;
}

.delete-room-btn:hover {
  background: #dc3545;
  color: white;
  transform: scale(1.1);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state p {
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.create-first-chat-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 25px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.create-first-chat-btn:hover {
  background: #667eea;
  color: white;
}

/* Responsive Design */
@media (max-width: 768px) {
  .chat-room-header {
    padding: 0.75rem 1rem;
  }
  
  .chat-room-header h3 {
    font-size: 1rem;
  }
  
  .chat-rooms {
    padding: 0.25rem;
  }
  
  .chat-room-item {
    padding: 0.5rem;
  }
  
  .room-name {
    font-size: 0.85rem;
  }
  
  .chat-room-preview {
    font-size: 0.75rem;
  }
}
</style> 