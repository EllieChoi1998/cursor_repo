<template>
  <div class="rag-answer-list">
    <div v-for="item in answer" :key="item.file_path" class="rag-answer-card">
      <div class="file-info">
        <span class="file-icon">📄</span>
        <span class="file-name">{{ item.file_name }}</span>
      </div>
      <div class="file-path" :title="item.file_path">{{ item.file_path }}</div>
      <div class="similarity">
        <span class="similarity-label">유사도:</span>
        <span class="similarity-value" :style="{ color: getSimilarityColor(item.similarity) }">
          {{ item.similarity.toFixed(2) }}
        </span>
      </div>
      <a :href="item.file_path" download class="download-btn">
        ⬇️ 다운로드
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RAGAnswerList',
  props: {
    answer: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    getSimilarityColor(sim) {
      // 0.9 이상: 파랑, 0.8~0.9: 보라, 이하: 회색
      if (sim >= 0.9) return '#2b6cb0'
      if (sim >= 0.8) return '#764ba2'
      return '#888'
    }
  }
}
</script>

<style scoped>
.rag-answer-list {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  margin: 1.5rem 0;
}
.rag-answer-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(102,126,234,0.08);
  padding: 1.2rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: box-shadow 0.2s;
  position: relative;
}
.rag-answer-card:hover {
  box-shadow: 0 4px 16px rgba(102,126,234,0.18);
}
.file-info {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  font-size: 1.1rem;
  font-weight: 600;
}
.file-icon {
  font-size: 1.3rem;
}
.file-name {
  font-weight: bold;
  color: #2b6cb0;
  word-break: break-all;
}
.file-path {
  font-size: 0.92rem;
  color: #888;
  word-break: break-all;
  cursor: pointer;
}
.similarity {
  font-size: 0.98rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.similarity-label {
  color: #666;
}
.similarity-value {
  font-weight: bold;
}
.download-btn {
  margin-top: 0.5rem;
  align-self: flex-start;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.45rem 1.1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.98rem;
  font-weight: 500;
  transition: background 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.download-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  color: #fff;
}
</style> 