<template>
  <div class="two-dynamic-tables">
    <div class="tables-header">
      <h3>{{ title }}</h3>
      <div class="global-controls">
        <input 
          v-model="globalSearchTerm" 
          type="text" 
          placeholder="전체 테이블 검색..." 
          class="global-search-input"
        >
        <button 
          v-if="hasAnyActiveFilters"
          @click="clearAllFilters" 
          class="emoji-btn clear-all-filters-btn"
          title="모든 필터 초기화"
        >
          🗑️
        </button>
      </div>
    </div>
    
    <div class="tables-container">
      <!-- Lot Hold Module Table -->
      <div class="table-wrapper">
        <div class="table-section-header">
          <h4>Lot Hold</h4>
          <span class="table-count">{{ lotHoldData.length }} items</span>
        </div>
        <div class="dynamic-table">
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
                  <th v-for="column in lotHoldColumns" :key="column.key" class="table-header-cell">
                    <div class="header-content" @click="toggleColumnFilter('lotHold', column.key)">
                      <span class="header-text">{{ column.label }}</span>
                      <div class="header-actions">
                        <span class="sort-icon" @click.stop="sortBy('lotHold', column.key)">
                          {{ getSortIcon('lotHold', column.key) }}
                        </span>
                        <span class="filter-icon" :class="{ 'active': hasActiveFilter('lotHold', column.key) }">
                          🔍
                        </span>
                      </div>
                    </div>
                    
                    <!-- 컬럼별 드롭다운 필터 -->
                    <div v-if="activeFilterColumn.table === 'lotHold' && activeFilterColumn.column === column.key" class="column-filter-dropdown">
                      <div class="filter-dropdown-content">
                        <div class="filter-section">
                          <label>텍스트 검색:</label>
                          <input 
                            v-model="lotHoldColumnFilters[column.key]" 
                            type="text" 
                            :placeholder="`${column.label} 검색...`" 
                            class="filter-input"
                            @input="updateColumnFilter('lotHold', column.key)"
                          >
                        </div>
                        <div class="filter-section">
                          <label>값 선택:</label>
                          <select 
                            v-model="lotHoldColumnSelectFilters[column.key]" 
                            class="filter-select"
                            @change="updateColumnFilter('lotHold', column.key)"
                          >
                            <option value="">모든 값</option>
                            <option 
                              v-for="value in getUniqueValues('lotHold', column.key)" 
                              :key="value" 
                              :value="value"
                            >
                              {{ value }}
                            </option>
                          </select>
                        </div>
                        <div class="filter-actions">
                          <button 
                            @click="clearColumnFilter('lotHold', column.key)"
                            class="emoji-btn clear-filter-btn"
                            :class="{ 'disabled': !lotHoldColumnFilters[column.key] && !lotHoldColumnSelectFilters[column.key] }"
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
                <tr v-for="(row, index) in filteredAndSortedLotHoldData" :key="index" class="table-row">
                  <!-- 인덱스 컬럼 -->
                  <td v-if="showIndex" class="table-cell index-cell">
                    <span class="index-number">{{ lotHoldStartIndex + index + 1 }}</span>
                  </td>
                  <td v-for="column in lotHoldColumns" :key="column.key" class="table-cell">
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
              Showing {{ lotHoldStartIndex + 1 }} to {{ lotHoldEndIndex }} of {{ filteredLotHoldData.length }} entries
              <span v-if="hasActiveFilters" class="filtered-info">
                (필터링됨: {{ lotHoldData.length }} → {{ filteredLotHoldData.length }})
              </span>
            </div>
            <div class="pagination-controls">
              <button 
                @click="previousPage('lotHold')" 
                :disabled="lotHoldCurrentPage === 1"
                class="pagination-btn"
              >
                Previous
              </button>
              <span class="page-info">{{ lotHoldCurrentPage }} / {{ lotHoldTotalPages }}</span>
              <button 
                @click="nextPage('lotHold')" 
                :disabled="lotHoldCurrentPage === lotHoldTotalPages"
                class="pagination-btn"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Inline Lot Module Table -->
      <div class="table-wrapper">
        <div class="table-section-header">
          <h4>PE Confirm Module</h4>
          <span class="table-count">{{ inlineLotData.length }} items</span>
        </div>
        <div class="dynamic-table">
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
                  <th v-for="column in inlineLotColumns" :key="column.key" class="table-header-cell">
                    <div class="header-content" @click="toggleColumnFilter('inlineLot', column.key)">
                      <span class="header-text">{{ column.label }}</span>
                      <div class="header-actions">
                        <span class="sort-icon" @click.stop="sortBy('inlineLot', column.key)">
                          {{ getSortIcon('inlineLot', column.key) }}
                        </span>
                        <span class="filter-icon" :class="{ 'active': hasActiveFilter('inlineLot', column.key) }">
                          🔍
                        </span>
                      </div>
                    </div>
                    
                    <!-- 컬럼별 드롭다운 필터 -->
                    <div v-if="activeFilterColumn.table === 'inlineLot' && activeFilterColumn.column === column.key" class="column-filter-dropdown">
                      <div class="filter-dropdown-content">
                        <div class="filter-section">
                          <label>텍스트 검색:</label>
                          <input 
                            v-model="inlineLotColumnFilters[column.key]" 
                            type="text" 
                            :placeholder="`${column.label} 검색...`" 
                            class="filter-input"
                            @input="updateColumnFilter('inlineLot', column.key)"
                          >
                        </div>
                        <div class="filter-section">
                          <label>값 선택:</label>
                          <select 
                            v-model="inlineLotColumnSelectFilters[column.key]" 
                            class="filter-select"
                            @change="updateColumnFilter('inlineLot', column.key)"
                          >
                            <option value="">모든 값</option>
                            <option 
                              v-for="value in getUniqueValues('inlineLot', column.key)" 
                              :key="value" 
                              :value="value"
                            >
                              {{ value }}
                            </option>
                          </select>
                        </div>
                        <div class="filter-actions">
                          <button 
                            @click="clearColumnFilter('inlineLot', column.key)"
                            class="emoji-btn clear-filter-btn"
                            :class="{ 'disabled': !inlineLotColumnFilters[column.key] && !inlineLotColumnSelectFilters[column.key] }"
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
                <tr v-for="(row, index) in filteredAndSortedInlineLotData" :key="index" class="table-row">
                  <!-- 인덱스 컬럼 -->
                  <td v-if="showIndex" class="table-cell index-cell">
                    <span class="index-number">{{ inlineLotStartIndex + index + 1 }}</span>
                  </td>
                  <td v-for="column in inlineLotColumns" :key="column.key" class="table-cell">
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
              Showing {{ inlineLotStartIndex + 1 }} to {{ inlineLotEndIndex }} of {{ filteredInlineLotData.length }} entries
              <span v-if="hasActiveFilters" class="filtered-info">
                (필터링됨: {{ inlineLotData.length }} → {{ filteredInlineLotData.length }})
              </span>
            </div>
            <div class="pagination-controls">
              <button 
                @click="previousPage('inlineLot')" 
                :disabled="inlineLotCurrentPage === 1"
                class="pagination-btn"
              >
                Previous
              </button>
              <span class="page-info">{{ inlineLotCurrentPage }} / {{ inlineLotTotalPages }}</span>
              <button 
                @click="nextPage('inlineLot')" 
                :disabled="inlineLotCurrentPage === inlineLotTotalPages"
                class="pagination-btn"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'

