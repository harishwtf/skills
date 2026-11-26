import React from 'react';
import { AbsoluteFill, Img, interpolate, Easing, useCurrentFrame, staticFile } from 'remotion';

const EASE_OUT = Easing.bezier(0.00, 0.00, 0.20, 1.00);
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

export const Conclusion: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], { ...clamp, easing: EASE_OUT });
  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={staticFile('outro.png')}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </AbsoluteFill>
  );
};
