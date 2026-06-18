"use client";

import React, { useState, useEffect } from "react";

interface TypewriterTextProps {
  text: string;
  speed?: number; // ms per character
}

export default function TypewriterText({ text, speed = 15 }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    // Reset state when text changes
    setDisplayedText("");
    setCurrentIndex(0);
  }, [text]);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText((prev) => prev + text.charAt(currentIndex));
        setCurrentIndex((prev) => prev + 1);
      }, speed);
      return () => clearTimeout(timeout);
    }
  }, [text, currentIndex, speed]);

  const isComplete = currentIndex >= text.length;

  return (
    <span className="font-sans text-sm leading-relaxed text-soc-textPrimary">
      {displayedText}
      {!isComplete && (
        <span className="inline-block w-1.5 h-4 ml-1 bg-soc-cyan animate-pulse align-middle" />
      )}
    </span>
  );
}
