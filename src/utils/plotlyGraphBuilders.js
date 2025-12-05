/**
 * Plotly Graph Builders - Bar, Line, Box 그래프 빌드 함수들
 */

import {
  getValueByPath,
  coerceNumber,
  mergeDeep,
  aggregatePoints,
  splitSeriesPoints
} from './plotlyHelpers.js'

/**
 * Build Bar Graph Figure
 */
export const buildBarFigure = (rows, encodings = {}, spec = {}) => {
  const xField = encodings.x?.field || encodings.category?.field
  const yField = encodings.y?.field || encodings.value?.field
  if (!xField || !yField) return null

  const seriesField = encodings.series?.field || encodings.group?.field || encodings.color?.field
  const aggregator = encodings.y?.agg || encodings.y?.aggregate || 'sum'
  const seriesMap = splitSeriesPoints(rows, { xField, yField, seriesField })

  const data = Array.from(seriesMap.entries()).map(([seriesKey, points]) => {
    const aggregated = aggregatePoints(points, aggregator)
    const trace = {
      type: 'bar',
      name: seriesKey,
      x: aggregated.map((point) => point.x),
      y: aggregated.map((point) => point.y)
    }
    if (spec.encodings?.color?.palette) {
      trace.marker = { color: spec.encodings.color.palette }
    }
    return trace
  })

  const defaultLayout = {
    height: 500,
    margin: { l: 80, r: 80, t: 100, b: 150, pad: 4 },
    xaxis: {
      tickangle: -45,
      tickfont: { size: 10, color: '#666' },
      showgrid: true,
      gridcolor: '#e5e5e5',
      gridwidth: 1
    },
    yaxis: {
      showgrid: true,
      gridcolor: '#d3d3d3',
      gridwidth: 1,
      zeroline: true,
      zerolinecolor: '#999',
      zerolinewidth: 2
    }
  }

  const mergedLayout = mergeDeep(defaultLayout, spec.layout || {})

  return {
    data,
    layout: mergedLayout,
    config: { ...(spec.config || {}) }
  }
}

/**
 * Build Line/Scatter Graph Figure
 */
