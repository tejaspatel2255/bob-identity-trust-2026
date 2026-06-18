"use client";

import React, { useEffect, useState } from "react";

interface RiskScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
}

export default function RiskScoreRing({
  score,
  size = 64,
  strokeWidth = 6,
}: RiskScoreRingProps) {
  const [offset, setOffset] = useState(0);
  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    // Animate the stroke-dashoffset on component mount
    const progressOffset = circumference - (score / 100) * circumference;
    const timer = setTimeout(() => {
      setOffset(progressOffset);
    }, 100);
    return () => clearTimeout(timer);
  }, [score, circumference]);

  // Color mapping based on score
  let strokeColor = "#00E5A0"; // Green for safe
  if (score > 65) {
    strokeColor = "#FF3B5C"; // Red for danger
  } else if (score > 30) {
    strokeColor = "#FFB800"; // Amber for warning
  }

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="transparent"
          stroke="#1E2D4A"
          strokeWidth={strokeWidth}
        />
        {/* Animated Progress Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="transparent"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      {/* Centered Score Label */}
      <span className="absolute font-mono text-xs font-bold text-soc-textPrimary">
        {score.toFixed(0)}
      </span>
    </div>
  );
}
