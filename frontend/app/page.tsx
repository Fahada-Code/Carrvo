import UrlInput from '@/components/UrlInput';
import { MOCK_LOG } from '@/lib/mock-data';
import PortalBadge from '@/components/PortalBadge';
import Link from 'next/link';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export default function HomePage() {
  const recent = MOCK_LOG.slice(0, 3);

  return (
    <div className="dot-grid flex min-h-full flex-col">
      {/* Hero */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-20">
        <div className="w-full max-w-2xl">
          {/* Kicker */}
          <p className="mb-6 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
            Open-core · Apache 2.0
          </p>

          {/* Headline */}
          <h1 className="mb-4 text-4xl font-semibold leading-tight tracking-tight text-[#e2e4eb] sm:text-5xl">
            Tailored applications.
            <br />
            <span className="text-[#f59e0b]">Not bulk blasts.</span>
          </h1>

          <p className="mb-10 max-w-lg text-base leading-relaxed text-[#7c8096]">
            Paste a job listing URL. Carrvo scrapes the description, tailors your resume
            and cover letter with AI, compiles both to PDF, and submits your application
            through the ATS portal — in minutes.
          </p>

          {/* URL input */}
          <UrlInput />

          {/* Supported portals */}
          <div className="mt-8 flex flex-wrap items-center gap-2">
            <span className="text-xs text-[#4a4d5e]">Supports:</span>
            {(['greenhouse', 'workday', 'lever', 'ashby'] as const).map((p) => (
              <PortalBadge key={p} portal={p} />
            ))}
          </div>
        </div>
      </div>

      {/* Recent applications strip */}
      {recent.length > 0 && (
        <div className="border-t border-[#1c1f28] bg-[#0d0f14]/60 px-6 py-5">
          <div className="mx-auto max-w-2xl">
            <div className="mb-3 flex items-center justify-between">
              <span className="font-mono text-[11px] uppercase tracking-wider text-[#4a4d5e]">
                Recent applications
              </span>
              <Link
                href="/log"
                className="text-xs text-[#4a4d5e] transition-colors hover:text-[#f59e0b]"
              >
                View all →
              </Link>
            </div>
            <div className="flex flex-col divide-y divide-[#1c1f28]">
              {recent.map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center justify-between py-2.5"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[11px] text-[#4a4d5e]">
                      {formatDate(entry.date)}
                    </span>
                    <span className="text-sm text-[#7c8096]">{entry.company}</span>
                    <span className="hidden text-xs text-[#4a4d5e] sm:block">
                      {entry.role}
                    </span>
                  </div>
                  <span
                    className={`font-mono text-[11px] ${
                      entry.status === 'submitted'
                        ? 'text-[#22c55e]'
                        : entry.status === 'error'
                        ? 'text-[#ef4444]'
                        : 'text-[#f59e0b]'
                    }`}
                  >
                    {entry.status === 'submitted'
                      ? '● submitted'
                      : entry.status === 'error'
                      ? '✗ error'
                      : '○ pending'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
