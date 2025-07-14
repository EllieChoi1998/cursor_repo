<template>
  <div class="commonality-table">
    <div class="table-header">
      <h3>Commonality Analysis Table</h3>
      <div class="table-controls">
        <input 
          v-model="searchTerm" 
          type="text" 
          placeholder="Search..." 
          class="search-input"
        >
        <select v-model="selectedDevice" class="device-filter">
          <option value="">All Devices</option>
          <option v-for="device in uniqueDevices" :key="device" :value="device">
            Device {{ device }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- Commonality Summary Section -->
    <div v-if="commonalityData" class="commonality-summary">
      <div class="summary-header">
        <h4>Commonality Analysis Summary</h4>
      </div>
      <div class="summary-content">
        <div class="summary-section">
          <h5>Good Lots ({{ commonalityData.good_lots.length }})</h5>
          <div class="lot-list good-lots">
            <span v-for="lot in commonalityData.good_lots" :key="lot" class="lot-badge good">
              {{ lot }}
            </span>
          </div>
        </div>
        <div class="summary-section">
          <h5>Bad Lots ({{ commonalityData.bad_lots.length }})</h5>
          <div class="lot-list bad-lots">
            <span v-for="lot in commonalityData.bad_lots" :key="lot" class="lot-badge bad">
              {{ lot }}
            </span>
          </div>
        </div>
        <div class="summary-section">
          <h5>Good Wafers ({{ commonalityData.good_wafers.length }})</h5>
          <div class="wafer-list good-wafers">
            <span v-for="wafer in commonalityData.good_wafers" :key="wafer" class="wafer-badge good">
              {{ wafer }}
            </span>
          </div>
        </div>
        <div class="summary-section">
          <h5>Bad Wafers ({{ commonalityData.bad_wafers.length }})</h5>
          <div class="wafer-list bad-wafers">
            <span v-for="wafer in commonalityData.bad_wafers" :key="wafer" class="wafer-badge bad">
              {{ wafer }}
            </span>
          </div>
        </div>

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
              <span v-else class="text-value">
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
import { defineComponent, ref, computed, watch } from 'vue'

export default defineComponent({
  name: 'CommonalityTable',
  props: {
    data: {
      type: Array,
      default: () => []
    },
    commonalityData: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const searchTerm = ref('')
    const selectedDevice = ref('')
    const currentPage = ref(1)
    const itemsPerPage = ref(10)
    const sortColumn = ref('DATE_WAFER_ID')
    const sortDirection = ref('asc')

    // 컬럼 정의 (약 10개 컬럼)
    const columns = [
      { key: 'DATE_WAFER_ID', label: 'Date Wafer ID', type: 'number' },
      { key: 'MIN', label: 'Min Value', type: 'number' },
      { key: 'MAX', label: 'Max Value', type: 'number' },
      { key: 'Q1', label: 'Q1', type: 'number' },
      { key: 'Q2', label: 'Q2 (Median)', type: 'number' },
      { key: 'Q3', label: 'Q3', type: 'number' },
      { key: 'DEVICE', label: 'Device', type: 'device' },
      { key: 'USL', label: 'USL', type: 'number' },
      { key: 'TGT', label: 'Target', type: 'number' },
      { key: 'LSL', label: 'LSL', type: 'number' },
      { key: 'UCL', label: 'UCL', type: 'number' },
      { key: 'LCL', label: 'LCL', type: 'number' }
    ]

    // 데이터는 이미 객체 형태 (DataFrame JSON)
    const processedData = computed(() => {
      return props.data
    })

    // 고유 디바이스 목록
    const uniqueDevices = computed(() => {
      const devices = processedData.value.map(row => row.DEVICE)
      return [...new Set(devices)]
    })

    // 필터링된 데이터
    const filteredData = computed(() => {
      let filtered = processedData.value

      // 디바이스 필터
      if (selectedDevice.value) {
        filtered = filtered.filter(row => row.DEVICE === selectedDevice.value)
      }

      // 검색 필터
      if (searchTerm.value) {
        const term = searchTerm.value.toLowerCase()
        filtered = filtered.filter(row => 
          Object.values(row).some(value => 
            value.toString().toLowerCase().includes(term)
          )
        )
      }

      return filtered
    })

    // 정렬된 데이터
    const sortedData = computed(() => {
      const sorted = [...filteredData.value].sort((a, b) => {
        const aVal = a[sortColumn.value]
        const bVal = b[sortColumn.value]
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortDirection.value === 'asc' ? aVal - bVal : bVal - aVal
        } else {
          const aStr = aVal.toString()
          const bStr = bVal.toString()
          return sortDirection.value === 'asc' 
            ? aStr.localeCompare(bStr) 
            : bStr.localeCompare(aStr)
        }
      })
      
      return sorted
    })

    // 페이지네이션
    const totalPages = computed(() => Math.ceil(sortedData.value.length / itemsPerPage.value))
    const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage.value)
    const endIndex = computed(() => Math.min(startIndex.value + itemsPerPage.value, sortedData.value.length))

    const filteredAndSortedData = computed(() => {
      return sortedData.value.slice(startIndex.value, endIndex.value)
    })

    // 정렬 함수
    const sortBy = (column) => {
      if (sortColumn.value === column) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortColumn.value = column
        sortDirection.value = 'asc'
      }
    }

    // 정렬 아이콘
    const getSortIcon = (column) => {
      if (sortColumn.value !== column) return '↕️'
      return sortDirection.value === 'asc' ? '↑' : '↓'
    }

    // 페이지네이션 함수
    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
      }
    }

    const previousPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--
      }
    }

    // 숫자 포맷팅
    const formatNumber = (value) => {
      if (typeof value === 'number') {
        return value.toFixed(2)
      }
      return value
    }

    // 검색어나 필터 변경 시 첫 페이지로 이동
    watch([searchTerm, selectedDevice], () => {
      currentPage.value = 1
    })

    return {
      searchTerm,
      selectedDevice,
      currentPage,
      columns,
      uniqueDevices,
      filteredAndSortedData,
      filteredData,
      totalPages,
      startIndex,
      endIndex,
      sortBy,
      getSortIcon,
      nextPage,
      previousPage,
      formatNumber
    }
  }
})
</script>

