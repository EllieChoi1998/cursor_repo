/**
 * Plotly 그래프 빌드 헬퍼 함수들
 * App.vue의 긴 함수들을 분리
 */

// 간단한 유틸 함수들
export const getValueByPath = (obj, path) => {
  if (!path) return obj
  const keys = String(path).split('.')
  let result = obj
  for (const key of keys) {
    if (result == null) return null
    result = result[key]
  }
  return result
}

export const coerceNumber = (value) => {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number' && !isNaN(value)) return value
  const num = Number(value)
  return isNaN(num) ? null : num
}

export const mergeDeep = (target, source) => {
  if (!source) return target
  const output = { ...target }
  Object.keys(source).forEach(key => {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      output[key] = mergeDeep(target[key] || {}, source[key])
    } else {
      output[key] = source[key]
    }
  })
  return output
}

// 집계 함수
export const aggregatePoints = (points, agg) => {
  if (!agg || agg === 'identity' || agg === 'none') return points
  const mode = agg.toLowerCase()
  const grouped = new Map()

  points.forEach(({ x, y }) => {
    const key = x ?? '__missing__'
    if (!grouped.has(key)) {
      grouped.set(key, { values: [], order: grouped.size })
    }
    if (y !== null && y !== undefined) {
      grouped.get(key).values.push(y)
    }
  })

  const summarise = (values) => {
    if (!values.length) return null
    switch (mode) {
      case 'sum': return values.reduce((acc, val) => acc + val, 0)
      case 'avg':
      case 'average':
      case 'mean': return values.reduce((acc, val) => acc + val, 0) / values.length
      case 'max': return Math.max(...values)
      case 'min': return Math.min(...values)
      case 'count': return values.length
      case 'median': {
        const sorted = [...values].sort((a, b) => a - b)
        const mid = Math.floor(sorted.length / 2)
        return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
      }
      default: return values[values.length - 1]
    }
  }

  return Array.from(grouped.entries())
    .sort((a, b) => a[1].order - b[1].order)
    .map(([x, { values }]) => ({ x: x === '__missing__' ? null : x, y: summarise(values) }))
}

// 시리즈별 포인트 분리
export const splitSeriesPoints = (rows, { xField, yField, seriesField }) => {
  const seriesMap = new Map()
  const safeField = (field) => field || null

  rows.forEach((row) => {
    const xValue = safeField(xField) ? getValueByPath(row, xField) : null
    const yRaw = safeField(yField) ? getValueByPath(row, yField) : null
    const yValue = coerceNumber(yRaw)
    const seriesKey = safeField(seriesField) ? getValueByPath(row, seriesField) : 'Series'
    if (!seriesMap.has(seriesKey)) {
      seriesMap.set(seriesKey, [])
    }
    seriesMap.get(seriesKey).push({ x: xValue, y: yValue })
  })

  return seriesMap
}

// Transform 적용
export const applyDeclarativeTransforms = (rows, transforms) => {
  if (!Array.isArray(transforms) || !transforms.length) return rows
  return transforms.reduce((currentRows, transform) => {
    if (!transform || typeof transform !== 'object') return currentRows
    if (transform.type === 'filter') {
      const { field, op = '==', value } = transform
      return currentRows.filter((row) => {
        const target = getValueByPath(row, field)
        switch (op) {
          case '>': return target > value
          case '>=': return target >= value
          case '<': return target < value
          case '<=': return target <= value
          case '!=':
          case '<>': return target !== value
          case 'in': return Array.isArray(value) ? value.includes(target) : false
          case 'not_in': return Array.isArray(value) ? !value.includes(target) : true
          case 'contains':
            return Array.isArray(target) ? target.includes(value) : String(target ?? '').includes(String(value ?? ''))
          default: return target === value
        }
      })
    }
    if (transform.type === 'sort') {
      const { field, direction = 'asc' } = transform
      const multiplier = direction === 'desc' ? -1 : 1
      return [...currentRows].sort((a, b) => {
        const valueA = getValueByPath(a, field)
        const valueB = getValueByPath(b, field)
        if (valueA === valueB) return 0
        return valueA > valueB ? multiplier : -multiplier
      })
    }
    return currentRows
  }, rows)
}
