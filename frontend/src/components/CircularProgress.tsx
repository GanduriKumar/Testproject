import React from 'react'

type Variant = 'primary' | 'success' | 'warning' | 'danger'

export default function CircularProgress({ value, size = 56, strokeWidth = 6, variant = 'primary', showLabel = true }: { value: number, size?: number, strokeWidth?: number, variant?: Variant, showLabel?: boolean }) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)))
  const radius = (size / 2) - strokeWidth
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference
  const colorClass: Record<Variant, string> = {
    primary: 'text-primary',
    success: 'text-success',
    warning: 'text-warning',
    danger: 'text-danger',
  }
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }} aria-label={`Progress ${clamped}%`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          stroke="currentColor"
          className="text-gray-200"
          fill="transparent"
          r={radius}
          cx={size/2}
          cy={size/2}
        />
        <circle
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          stroke="currentColor"
          className={colorClass[variant]}
          fill="transparent"
          r={radius}
          cx={size/2}
          cy={size/2}
          style={{ strokeDasharray: `${circumference} ${circumference}`, strokeDashoffset: offset, transition: 'stroke-dashoffset 0.3s ease' }}
        />
      </svg>
      {showLabel && (
        <span className="absolute text-xs font-medium" aria-hidden>{clamped}%</span>
      )}
    </div>
  )
}
