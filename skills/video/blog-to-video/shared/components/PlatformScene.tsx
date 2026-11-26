import React from 'react';
import { AbsoluteFill, interpolate, Easing } from 'remotion';
import { COLORS, GRADIENTS, RADIUS, SHADOWS } from '../tokens';
import { fontFamily } from '../fonts';
import { FadeIn } from './FadeIn';

const EASE_OUT = Easing.bezier(0.00, 0.00, 0.20, 1.00);
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

function fadeIn(frame: number, start: number, dur = 20) {
  const f = Math.max(0, frame - start);
  return {
    opacity: interpolate(f, [0, dur], [0, 1], { ...clamp, easing: EASE_OUT }),
    y: interpolate(f, [0, dur], [24, 0], { ...clamp, easing: EASE_OUT }),
    scale: interpolate(f, [0, dur], [0.97, 1], { ...clamp, easing: EASE_OUT }),
  };
}

export interface PlatformBeat {
  NAME_IN: number;
  STRENGTH1_IN: number;
  STRENGTH2_IN?: number;
  STRENGTH3_IN?: number;
  GAP_IN?: number;
  PRICING_IN: number;
  G2_IN: number;
}

interface PlatformSceneProps {
  frame: number;
  number: string;
  name: string;
  subName?: string;
  bestFor: string;
  strengths: string[];
  limitation?: string;
  pricing: string;
  g2?: string;
  beats: PlatformBeat;
}

