// Plotly Graph Builder - 그래프 빌드 관련 함수들

/**
 * 선언적 transform을 데이터에 적용
 */
export const applyDeclarativeTransforms = (rows, transforms, getValueByPath) => {
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

/**
 * 포인트 집계
 */
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
      case 'sum':
        return values.reduce((acc, val) => acc + val, 0)
      case 'avg':
      case 'average':
      case 'mean':
        return values.reduce((acc, val) => acc + val, 0) / values.length
      case 'max':
        return Math.max(...values)
      case 'min':
        return Math.min(...values)
      case 'count':
        return values.length
      case 'median': {
        const sorted = [...values].sort((a, b) => a - b)
        const mid = Math.floor(sorted.length / 2)
        return sorted.length % 2
          ? sorted[mid]
          : (sorted[mid - 1] + sorted[mid]) / 2
      }
      default:
        return values[values.length - 1]
    }
  }

  const aggregated = Array.from(grouped.entries())
    .sort((a, b) => a[1].order - b[1].order)
    .map(([x, { values }]) => ({ x: x === '__missing__' ? null : x, y: summarise(values) }))

  return aggregated
}

/**
 * 시리즈별로 포인트 분리
 */
export const splitSeriesPoints = (rows, { xField, yField, seriesField }, getValueByPath, coerceNumber) => {
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

export default {
  applyDeclarativeTransforms,
  aggregatePoints,
  splitSeriesPoints
}
