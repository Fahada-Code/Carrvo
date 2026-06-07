import type { AtsPortal } from '@/lib/types';
import { PORTAL_LABELS } from '@/lib/ats';

const COLORS: Record<AtsPortal, string> = {
  greenhouse: 'text-[#22c55e] bg-[#22c55e]/10 border-[#22c55e]/20',
  lever:      'text-[#3b82f6] bg-[#3b82f6]/10 border-[#3b82f6]/20',
  ashby:      'text-[#a855f7] bg-[#a855f7]/10 border-[#a855f7]/20',
  workday:    'text-[#f59e0b] bg-[#f59e0b]/10 border-[#f59e0b]/20',
  unknown:    'text-[#7c8096] bg-[#7c8096]/10 border-[#7c8096]/20',
};

interface Props {
  portal: AtsPortal;
  size?: 'sm' | 'md';
}

export default function PortalBadge({ portal, size = 'sm' }: Props) {
  const padding = size === 'md' ? 'px-2.5 py-1 text-xs' : 'px-2 py-0.5 text-[11px]';
  return (
    <span
      className={`inline-flex items-center rounded border font-mono font-medium ${padding} ${COLORS[portal]}`}
    >
      {PORTAL_LABELS[portal]}
    </span>
  );
}