export const buildLineFigure = (rows, encodings = {}, spec = {}, chartType = 'line') => {
  console.log('[buildLineFigure] START', {
    chartType,
    rowsCount: rows?.length,
    encodings,
    spec,
    firstRow: rows?.[0]
  })
  
  const xField = encodings.x?.field || encodings.category?.field
  const yField = encodings.y?.field || encodings.value?.field
  
  console.log('[buildLineFigure] Fields:', { xField, yField })
  
  if (!xField || !yField) {
    console.error('[buildLineFigure] Missing xField or yField!')
    return null
  }

  const seriesField = encodings.series?.field || encodings.group?.field || encodings.color?.field
  const aggregator = encodings.y?.agg || encodings.y?.aggregate || 'identity'
  const seriesMap = splitSeriesPoints(rows, { xField, yField, seriesField })

  console.log('[buildLineFigure] SeriesMap size:', seriesMap.size)
  seriesMap.forEach((points, key) => {
    console.log(`[buildLineFigure] Series "${key}":`, points.length, 'points')
    console.log('[buildLineFigure] First 3 points:', points.slice(0, 3))
  })

  const baseMode = chartType === 'scatter' 
    ? 'markers'
    : (spec.mode || 'lines+markers')
  
  console.log('[buildLineFigure] baseMode:', baseMode, 'chartType:', chartType)
  
  const traces = Array.from(seriesMap.entries()).map(([seriesKey, points]) => {
    const aggregated = aggregatePoints(points, aggregator)
    console.log(`[buildLineFigure] Aggregated "${seriesKey}":`, aggregated.length, 'points')
    console.log('[buildLineFigure] Aggregated first 3:', aggregated.slice(0, 3))
    
    const trace = {
      type: chartType === 'scatter' ? 'scatter' : 'scatter',
      mode: baseMode,
      name: seriesKey,
      x: aggregated.map((point) => point.x),
      y: aggregated.map((point) => point.y)
    }
    
    console.log(`[buildLineFigure] Trace "${seriesKey}":`, {
      xLength: trace.x.length,
      yLength: trace.y.length,
      xSample: trace.x.slice(0, 3),
      ySample: trace.y.slice(0, 3)
    })
    
    return trace
  })
  
  console.log('[buildLineFigure] Total traces:', traces.length)

  // For scatter plots, add regression line by default
  if (chartType === 'scatter') {
    let referenceLines = spec.reference_lines
    
    console.log('[buildLineFigure] Original reference_lines:', referenceLines)
    console.log('[buildLineFigure] reference_lines type:', typeof referenceLines)
    
    if (referenceLines === undefined || 
        referenceLines === null || 
        referenceLines === '' ||
        (typeof referenceLines === 'string' && referenceLines.trim() === '') ||
        (Array.isArray(referenceLines) && referenceLines.length === 0)) {
      console.log('[buildLineFigure] No reference lines provided - using default regression line')
      referenceLines = [
        {
          type: 'regression',
          name: '회귀선',
          color: 'blue',
          width: 2,
          dash: 'solid'
        }
      ]
    } else if (Array.isArray(referenceLines) && referenceLines.length > 0) {
      console.log('[buildLineFigure] Using user-defined reference lines:', referenceLines.length)
    } else {
      console.warn('[buildLineFigure] Unexpected reference_lines format:', referenceLines, '- using default')
      referenceLines = [
        {
          type: 'regression',
          name: '회귀선',
          color: 'blue',
          width: 2,
          dash: 'solid'
        }
      ]
    }

    // Add reference lines for scatter plots
    try {
      referenceLines.forEach((refLine) => {
        if (refLine.type === 'mean' || refLine.type === 'average') {
          const allYValues = []
          traces.forEach(trace => {
            if (trace.y && Array.isArray(trace.y)) {
              allYValues.push(...trace.y.filter(v => typeof v === 'number' && !isNaN(v)))
            }
          })
          
          if (allYValues.length === 0) return
          
          const mean = allYValues.reduce((sum, val) => sum + val, 0) / allYValues.length
          const allXValues = []
          traces.forEach(trace => {
            if (trace.x && Array.isArray(trace.x)) {
              allXValues.push(...trace.x.filter(v => typeof v === 'number' && !isNaN(v)))
            }
          })
          
          if (allXValues.length === 0) return
          
          const xMin = Math.min(...allXValues)
          const xMax = Math.max(...allXValues)
          
          traces.push({
            type: 'scatter',
            mode: 'lines',
            name: refLine.name || 'Mean',
            x: [xMin, xMax],
            y: [mean, mean],
            line: {
              color: refLine.color || 'red',
              width: refLine.width || 2,
              dash: refLine.dash || 'dash'
            },
            showlegend: true
          })
        } else if (refLine.type === 'horizontal') {
          if (typeof refLine.value !== 'number' || isNaN(refLine.value)) return
          
          const allXValues = []
          traces.forEach(trace => {
            if (trace.x && Array.isArray(trace.x)) {
              allXValues.push(...trace.x.filter(v => typeof v === 'number' && !isNaN(v)))
            }
          })
          
          if (allXValues.length === 0) return
          
          const xMin = Math.min(...allXValues)
          const xMax = Math.max(...allXValues)
          
          traces.push({
            type: 'scatter',
            mode: 'lines',
            name: refLine.name || 'Reference',
            x: [xMin, xMax],
            y: [refLine.value, refLine.value],
            line: {
              color: refLine.color || 'red',
              width: refLine.width || 2,
              dash: refLine.dash || 'dash'
            },
            showlegend: true
          })
        } else if (refLine.type === 'regression' || refLine.type === 'linear') {
          // Step 1: Collect all unique X values and build a consistent mapping
          const allXValues = new Set()
          traces.forEach(trace => {
            if (trace.x && Array.isArray(trace.x)) {
              trace.x.forEach(x => allXValues.add(x))
            }
          })
          
          // Check if X is numeric
          const xValuesArray = Array.from(allXValues)
          const isNumericX = xValuesArray.every(x => {
            if (typeof x === 'number') return true
            const parsed = parseFloat(x)
            return !isNaN(parsed)
          })
          
          console.log('[buildLineFigure] X values analysis:', {
            uniqueCount: xValuesArray.length,
            isNumeric: isNumericX,
            sample: xValuesArray.slice(0, 5)
          })
          
          // Step 2: Create consistent X mapping
          let xMapping = new Map()
          if (isNumericX) {
            // For numeric X, map each X value to its numeric representation
            xValuesArray.forEach(x => {
              const numericX = typeof x === 'number' ? x : parseFloat(x)
              xMapping.set(x, numericX)
            })
          } else {
            // For categorical X, use index based on order of appearance
            xValuesArray.forEach((x, idx) => {
              xMapping.set(x, idx)
            })
          }
          
          // Step 3: Collect all points with consistent X mapping
          const allPoints = []
          traces.forEach(trace => {
            if (trace.x && trace.y && Array.isArray(trace.x) && Array.isArray(trace.y)) {
              trace.x.forEach((x, i) => {
                const xVal = xMapping.get(x)
                const yVal = typeof trace.y[i] === 'number' ? trace.y[i] : parseFloat(trace.y[i])
                
                if (xVal !== undefined && !isNaN(yVal) && isFinite(yVal)) {
                  allPoints.push({ x: xVal, y: yVal, originalX: x })
                }
              })
            }
          })
          
          if (allPoints.length < 2) {
            console.warn('[buildLineFigure] Not enough valid points for regression line:', allPoints.length)
            return
          }
          
          console.log('[buildLineFigure] Regression points:', allPoints.length, 'first 5:', allPoints.slice(0, 5))
          
          // Step 4: Calculate linear regression
          const n = allPoints.length
          const sumX = allPoints.reduce((sum, p) => sum + p.x, 0)
          const sumY = allPoints.reduce((sum, p) => sum + p.y, 0)
          const sumXY = allPoints.reduce((sum, p) => sum + p.x * p.y, 0)
          const sumX2 = allPoints.reduce((sum, p) => sum + p.x * p.x, 0)
          
          const denominator = (n * sumX2 - sumX * sumX)
          
          if (Math.abs(denominator) < 1e-10) {
            console.warn('[buildLineFigure] Cannot calculate regression: denominator near zero:', denominator)
            return
          }
          
          const slope = (n * sumXY - sumX * sumY) / denominator
          const intercept = (sumY - slope * sumX) / n
          
          console.log('[buildLineFigure] Regression calculated:', {
            slope,
            intercept,
            n,
            sumX: sumX.toFixed(2),
            sumY: sumY.toFixed(2),
            sumXY: sumXY.toFixed(2),
            sumX2: sumX2.toFixed(2),
            denominator: denominator.toFixed(2)
          })
          
          if (!isFinite(slope) || !isFinite(intercept)) {
            console.warn('[buildLineFigure] Invalid regression values:', { slope, intercept })
            return
          }
          
          // Step 5: Create regression line trace
          const xMin = Math.min(...allPoints.map(p => p.x))
          const xMax = Math.max(...allPoints.map(p => p.x))
          const yMin = slope * xMin + intercept
          const yMax = slope * xMax + intercept
          
          console.log('[buildLineFigure] Regression line:', {
            xMin,
            xMax,
            yMin: yMin.toFixed(2),
            yMax: yMax.toFixed(2),
            isNumericX
          })
          
          // For categorical X, we need to find the original X values at min/max indices
          let regressionX, regressionY
          if (isNumericX) {
            regressionX = [xMin, xMax]
            regressionY = [yMin, yMax]
          } else {
            // Find original X values for min and max indices
            const minPoint = allPoints.find(p => p.x === xMin)
            const maxPoint = allPoints.find(p => p.x === xMax)
            regressionX = [minPoint?.originalX || xMin, maxPoint?.originalX || xMax]
            regressionY = [yMin, yMax]
          }
          
          traces.push({
            type: 'scatter',
            mode: 'lines',
            name: refLine.name || 'Regression',
            x: regressionX,
            y: regressionY,
            line: {
              color: refLine.color || 'blue',
              width: refLine.width || 2,
              dash: refLine.dash || 'solid'
            },
            showlegend: true,
            hoverinfo: 'skip'
          })
        }
      })
    } catch (error) {
      console.error('[buildLineFigure] Error adding reference lines:', error)
    }
  }

  const defaultLayout = {
    height: 500,
    margin: { l: 80, r: 80, t: 100, b: 150, pad: 4 },
    xaxis: {
      tickangle: -45,
      tickfont: { size: 10, color: '#666' },
      showgrid: true,
      gridcolor: '#e5e5e5',
      gridwidth: 1
    },
    yaxis: {
      showgrid: true,
      gridcolor: '#d3d3d3',
      gridwidth: 1,
      griddash: 'dot',
      zeroline: true,
      zerolinecolor: '#999',
      zerolinewidth: 2
    }
  }

  const mergedLayout = mergeDeep(defaultLayout, spec.layout || {})

  return {
    data: traces,
    layout: mergedLayout,
    config: { ...(spec.config || {}) }
  }
}

