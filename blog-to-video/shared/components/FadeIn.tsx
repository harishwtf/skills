import React from 'react';
import { interpolate, Easing } from 'remotion';

const EASE_OUT = Easing.bezier(0.00, 0.00, 0.20, 1.00);
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

export const FadeIn: React.FC<{
  frame: number;
  startAt: number;
  duration?: number;
  yDistance?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ frame, startAt, duration = 20, yDistance = 20, children, style }) => {
  const f = Math.max(0, frame - startAt);
  const opacity = interpolate(f, [0, duration], [0, 1], { ...clamp, easing: EASE_OUT });
  const y = interpolate(f, [0, duration], [yDistance, 0], { ...clamp, easing: EASE_OUT });
  return (
    <div style={{ opacity, transform: `translateY(${y}px)`, ...style }}>
      {children}
    </div>
  );
};
