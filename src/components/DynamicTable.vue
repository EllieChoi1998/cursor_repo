<template>
  <div class="dynamic-table">
    <div class="table-header">
      <h3>{{ title }}</h3>
      <div class="table-controls">
        <input 
          v-model="searchTerm" 
          type="text" 
          placeholder="전체 검색..." 
          class="search-input"
        >
        <button 
          v-if="hasActiveFilters"
          @click="clearAllFilters" 
          class="emoji-btn clear-all-filters-btn"
          title="모든 필터 초기화"
        >
          🗑️
        </button>
      </div>
    </div>
    
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <!-- 인덱스 컬럼 헤더 -->
            <th v-if="showIndex" class="table-header-cell index-header">
              <div class="header-content">
                <span class="header-text">색인</span>
              </div>
            </th>
            <th v-for="column in columns" :key="column.key" class="table-header-cell">
              <div class="header-content" @click="toggleColumnFilter(column.key)">
                <span class="header-text">{{ column.label }}</span>
                <div class="header-actions">
                  <span class="sort-icon" @click.stop="sortBy(column.key)">
                    {{ getSortIcon(column.key) }}
                  </span>
                  <span class="filter-icon" :class="{ 'active': hasActiveFilter(column.key) }">
                    🔍
                  </span>
                </div>
              </div>
              
              <!-- 컬럼별 드롭다운 필터 -->
              <div v-if="activeFilterColumn === column.key" class="column-filter-dropdown">
                <div class="filter-dropdown-content">
                  <div class="filter-section">
                    <label>텍스트 검색:</label>
                    <input 
                      v-model="columnFilters[column.key]" 
                      type="text" 
                      :placeholder="`${column.label} 검색...`" 
                      class="filter-input"
                      @input="updateColumnFilter(column.key)"
                    >
                  </div>
                  <div class="filter-section">
                    <label>값 선택:</label>
                    <select 
                      v-model="columnSelectFilters[column.key]" 
                      class="filter-select"
                      @change="updateColumnFilter(column.key)"
                    >
                      <option value="">모든 값</option>
                      <option 
                        v-for="value in getUniqueValues(column.key)" 
                        :key="value" 
                        :value="value"
                      >
                        {{ value }}
                      </option>
                    </select>
                  </div>
                  <div class="filter-actions">
                    <button 
                      @click="clearColumnFilter(column.key)"
                      class="emoji-btn clear-filter-btn"
                      :class="{ 'disabled': !columnFilters[column.key] && !columnSelectFilters[column.key] }"
                      title="필터 초기화"
                    >
                      🔄
                    </button>
                    <button @click="closeColumnFilter" class="emoji-btn close-filter-btn" title="닫기">
                      ❌
                    </button>
                  </div>
                </div>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in filteredAndSortedData" :key="index" class="table-row">
            <!-- 인덱스 컬럼 -->
            <td v-if="showIndex" class="table-cell index-cell">
              <span class="index-number">{{ startIndex + index + 1 }}</span>
            </td>
            <td v-for="column in columns" :key="column.key" class="table-cell">
              <span v-if="column.type === 'number'" class="number-value">
                {{ formatNumber(row[column.key]) }}
              </span>
              <span v-else-if="column.type === 'device'" class="device-badge" :class="`device-${row[column.key]}`">
                {{ row[column.key] }}
              </span>
              <span v-else class="text-value" :class="getValueColorClass(row[column.key])">
                {{ row[column.key] }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="table-footer">
      <div class="pagination-info">
        Showing {{ startIndex + 1 }} to {{ endIndex }} of {{ filteredData.length }} entries
        <span v-if="hasActiveFilters" class="filtered-info">
          (필터링됨: {{ originalDataLength }} → {{ filteredData.length }})
        </span>
      </div>
      <div class="pagination-controls">
        <button 
          @click="previousPage" 
          :disabled="currentPage === 1"
          class="pagination-btn"
        >
          Previous
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
          class="pagination-btn"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'

export default defineComponent({
  name: 'DynamicTable',
  props: {
    data: {
      type: Array,
      default: () => []
    },
    title: {
      type: String,
      default: 'Data Table'
    },
    showIndex: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    const searchTerm = ref('')
    const currentPage = ref(1)
    const itemsPerPage = ref(10)
    const sortColumn = ref('')
    const sortDirection = ref('asc')
    
    // 컬럼별 필터 상태
    const columnFilters = ref({})
    const columnSelectFilters = ref({})
    
    // 현재 활성화된 필터 컬럼
    const activeFilterColumn = ref(null)

    // 동적 컬럼 생성: 첫 row의 키를 기준으로
    const columns = computed(() => {
      const firstRow = props.data && props.data.length > 0 ? props.data[0] : null
      if (!firstRow) return []
      
      return Object.keys(firstRow).map(key => {
        // 숫자 타입 판별
        const value = firstRow[key]
        let type = 'text'
        
        if (typeof value === 'number') {
          type = 'number'
        } else if (key.toUpperCase() === 'DEVICE') {
          type = 'device'
        }
        
        return { 
          key, 
          label: key.replace(/_/g, ' ').toUpperCase(), 
          type 
        }
      })
    })

    // 원본 데이터 길이
    const originalDataLength = computed(() => props.data.length)

    // 각 컬럼의 고유 값들 반환
    const getUniqueValues = (columnKey) => {
      const values = props.data.map(row => row[columnKey]).filter(Boolean)
      return [...new Set(values)].sort()
    }

    // 필터링된 데이터
    const filteredData = computed(() => {
      let filtered = props.data

      // 전체 검색 필터
      if (searchTerm.value) {
        const term = searchTerm.value.toLowerCase()
        filtered = filtered.filter(row => 
          Object.values(row).some(value => 
            value && value.toString().toLowerCase().includes(term)
          )
        )
      }

      // 컬럼별 필터 적용
      Object.keys(columnFilters.value).forEach(columnKey => {
        const filterValue = columnFilters.value[columnKey]
        if (filterValue) {
          const term = filterValue.toLowerCase()
          filtered = filtered.filter(row => {
            const cellValue = row[columnKey]
            return cellValue && cellValue.toString().toLowerCase().includes(term)
          })
        }
      })

      // 컬럼별 선택 필터 적용
      Object.keys(columnSelectFilters.value).forEach(columnKey => {
        const selectValue = columnSelectFilters.value[columnKey]
        if (selectValue) {
          filtered = filtered.filter(row => row[columnKey] === selectValue)
        }
      })

      return filtered
    })

    // 정렬된 데이터
    const sortedData = computed(() => {
      if (!sortColumn.value) return filteredData.value
      
      const sorted = [...filteredData.value].sort((a, b) => {
        const aVal = a[sortColumn.value]
        const bVal = b[sortColumn.value]
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortDirection.value === 'asc' ? aVal - bVal : bVal - aVal
        } else {
          const aStr = (aVal ?? '').toString()
          const bStr = (bVal ?? '').toString()
          return sortDirection.value === 'asc' 
            ? aStr.localeCompare(bStr) 
            : bStr.localeCompare(aStr)
        }
      })
      
      return sorted
    })

    // 페이지네이션
    const totalPages = computed(() => Math.ceil(filteredData.value.length / itemsPerPage.value))
    const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage.value)
    const endIndex = computed(() => Math.min(startIndex.value + itemsPerPage.value, filteredData.value.length))

    const filteredAndSortedData = computed(() => {
      return sortedData.value.slice(startIndex.value, endIndex.value)
    })

    // 필터 관련 함수들
    const hasActiveFilters = computed(() => {
      return searchTerm.value || 
             Object.values(columnFilters.value).some(v => v) ||
             Object.values(columnSelectFilters.value).some(v => v)
    })

    const hasActiveFilter = (columnKey) => {
      return columnFilters.value[columnKey] || columnSelectFilters.value[columnKey]
    }

    // 컬럼 필터 토글
    const toggleColumnFilter = (columnKey) => {
      if (activeFilterColumn.value === columnKey) {
        activeFilterColumn.value = null
      } else {
        activeFilterColumn.value = columnKey
      }
    }

    // 컬럼 필터 닫기
    const closeColumnFilter = () => {
      activeFilterColumn.value = null
    }

    // 컬럼 필터 업데이트
    const updateColumnFilter = (columnKey) => {
      // 필터가 적용되면 페이지를 1로 리셋
      currentPage.value = 1
    }

    // 컬럼 필터 초기화
    const clearColumnFilter = (columnKey) => {
      columnFilters.value[columnKey] = ''
      columnSelectFilters.value[columnKey] = ''
      currentPage.value = 1
    }

    // 모든 필터 초기화
    const clearAllFilters = () => {
      searchTerm.value = ''
      columnFilters.value = {}
      columnSelectFilters.value = {}
      activeFilterColumn.value = null
      currentPage.value = 1
    }

    const sortBy = (column) => {
      if (sortColumn.value === column) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortColumn.value = column
        sortDirection.value = 'asc'
      }
      currentPage.value = 1
    }

    const getSortIcon = (column) => {
      if (sortColumn.value !== column) return '↕️'
      return sortDirection.value === 'asc' ? '↑' : '↓'
    }

    const formatNumber = (value) => {
      if (typeof value !== 'number') return value
      // 원본 데이터를 그대로 표시 - 데이터 조작 금지
      return value
    }

    // G/B 값에 따른 색상 클래스 반환
    const getValueColorClass = (value) => {
      if (value === 'G') {
        return 'value-good'
      } else if (value === 'B') {
        return 'value-bad'
      }
      return ''
    }

    const previousPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--
      }
    }

    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
      }
    }

    return {
      searchTerm,
      currentPage,
      columns,
      filteredData,
      filteredAndSortedData,
      totalPages,
      startIndex,
      endIndex,
      sortColumn,
      sortDirection,
      originalDataLength,
      activeFilterColumn,
      columnFilters,
      columnSelectFilters,
      hasActiveFilters,
      hasActiveFilter,
      getUniqueValues,
      toggleColumnFilter,
      closeColumnFilter,
      updateColumnFilter,
      clearColumnFilter,
      clearAllFilters,
      sortBy,
      getSortIcon,
      formatNumber,
      getValueColorClass,
      previousPage,
      nextPage
    }
  }
})
</script>

