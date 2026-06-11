import React from 'react';
import { interpolate, Easing } from 'remotion';

const EASE_OUT = Easing.bezier(0.00, 0.00, 0.20, 1.00);
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

export const WordReveal: React.FC<{
  text: string;
  startAt: number;
  frame: number;
  color: string;
  fontSize?: number;
  fontWeight?: number;
  lineHeight?: string;
  letterSpacing?: string;
  wordGap?: number;
  wordDuration?: number;
  stagger?: number;
  yDistance?: number;
}> = ({
  text,
  startAt,
  frame,
  color,
  fontSize = 46,
  fontWeight = 700,
  lineHeight = '58px',
  letterSpacing = '-0.02em',
  wordGap = 12,
  wordDuration = 14,
  stagger = 3,
  yDistance = 18,
}) => {
  const words = text.split(' ');
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: `0 ${wordGap}px`,
        fontSize,
        fontWeight,
        color,
        lineHeight,
        letterSpacing,
      }}
    >
      {words.map((word, i) => {
        const wordStart = startAt + i * stagger;
        const f = Math.max(0, frame - wordStart);
        const opacity = interpolate(f, [0, wordDuration], [0, 1], { ...clamp, easing: EASE_OUT });
        const y = interpolate(f, [0, wordDuration], [yDistance, 0], { ...clamp, easing: EASE_OUT });
        return (
          <span key={i} style={{ display: 'inline-block', opacity, transform: `translateY(${y}px)` }}>
            {word}
          </span>
        );
      })}
    </div>
  );
};