export default defineComponent({
  name: 'TwoDynamicTables',
  props: {
    data: {
      type: Array,
      default: () => []
    },
    title: {
      type: String,
      default: 'Two Dynamic Tables'
    },
    showIndex: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    // 전역 검색
    const globalSearchTerm = ref('')
    
    // 페이지네이션
    const lotHoldCurrentPage = ref(1)
    const inlineLotCurrentPage = ref(1)
    const itemsPerPage = ref(10)
    
    // 정렬
    const lotHoldSortColumn = ref('')
    const lotHoldSortDirection = ref('asc')
    const inlineLotSortColumn = ref('')
    const inlineLotSortDirection = ref('asc')
    
    // 컬럼별 필터 상태
    const lotHoldColumnFilters = ref({})
    const lotHoldColumnSelectFilters = ref({})
    const inlineLotColumnFilters = ref({})
    const inlineLotColumnSelectFilters = ref({})
    
    // 현재 활성화된 필터 컬럼
    const activeFilterColumn = ref({ table: null, column: null })

    // 데이터 추출 (이미 파싱된 JSON 객체/배열 처리)
    const lotHoldData = computed(() => {
      if (!props.data || props.data.length === 0) return []
      
      console.log('🔍 TwoDynamicTables received data:', props.data)
      console.log('🔍 First item:', props.data[0])
      console.log('🔍 lot_hold type:', typeof props.data[0]?.lot_hold)
      console.log('🔍 lot_hold data:', props.data[0]?.lot_hold)
      
      const firstItem = props.data[0]
      if (firstItem && firstItem.lot_hold) {
        // 이미 파싱된 데이터를 그대로 사용 (문자열인 경우만 파싱)
        if (typeof firstItem.lot_hold === 'string') {
          try {
            const parsed = JSON.parse(firstItem.lot_hold)
            return Array.isArray(parsed) ? parsed : []
          } catch (error) {
            console.error('Error parsing lot_hold string:', error)
            return []
          }
        } else {
          // 이미 객체/배열인 경우 그대로 사용
          return Array.isArray(firstItem.lot_hold) ? firstItem.lot_hold : []
        }
      }
      return []
    })

    const inlineLotData = computed(() => {
      if (!props.data || props.data.length === 0) return []
      
      const firstItem = props.data[0]
      // pe_confirm_module 또는 pe_module 지원
      const peData = firstItem?.pe_confirm_module || firstItem?.pe_module
      
      console.log('🔍 PE data type:', typeof peData)
      console.log('🔍 PE data:', peData)
      if (peData) {
        // 이미 파싱된 데이터를 그대로 사용 (문자열인 경우만 파싱)
        if (typeof peData === 'string') {
          try {
            const parsed = JSON.parse(peData)
            return Array.isArray(parsed) ? parsed : []
          } catch (error) {
            console.error('Error parsing PE module string:', error)
            return []
          }
        } else {
          // 이미 객체/배열인 경우 그대로 사용
          return Array.isArray(peData) ? peData : []
        }
      }
      return []
    })

    // 동적 컬럼 생성
    const lotHoldColumns = computed(() => {
      const firstRow = lotHoldData.value && lotHoldData.value.length > 0 ? lotHoldData.value[0] : null
      if (!firstRow) return []
      
      return Object.keys(firstRow).map(key => {
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

    const inlineLotColumns = computed(() => {
      const firstRow = inlineLotData.value && inlineLotData.value.length > 0 ? inlineLotData.value[0] : null
      if (!firstRow) return []
      
      return Object.keys(firstRow).map(key => {
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

    // 각 컬럼의 고유 값들 반환
    const getUniqueValues = (tableType, columnKey) => {
      const data = tableType === 'lotHold' ? lotHoldData.value : inlineLotData.value
      const values = data.map(row => row[columnKey]).filter(Boolean)
      return [...new Set(values)].sort()
    }

    // 필터링된 데이터
    const filteredLotHoldData = computed(() => {
      let filtered = lotHoldData.value

      // 전역 검색 필터
      if (globalSearchTerm.value) {
        const term = globalSearchTerm.value.toLowerCase()
        filtered = filtered.filter(row => 
          Object.values(row).some(value => 
            value && value.toString().toLowerCase().includes(term)
          )
        )
      }

      // 컬럼별 필터 적용
      Object.keys(lotHoldColumnFilters.value).forEach(columnKey => {
        const filterValue = lotHoldColumnFilters.value[columnKey]
        if (filterValue) {
          const term = filterValue.toLowerCase()
          filtered = filtered.filter(row => {
            const cellValue = row[columnKey]
            return cellValue && cellValue.toString().toLowerCase().includes(term)
          })
        }
      })

      // 컬럼별 선택 필터 적용
      Object.keys(lotHoldColumnSelectFilters.value).forEach(columnKey => {
        const selectValue = lotHoldColumnSelectFilters.value[columnKey]
        if (selectValue) {
          filtered = filtered.filter(row => row[columnKey] === selectValue)
        }
      })

      return filtered
    })

    const filteredInlineLotData = computed(() => {
      let filtered = inlineLotData.value

      // 전역 검색 필터
      if (globalSearchTerm.value) {
        const term = globalSearchTerm.value.toLowerCase()
        filtered = filtered.filter(row => 
          Object.values(row).some(value => 
            value && value.toString().toLowerCase().includes(term)
          )
        )
      }

      // 컬럼별 필터 적용
      Object.keys(inlineLotColumnFilters.value).forEach(columnKey => {
        const filterValue = inlineLotColumnFilters.value[columnKey]
        if (filterValue) {
          const term = filterValue.toLowerCase()
          filtered = filtered.filter(row => {
            const cellValue = row[columnKey]
            return cellValue && cellValue.toString().toLowerCase().includes(term)
          })
        }
      })

      // 컬럼별 선택 필터 적용
      Object.keys(inlineLotColumnSelectFilters.value).forEach(columnKey => {
        const selectValue = inlineLotColumnSelectFilters.value[columnKey]
        if (selectValue) {
          filtered = filtered.filter(row => row[columnKey] === selectValue)
        }
      })

      return filtered
    })

    // 정렬된 데이터
    const sortedLotHoldData = computed(() => {
      if (!lotHoldSortColumn.value) return filteredLotHoldData.value
      
      const sorted = [...filteredLotHoldData.value].sort((a, b) => {
        const aVal = a[lotHoldSortColumn.value]
        const bVal = b[lotHoldSortColumn.value]
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return lotHoldSortDirection.value === 'asc' ? aVal - bVal : bVal - aVal
        } else {
          const aStr = (aVal ?? '').toString()
          const bStr = (bVal ?? '').toString()
          return lotHoldSortDirection.value === 'asc' 
            ? aStr.localeCompare(bStr) 
            : bStr.localeCompare(aStr)
        }
      })
      
      return sorted
    })

    const sortedInlineLotData = computed(() => {
      if (!inlineLotSortColumn.value) return filteredInlineLotData.value
      
      const sorted = [...filteredInlineLotData.value].sort((a, b) => {
        const aVal = a[inlineLotSortColumn.value]
        const bVal = b[inlineLotSortColumn.value]
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return inlineLotSortDirection.value === 'asc' ? aVal - bVal : bVal - aVal
        } else {
          const aStr = (aVal ?? '').toString()
          const bStr = (bVal ?? '').toString()
          return inlineLotSortDirection.value === 'asc' 
            ? aStr.localeCompare(bStr) 
            : bStr.localeCompare(aStr)
        }
      })
      
      return sorted
    })

    // 페이지네이션 계산
    const lotHoldTotalPages = computed(() => Math.ceil(filteredLotHoldData.value.length / itemsPerPage.value))
    const lotHoldStartIndex = computed(() => (lotHoldCurrentPage.value - 1) * itemsPerPage.value)
    const lotHoldEndIndex = computed(() => Math.min(lotHoldStartIndex.value + itemsPerPage.value, filteredLotHoldData.value.length))

    const inlineLotTotalPages = computed(() => Math.ceil(filteredInlineLotData.value.length / itemsPerPage.value))
    const inlineLotStartIndex = computed(() => (inlineLotCurrentPage.value - 1) * itemsPerPage.value)
    const inlineLotEndIndex = computed(() => Math.min(inlineLotStartIndex.value + itemsPerPage.value, filteredInlineLotData.value.length))

    const filteredAndSortedLotHoldData = computed(() => {
      return sortedLotHoldData.value.slice(lotHoldStartIndex.value, lotHoldEndIndex.value)
    })

    const filteredAndSortedInlineLotData = computed(() => {
      return sortedInlineLotData.value.slice(inlineLotStartIndex.value, inlineLotEndIndex.value)
    })

    // 필터 관련 함수들
    const hasAnyActiveFilters = computed(() => {
      return globalSearchTerm.value || 
             Object.values(lotHoldColumnFilters.value).some(v => v) ||
             Object.values(lotHoldColumnSelectFilters.value).some(v => v) ||
             Object.values(inlineLotColumnFilters.value).some(v => v) ||
             Object.values(inlineLotColumnSelectFilters.value).some(v => v)
    })

    const hasActiveFilters = computed(() => {
      return globalSearchTerm.value || 
             Object.values(lotHoldColumnFilters.value).some(v => v) ||
             Object.values(lotHoldColumnSelectFilters.value).some(v => v) ||
             Object.values(inlineLotColumnFilters.value).some(v => v) ||
             Object.values(inlineLotColumnSelectFilters.value).some(v => v)
    })

    const hasActiveFilter = (tableType, columnKey) => {
      if (tableType === 'lotHold') {
        return lotHoldColumnFilters.value[columnKey] || lotHoldColumnSelectFilters.value[columnKey]
      } else {
        return inlineLotColumnFilters.value[columnKey] || inlineLotColumnSelectFilters.value[columnKey]
      }
    }

    // 컬럼 필터 토글
    const toggleColumnFilter = (tableType, columnKey) => {
      if (activeFilterColumn.value.table === tableType && activeFilterColumn.value.column === columnKey) {
        activeFilterColumn.value = { table: null, column: null }
      } else {
        activeFilterColumn.value = { table: tableType, column: columnKey }
      }
    }

    // 컬럼 필터 닫기
    const closeColumnFilter = () => {
      activeFilterColumn.value = { table: null, column: null }
    }

    // 컬럼 필터 업데이트
    const updateColumnFilter = (tableType) => {
      if (tableType === 'lotHold') {
        lotHoldCurrentPage.value = 1
      } else {
        inlineLotCurrentPage.value = 1
      }
    }

    // 컬럼 필터 초기화
    const clearColumnFilter = (tableType, columnKey) => {
      if (tableType === 'lotHold') {
        lotHoldColumnFilters.value[columnKey] = ''
        lotHoldColumnSelectFilters.value[columnKey] = ''
        lotHoldCurrentPage.value = 1
      } else {
        inlineLotColumnFilters.value[columnKey] = ''
        inlineLotColumnSelectFilters.value[columnKey] = ''
        inlineLotCurrentPage.value = 1
      }
    }

    // 모든 필터 초기화
    const clearAllFilters = () => {
      globalSearchTerm.value = ''
      lotHoldColumnFilters.value = {}
      lotHoldColumnSelectFilters.value = {}
      inlineLotColumnFilters.value = {}
      inlineLotColumnSelectFilters.value = {}
      activeFilterColumn.value = { table: null, column: null }
      lotHoldCurrentPage.value = 1
      inlineLotCurrentPage.value = 1
    }

    const sortBy = (tableType, column) => {
      if (tableType === 'lotHold') {
        if (lotHoldSortColumn.value === column) {
          lotHoldSortDirection.value = lotHoldSortDirection.value === 'asc' ? 'desc' : 'asc'
        } else {
          lotHoldSortColumn.value = column
          lotHoldSortDirection.value = 'asc'
        }
        lotHoldCurrentPage.value = 1
      } else {
        if (inlineLotSortColumn.value === column) {
          inlineLotSortDirection.value = inlineLotSortDirection.value === 'asc' ? 'desc' : 'asc'
        } else {
          inlineLotSortColumn.value = column
          inlineLotSortDirection.value = 'asc'
        }
        inlineLotCurrentPage.value = 1
      }
    }

    const getSortIcon = (tableType, column) => {
      if (tableType === 'lotHold') {
        if (lotHoldSortColumn.value !== column) return '↕️'
        return lotHoldSortDirection.value === 'asc' ? '↑' : '↓'
      } else {
        if (inlineLotSortColumn.value !== column) return '↕️'
        return inlineLotSortDirection.value === 'asc' ? '↑' : '↓'
      }
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

    const previousPage = (tableType) => {
      if (tableType === 'lotHold') {
        if (lotHoldCurrentPage.value > 1) {
          lotHoldCurrentPage.value--
        }
      } else {
        if (inlineLotCurrentPage.value > 1) {
          inlineLotCurrentPage.value--
        }
      }
    }

    const nextPage = (tableType) => {
      if (tableType === 'lotHold') {
        if (lotHoldCurrentPage.value < lotHoldTotalPages.value) {
          lotHoldCurrentPage.value++
        }
      } else {
        if (inlineLotCurrentPage.value < inlineLotTotalPages.value) {
          inlineLotCurrentPage.value++
        }
      }
    }

    return {
      globalSearchTerm,
      lotHoldCurrentPage,
      inlineLotCurrentPage,
      lotHoldColumns,
      inlineLotColumns,
      lotHoldData,
      inlineLotData,
      filteredLotHoldData,
      filteredInlineLotData,
      filteredAndSortedLotHoldData,
      filteredAndSortedInlineLotData,
      lotHoldTotalPages,
      inlineLotTotalPages,
      lotHoldStartIndex,
      lotHoldEndIndex,
      inlineLotStartIndex,
      inlineLotEndIndex,
      lotHoldSortColumn,
      lotHoldSortDirection,
      inlineLotSortColumn,
      inlineLotSortDirection,
      activeFilterColumn,
      lotHoldColumnFilters,
      lotHoldColumnSelectFilters,
      inlineLotColumnFilters,
      inlineLotColumnSelectFilters,
      hasAnyActiveFilters,
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
.two-dynamic-tables {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin: 1rem 0;
}

.tables-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.tables-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.global-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.global-search-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.875rem;
  min-width: 200px;
}

.global-search-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.global-search-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.tables-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
}

.table-wrapper {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
}

.table-section-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.table-count {
  font-size: 0.875rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.dynamic-table {
  background: white;
}

.table-container {
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 0.8rem;
}

.table-header-cell {
  position: relative;
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  padding: 0;
  font-weight: 600;
  color: #495057;
  text-align: left;
  min-width: 100px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.header-content:hover {
  background-color: #e9ecef;
}

.header-text {
  font-weight: 600;
  font-size: 0.75rem;
}

.header-actions {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.sort-icon {
  cursor: pointer;
  font-size: 0.7rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.sort-icon:hover {
  opacity: 1;
}

.filter-icon {
  font-size: 0.7rem;
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
  padding: 0.75rem;
}

.filter-section {
  margin-bottom: 0.75rem;
}

.filter-section:last-child {
  margin-bottom: 0;
}

.filter-section label {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.filter-input, .filter-select {
  width: 100%;
  padding: 0.375rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.75rem;
  background: white;
}

.filter-input:focus, .filter-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25);
}

.filter-actions {
  display: flex;
  gap: 0.25rem;
  justify-content: flex-end;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e9ecef;
}

.emoji-btn {
  padding: 0.375rem;
  border: 1px solid #ced4da;
  border-radius: 50%;
  background: white;
  color: #6c757d;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 1.5rem;
  height: 1.5rem;
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
  padding: 0.75rem;
  font-size: 0.75rem;
  color: #495057;
  border-right: 1px solid #e9ecef;
}

.table-cell:last-child {
  border-right: none;
}

/* 인덱스 컬럼 스타일 */
.index-header {
  width: 60px;
  min-width: 60px;
  max-width: 60px;
  text-align: center;
  background: #e9ecef !important;
}

.index-header .header-content {
  justify-content: center;
  padding: 0.75rem 0.25rem;
}

.index-cell {
  width: 60px;
  min-width: 60px;
  max-width: 60px;
  text-align: center;
  padding: 0.75rem 0.25rem;
  background: #f8f9fa;
  font-weight: 500;
  color: #6c757d;
  border-right: 2px solid #dee2e6;
}

.index-number {
  font-size: 0.75rem;
  font-weight: 600;
  color: #495057;
}

.number-value {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #28a745;
}

.device-badge {
  padding: 0.125rem 0.25rem;
  border-radius: 8px;
  font-size: 0.7rem;
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
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.pagination-info {
  font-size: 0.75rem;
  color: #6c757d;
}

.filtered-info {
  color: #667eea;
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.pagination-btn {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
  color: #495057;
  font-size: 0.75rem;
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
  font-size: 0.75rem;
  color: #6c757d;
  margin: 0 0.25rem;
}

/* 반응형 디자인 */
@media (max-width: 1200px) {
  .tables-container {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .table-container {
    max-height: 500px;
  }
}

@media (max-width: 768px) {
  .tables-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .global-controls {
    justify-content: center;
  }
  
  .global-search-input {
    min-width: 150px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 0.25rem;
    align-items: flex-start;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .filter-dropdown-content {
    padding: 0.5rem;
  }
  
  .filter-actions {
    flex-direction: column;
  }
  
  .table-footer {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
  }
  
  .pagination-controls {
    justify-content: center;
  }
  
  .table-section-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
    text-align: center;
  }
}
</style>