<style scoped>
.dynamic-table {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin: 1rem 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.table-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.table-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.875rem;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.search-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.table-header-cell {
  position: relative;
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  padding: 0;
  font-weight: 600;
  color: #495057;
  text-align: left;
  min-width: 120px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.header-content:hover {
  background-color: #e9ecef;
}

.header-text {
  font-weight: 600;
  font-size: 0.875rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.sort-icon {
  cursor: pointer;
  font-size: 0.75rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.sort-icon:hover {
  opacity: 1;
}

.filter-icon {
  font-size: 0.75rem;
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.filter-icon.active {
  opacity: 1;
  color: #667eea;
}

/* 컬럼 필터 드롭다운 */
.column-filter-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dee2e6;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.filter-dropdown-content {
  padding: 1rem;
}

.filter-section {
  margin-bottom: 1rem;
}

.filter-section:last-child {
  margin-bottom: 0;
}

.filter-section label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.filter-input, .filter-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.875rem;
  background: white;
}

.filter-input:focus, .filter-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25);
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.emoji-btn {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 50%;
  background: white;
  color: #6c757d;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.clear-filter-btn:hover {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
  transform: scale(1.1);
}

.close-filter-btn:hover {
  background: #6c757d;
  color: white;
  border-color: #6c757d;
  transform: scale(1.1);
}

.emoji-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.emoji-btn.disabled:hover {
  transform: none;
  background: white;
  color: #6c757d;
  border-color: #ced4da;
}

.clear-all-filters-btn {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.clear-all-filters-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.table-row {
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: #f8f9fa;
}

.table-cell {
  padding: 1rem;
  font-size: 0.875rem;
  color: #495057;
  border-right: 1px solid #e9ecef;
}

.table-cell:last-child {
  border-right: none;
}

/* 인덱스 컬럼 스타일 */
.index-header {
  width: 80px;
  min-width: 80px;
  max-width: 80px;
  text-align: center;
  background: #e9ecef !important;
}

.index-header .header-content {
  justify-content: center;
  padding: 1rem 0.5rem;
}

.index-cell {
  width: 80px;
  min-width: 80px;
  max-width: 80px;
  text-align: center;
  padding: 1rem 0.5rem;
  background: #f8f9fa;
  font-weight: 500;
  color: #6c757d;
  border-right: 2px solid #dee2e6;
}

.index-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: #495057;
}

.number-value {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #28a745;
}

.device-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.device-para1 {
  background: #e3f2fd;
  color: #1976d2;
}

.device-para2 {
  background: #f3e5f5;
  color: #7b1fa2;
}

.device-para3 {
  background: #e8f5e8;
  color: #388e3c;
}

.text-value {
  color: #495057;
}

.value-good {
  color: #28a745;
  font-weight: 600;
}

.value-bad {
  color: #dc3545;
  font-weight: 600;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.pagination-info {
  font-size: 0.875rem;
  color: #6c757d;
}

.filtered-info {
  color: #667eea;
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.pagination-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
  color: #495057;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.875rem;
  color: #6c757d;
  margin: 0 0.5rem;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .table-controls {
    justify-content: center;
  }
  
  .header-content {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .filter-dropdown-content {
    padding: 0.75rem;
  }
  
  .filter-actions {
    flex-direction: column;
  }
  
  .table-footer {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .pagination-controls {
    justify-content: center;
  }
}
</style>