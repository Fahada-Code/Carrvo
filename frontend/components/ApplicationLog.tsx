import type { ApplicationEntry, ApplicationStatus } from '@/lib/types';
import PortalBadge from './PortalBadge';

function StatusBadge({ status }: { status: ApplicationStatus }) {
  const styles: Record<ApplicationStatus, string> = {
    submitted: 'text-[#22c55e] bg-[#22c55e]/10 border-[#22c55e]/20',
    error:     'text-[#ef4444] bg-[#ef4444]/10 border-[#ef4444]/20',
    pending:   'text-[#f59e0b] bg-[#f59e0b]/10 border-[#f59e0b]/20',
  };
  const labels: Record<ApplicationStatus, string> = {
    submitted: '● Submitted',
    error:     '✗ Error',
    pending:   '○ Pending',
  };
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 font-mono text-[11px] font-medium ${styles[status]}`}
    >
      {labels[status]}
    </span>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

interface Props {
  entries: ApplicationEntry[];
}

export default function ApplicationLog({ entries }: Props) {
  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded border border-[#1c1f28] bg-[#0d0f14] px-8 py-20 text-center">
        <p className="font-mono text-sm text-[#4a4d5e]">No applications yet.</p>
        <p className="mt-1 text-xs text-[#252a35]">
          Paste a job link on the home page to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded border border-[#1c1f28]">
      {/* Table header */}
      <div className="grid grid-cols-[140px_1fr_120px_140px_80px] gap-4 border-b border-[#1c1f28] bg-[#0d0f14] px-5 py-3">
        {['Date', 'Role', 'Portal', 'Status', ''].map((col) => (
          <span key={col} className="font-mono text-[11px] uppercase tracking-wider text-[#4a4d5e]">
            {col}
          </span>
        ))}
      </div>

      {/* Rows */}
      <div className="flex flex-col divide-y divide-[#1c1f28] bg-[#0d0f14]">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="group grid grid-cols-[140px_1fr_120px_140px_80px] items-center gap-4 px-5 py-3.5 transition-colors hover:bg-[#111420]"
          >
            {/* Date */}
            <span className="font-mono text-xs text-[#4a4d5e]">
              {formatDate(entry.date)}
            </span>

            {/* Company + Role */}
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-[#e2e4eb]">{entry.role}</p>
              <p className="truncate text-xs text-[#7c8096]">{entry.company}</p>
            </div>

            {/* Portal */}
            <PortalBadge portal={entry.portal} />

            {/* Status */}
            <StatusBadge status={entry.status} />

            {/* Action */}
            <a
              href={entry.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-right text-xs text-[#4a4d5e] transition-colors hover:text-[#f59e0b]"
            >
              View ↗
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
