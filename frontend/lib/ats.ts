import type { AtsPortal } from './types';

const PORTAL_PATTERNS: { pattern: RegExp; portal: AtsPortal }[] = [
  { pattern: /greenhouse\.io/i, portal: 'greenhouse' },
  { pattern: /lever\.co/i, portal: 'lever' },
  { pattern: /ashby\.io/i, portal: 'ashby' },
  { pattern: /myworkdayjobs\.com|workday\.com/i, portal: 'workday' },
];

export function detectPortal(url: string): AtsPortal {
  for (const { pattern, portal } of PORTAL_PATTERNS) {
    if (pattern.test(url)) return portal;
  }
  return 'unknown';
}

export const PORTAL_LABELS: Record<AtsPortal, string> = {
  greenhouse: 'Greenhouse',
  lever: 'Lever',
  ashby: 'Ashby',
  workday: 'Workday',
  unknown: 'Unknown ATS',
};

export function isValidJobUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:';
  } catch {
    return false;
  }
}
