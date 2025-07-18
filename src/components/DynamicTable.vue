<template>
  <div class="dynamic-table">
    <div class="table-header">
      <h3>{{ title }}</h3>
      <div class="table-controls">
        <input 
          v-model="searchTerm" 
          type="text" 
          placeholder="Search..." 
          class="search-input"
        >
        <select v-if="uniqueDevices.length > 0" v-model="selectedDevice" class="device-filter">
          <option value="">All Devices</option>
          <option v-for="device in uniqueDevices" :key="device" :value="device">
            Device {{ device }}
          </option>
        </select>
      </div>
    </div>
    
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" class="table-header-cell">
              {{ column.label }}
              <span class="sort-icon" @click="sortBy(column.key)">
                {{ getSortIcon(column.key) }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in filteredAndSortedData" :key="index" class="table-row">
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
    }
  },
  setup(props) {
    const searchTerm = ref('')
    const selectedDevice = ref('')
    const currentPage = ref(1)
    const itemsPerPage = ref(10)
    const sortColumn = ref('')
    const sortDirection = ref('asc')

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

    // 고유 디바이스 목록 (DEVICE 컬럼이 있을 때만)
    const uniqueDevices = computed(() => {
      if (!columns.value.some(col => col.key.toUpperCase() === 'DEVICE')) return []
      const deviceColumn = columns.value.find(col => col.key.toUpperCase() === 'DEVICE')
      if (!deviceColumn) return []
      
      const devices = props.data.map(row => row[deviceColumn.key]).filter(Boolean)
      return [...new Set(devices)]
    })

    // 필터링된 데이터
    const filteredData = computed(() => {
      let filtered = props.data

      // 디바이스 필터 (DEVICE 컬럼이 있을 때만)
      if (selectedDevice.value && uniqueDevices.value.length > 0) {
        const deviceColumn = columns.value.find(col => col.key.toUpperCase() === 'DEVICE')
        if (deviceColumn) {
          filtered = filtered.filter(row => row[deviceColumn.key] === selectedDevice.value)
        }
      }

      // 검색 필터
      if (searchTerm.value) {
        const term = searchTerm.value.toLowerCase()
        filtered = filtered.filter(row => 
          Object.values(row).some(value => 
            value && value.toString().toLowerCase().includes(term)
          )
        )
      }

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

    // 메서드들
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
      return value.toFixed(2)
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
      selectedDevice,
      currentPage,
      columns,
      uniqueDevices,
      filteredData,
      filteredAndSortedData,
      totalPages,
      startIndex,
      endIndex,
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

.search-input, .device-filter {
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

.search-input:focus, .device-filter:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.table-container {
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table-header-cell {
  background: #f8f9fa;
  padding: 1rem 0.75rem;
  font-weight: 600;
  text-align: left;
  border-bottom: 2px solid #e9ecef;
  position: sticky;
  top: 0;
  z-index: 10;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}

.table-header-cell:hover {
  background: #e9ecef;
}

.sort-icon {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  opacity: 0.6;
}

.table-row {
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: #f8f9fa;
}

.table-cell {
  padding: 0.75rem;
  border-bottom: 1px solid #e9ecef;
  vertical-align: middle;
}

.number-value {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #2563eb;
}

.device-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
}

.device-A { background: #dbeafe; color: #1e40af; }
.device-B { background: #dcfce7; color: #166534; }
.device-C { background: #fef3c7; color: #92400e; }

.text-value {
  color: #374151;
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
  color: #6b7280;
  font-size: 0.875rem;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.pagination-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.pagination-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

/* G/B 값 색상 스타일 */
.value-good {
  color: #10b981 !important;
  font-weight: 600;
}

.value-bad {
  color: #ef4444 !important;
  font-weight: 600;
}

/* Responsive */
@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .table-controls {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .search-input, .device-filter {
    width: 100%;
  }
}
</style>