import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

function getScoreColor(score) {
  if (score >= 7) return '#22c55e'
  if (score >= 4) return '#eab308'
  return '#ef4444'
}

export default function NetworkGraph({ parsedData, members }) {
  const svgRef = useRef(null)
  const tooltipRef = useRef(null)

  useEffect(() => {
    if (!parsedData || !members || members.length === 0) return

    // Build interaction edges: count sequential adjacent messages between different people
    const edgeMap = {}
    for (let i = 0; i < parsedData.length - 1; i++) {
      const a = parsedData[i].name
      const b = parsedData[i + 1].name
      if (a !== b) {
        const key = [a, b].sort().join('|||')
        edgeMap[key] = (edgeMap[key] || 0) + 1
      }
    }

    const nodes = members.map(m => ({
      id: m.name,
      score: m.overall_score ?? 5,
    }))

    const links = Object.entries(edgeMap).map(([key, count]) => {
      const [source, target] = key.split('|||')
      return { source, target, count }
    })

    const maxCount = Math.max(...links.map(l => l.count), 1)

    const container = svgRef.current
    const width = container.clientWidth || 600
    const height = 400

    // Clear previous
    d3.select(container).selectAll('*').remove()

    const svg = d3.select(container)
      .attr('width', width)
      .attr('height', height)

    // Defs for glow filter
    const defs = svg.append('defs')
    const filter = defs.append('filter').attr('id', 'glow')
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur')
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(40))

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#2A2550')
      .attr('stroke-width', d => 1 + (d.count / maxCount) * 5)
      .attr('stroke-opacity', 0.6)

    // Draw nodes
    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x; d.fy = d.y
        })
        .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null; d.fy = null
        })
      )

    node.append('circle')
      .attr('r', d => 16 + (d.score / 10) * 20)
      .attr('fill', d => `${getScoreColor(d.score)}22`)
      .attr('stroke', d => getScoreColor(d.score))
      .attr('stroke-width', 2)
      .attr('filter', 'url(#glow)')

    node.append('text')
      .text(d => d.id.charAt(0).toUpperCase())
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', d => getScoreColor(d.score))
      .attr('font-size', 14)
      .attr('font-weight', 'bold')
      .style('pointer-events', 'none')

    node.append('text')
      .text(d => d.id)
      .attr('text-anchor', 'middle')
      .attr('y', d => 22 + (d.score / 10) * 20)
      .attr('fill', '#9ca3af')
      .attr('font-size', 11)
      .style('pointer-events', 'none')

    // Tooltip
    const tooltip = d3.select(tooltipRef.current)

    node
      .on('mouseover', (event, d) => {
        tooltip
          .style('opacity', 1)
          .style('left', `${event.offsetX + 10}px`)
          .style('top', `${event.offsetY - 10}px`)
          .html(`<strong>${d.id}</strong><br/>Score: ${d.score.toFixed(1)}`)
      })
      .on('mouseout', () => tooltip.style('opacity', 0))

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => simulation.stop()
  }, [parsedData, members])

  return (
    <div className="glass p-5 rounded-2xl animate-fade-in">
      <h3 className="font-heading font-semibold text-accent mb-2">Interaction Network</h3>
      <p className="text-xs text-gray-500 mb-4">Node size = contribution score • Edge thickness = interaction frequency • Drag nodes to explore</p>
      <div className="relative">
        <svg ref={svgRef} className="w-full" style={{ height: 400 }} />
        <div
          ref={tooltipRef}
          className="d3-tooltip"
          style={{ opacity: 0, transition: 'opacity 0.2s' }}
        />
      </div>
    </div>
  )
}