<style scoped>
.commonality-table {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-top: 1rem;
}

.table-header {
  padding: 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.table-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.table-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  padding: 0.5rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.search-input:focus {
  border-color: #667eea;
}

.device-filter {
  padding: 0.5rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  background: white;
  cursor: pointer;
}

.device-filter:focus {
  border-color: #667eea;
}

.table-container {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  table-layout: fixed;
}

.table-header-cell {
  background: #f8f9fa;
  padding: 1rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 10;
  cursor: pointer;
  user-select: none;
  /* display: flex; */
  /* align-items: center; */
  /* gap: 0.5rem; */
  white-space: nowrap;
  vertical-align: middle;
}

.table-header-cell .sort-icon {
  font-size: 0.85em;
  opacity: 0.7;
  margin-left: 0.3em;
  display: inline-block;
  float: right;
}

.table-header-cell:hover {
  background: #e9ecef;
}

.table-row {
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: #f8f9fa;
}

.table-cell {
  padding: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.number-value {
  font-family: 'Courier New', monospace;
  font-weight: 500;
  color: #495057;
}

.text-value {
  color: #333;
}

.device-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
  min-width: 30px;
  display: inline-block;
}

.device-A {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.device-B {
  background: rgba(118, 75, 162, 0.2);
  color: #764ba2;
}

.device-C {
  background: rgba(255, 128, 10, 0.2);
  color: #ff800a;
}

.table-footer {
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.pagination-info {
  color: #666;
  font-size: 0.9rem;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pagination-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #667eea;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.9rem;
  color: #666;
  margin: 0 0.5rem;
}

/* Commonality Summary Styles */
.commonality-summary {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 1rem;
  overflow: hidden;
}

.summary-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 1.5rem;
}

.summary-header h4 {
  margin: 0;
  font-size: 1.1rem;
}

.summary-content {
  padding: 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.summary-section h5 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 0.95rem;
  font-weight: 600;
}

.lot-list, .wafer-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.lot-badge, .wafer-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  display: inline-block;
}

.lot-badge.good, .wafer-badge.good {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
  border: 1px solid rgba(40, 167, 69, 0.3);
}

.lot-badge.bad, .wafer-badge.bad {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
  border: 1px solid rgba(220, 53, 69, 0.3);
}



/* 반응형 디자인 */
@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .table-controls {
    flex-direction: column;
  }
  
  .table-footer {
    flex-direction: column;
    text-align: center;
  }
  
  .data-table {
    font-size: 0.8rem;
  }
  
  .table-cell {
    padding: 0.5rem 0.25rem;
  }
  
  .summary-content {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
</style> 