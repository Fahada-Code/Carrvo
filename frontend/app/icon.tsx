import { ImageResponse } from 'next/og';

export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    <div
      style={{
        background: '#07080b',
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'monospace',
        fontSize: 18,
        fontWeight: 700,
        color: '#f59e0b',
        letterSpacing: '-1px',
      }}
    >
      C
    </div>,
    { ...size }
  );
}