export const PlatformScene: React.FC<PlatformSceneProps> = ({
  frame,
  number,
  name,
  subName,
  bestFor,
  strengths,
  limitation,
  pricing,
  g2,
  beats,
}) => {
  const nameReveal = fadeIn(frame, beats.NAME_IN, 18);
  const bestForReveal = fadeIn(frame, beats.NAME_IN + 30, 16);
  const s1Reveal = fadeIn(frame, beats.STRENGTH1_IN, 20);
  const s2Reveal = beats.STRENGTH2_IN ? fadeIn(frame, beats.STRENGTH2_IN, 20) : null;
  const s3Reveal = beats.STRENGTH3_IN ? fadeIn(frame, beats.STRENGTH3_IN, 20) : null;
  const gapReveal = beats.GAP_IN ? fadeIn(frame, beats.GAP_IN, 20) : null;
  const pricingReveal = fadeIn(frame, beats.PRICING_IN, 18);
  const g2Reveal = fadeIn(frame, beats.G2_IN, 18);

  const dividerF = Math.max(0, frame - (beats.NAME_IN + 45));
  const dividerWidth = interpolate(dividerF, [0, 30], [0, 1], { ...clamp, easing: EASE_OUT });

  const bgOpacity = interpolate(Math.max(0, frame), [0, 20], [0, 1], { ...clamp, easing: EASE_OUT });

  const strengthItems = strengths.map((text, i) => {
    const reveals = [s1Reveal, s2Reveal, s3Reveal];
    const r = reveals[i];
    if (!r) return null;
    return (
      <div
        key={i}
        style={{
          opacity: r.opacity,
          transform: `translateY(${r.y}px)`,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 16,
          padding: '18px 24px',
          background: COLORS.SURFACE,
          borderRadius: RADIUS.LG,
          border: `1px solid ${COLORS.BORDER_SOFT}`,
          boxShadow: SHADOWS.CARD,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: GRADIENTS.BRAND,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            marginTop: 1,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2.5 7L5.5 10L11.5 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <span
          style={{
            fontSize: 22,
            fontWeight: 500,
            color: COLORS.BODY,
            fontFamily,
            lineHeight: '30px',
          }}
        >
          {text}
        </span>
      </div>
    );
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG, fontFamily, opacity: bgOpacity }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: GRADIENTS.BG_RADIAL,
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          padding: '72px 100px 64px',
          gap: 0,
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 32, marginBottom: 10 }}>
          <div
            style={{
              fontSize: 96,
              fontWeight: 800,
              lineHeight: '1',
              background: GRADIENTS.BRAND,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              opacity: nameReveal.opacity,
              transform: `translateY(${nameReveal.y}px)`,
              flexShrink: 0,
              letterSpacing: '-0.04em',
              filter: `drop-shadow(0 0 20px rgba(132,61,245,0.4))`,
            }}
          >
            {number}
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              opacity: nameReveal.opacity,
              transform: `translateY(${nameReveal.y}px)`,
              paddingBottom: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}>
              <span
                style={{
                  fontSize: 56,
                  fontWeight: 800,
                  color: COLORS.HEADING,
                  letterSpacing: '-0.02em',
                  lineHeight: '1',
                }}
              >
                {name}
              </span>
              {subName && (
                <span
                  style={{
                    fontSize: 28,
                    fontWeight: 600,
                    color: COLORS.MUTED,
                    letterSpacing: '-0.01em',
                  }}
                >
                  / {subName}
                </span>
              )}
            </div>

            <div
              style={{
                opacity: bestForReveal.opacity,
                transform: `translateY(${bestForReveal.y}px)`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: COLORS.MUTED,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}
              >
                Best for
              </span>
              <span style={{ fontSize: 13, color: COLORS.MUTED }}>·</span>
              <span
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: COLORS.PRIMARY,
                  background: 'rgba(132,61,245,0.12)',
                  padding: '3px 12px',
                  borderRadius: RADIUS.PILL,
                  border: `1px solid rgba(132,61,245,0.25)`,
                }}
              >
                {bestFor}
              </span>
            </div>
          </div>

          <div style={{ flex: 1 }} />

          {g2 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
                gap: 8,
                opacity: g2Reveal.opacity,
                transform: `translateY(${g2Reveal.y}px)`,
                paddingBottom: 8,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  background: 'rgba(92,22,204,0.08)',
                  border: `1px solid ${COLORS.BORDER}`,
                  borderRadius: RADIUS.PILL,
                  padding: '5px 14px',
                }}
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill={COLORS.PRIMARY}>
                  <path d="M7 1l1.8 3.6L13 5.3l-3 2.9.7 4.1L7 10.4l-3.7 1.9.7-4.1-3-2.9 4.2-.7z" />
                </svg>
                <span style={{ fontSize: 16, fontWeight: 700, color: COLORS.PRIMARY, fontFamily }}>
                  {g2}
                </span>
                <span style={{ fontSize: 13, color: COLORS.MUTED, fontFamily }}>G2</span>
              </div>
              <div
                style={{
                  opacity: pricingReveal.opacity,
                  transform: `translateY(${pricingReveal.y}px)`,
                  fontSize: 15,
                  fontWeight: 600,
                  color: COLORS.MUTED,
                  fontFamily,
                }}
              >
                {pricing}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: GRADIENTS.BRAND,
            transformOrigin: 'left',
            transform: `scaleX(${dividerWidth})`,
            borderRadius: 1,
            marginBottom: 36,
          }}
        />

        {/* Content Grid */}
        <div style={{ display: 'flex', gap: 32, flex: 1 }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <span
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: COLORS.MUTED,
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                opacity: s1Reveal.opacity,
              }}
            >
              Key strengths
            </span>
            {strengthItems}
          </div>

          <div style={{ width: 440, display: 'flex', flexDirection: 'column', gap: 16 }}>
            {limitation && beats.GAP_IN && gapReveal && (
              <FadeIn frame={frame} startAt={beats.GAP_IN} duration={20} yDistance={20}>
                <div
                  style={{
                    padding: '20px 24px',
                    background: COLORS.BG_SOFT,
                    border: `1px solid ${COLORS.BORDER_SOFT}`,
                    borderRadius: RADIUS.LG,
                    display: 'flex',
                    gap: 14,
                    alignItems: 'flex-start',
                  }}
                >
                  <span style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>⚠</span>
                  <div>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 700,
                        color: COLORS.PRIMARY_DARK,
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                        marginBottom: 6,
                        fontFamily,
                      }}
                    >
                      Watch out
                    </div>
                    <div
                      style={{
                        fontSize: 20,
                        fontWeight: 500,
                        color: COLORS.BODY,
                        lineHeight: '28px',
                        fontFamily,
                      }}
                    >
                      {limitation}
                    </div>
                  </div>
                </div>
              </FadeIn>
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