/**
 * Build Box Plot Figure
 */
export const buildBoxFigure = (rows, encodings = {}, spec = {}) => {
  const valueField = encodings.value?.field || encodings.y?.field
  const categoryField = encodings.category?.field || encodings.x?.field
  const seriesField = encodings.series?.field || encodings.group?.field || encodings.color?.field
  if (!valueField) return null

  const groups = new Map()
  rows.forEach((row) => {
    const bucketKey = seriesField ? getValueByPath(row, seriesField) : getValueByPath(row, categoryField) || 'Series'
    if (!groups.has(bucketKey)) {
      groups.set(bucketKey, [])
    }
    const value = coerceNumber(getValueByPath(row, valueField))
    // Skip null, undefined, NaN, and Infinity values
    if (value !== null && value !== undefined && typeof value === 'number' && isFinite(value)) {
      groups.get(bucketKey).push(value)
    }
  })

  const data = Array.from(groups.entries()).map(([key, values]) => ({
    type: 'box',
    name: key,
    y: values,
    boxpoints: spec.boxpoints || 'outliers'
  }))

  const defaultLayout = {
    height: 500,
    margin: { l: 80, r: 80, t: 100, b: 150, pad: 4 },
    xaxis: {
      tickangle: -45,
      tickfont: { size: 10, color: '#666' },
      showgrid: true,
      gridcolor: '#e5e5e5',
      gridwidth: 1
    },
    yaxis: {
      showgrid: true,
      gridcolor: '#d3d3d3',
      gridwidth: 1,
      zeroline: true,
      zerolinecolor: '#999',
      zerolinewidth: 2
    }
  }

  const mergedLayout = mergeDeep(defaultLayout, spec.layout || {})

  return {
    data,
    layout: mergedLayout,
    config: { ...(spec.config || {}) }
  }
}
