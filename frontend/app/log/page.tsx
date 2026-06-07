import ApplicationLog from '@/components/ApplicationLog';
import { MOCK_LOG } from '@/lib/mock-data';
import Link from 'next/link';

export default function LogPage() {
  const total = MOCK_LOG.length;
  const submitted = MOCK_LOG.filter((e) => e.status === 'submitted').length;
  const errors = MOCK_LOG.filter((e) => e.status === 'error').length;

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
            Application history
          </p>
          <h1 className="text-xl font-semibold text-[#e2e4eb]">Log</h1>
        </div>
        <Link
          href="/"
          className="rounded border border-[#1c1f28] px-4 py-2 text-xs text-[#7c8096] transition-colors hover:border-[#252a35] hover:text-[#e2e4eb]"
        >
          + New application
        </Link>
      </div>

      {/* Stats row */}
      <div className="mb-6 flex gap-6">
        <div>
          <p className="font-mono text-2xl font-semibold text-[#e2e4eb]">{total}</p>
          <p className="mt-0.5 text-xs text-[#4a4d5e]">Total</p>
        </div>
        <div className="border-l border-[#1c1f28] pl-6">
          <p className="font-mono text-2xl font-semibold text-[#22c55e]">{submitted}</p>
          <p className="mt-0.5 text-xs text-[#4a4d5e]">Submitted</p>
        </div>
        {errors > 0 && (
          <div className="border-l border-[#1c1f28] pl-6">
            <p className="font-mono text-2xl font-semibold text-[#ef4444]">{errors}</p>
            <p className="mt-0.5 text-xs text-[#4a4d5e]">Errors</p>
          </div>
        )}
      </div>

      {/* Log table */}
      <ApplicationLog entries={MOCK_LOG} />

      {/* Footer note */}
      <p className="mt-4 text-xs text-[#252a35]">
        Data stored locally at <span className="font-mono">~/.carrvo/applications.json</span>
      </p>
    </div>
  );
}
