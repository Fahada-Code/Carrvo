import type { ParsedJob, TailoringResult } from '@/lib/types';
import PortalBadge from './PortalBadge';

interface Props {
  job: ParsedJob;
  result: TailoringResult;
  onConfirm: () => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

export default function ConfirmationScreen({
  job,
  result,
  onConfirm,
  onCancel,
  isSubmitting,
}: Props) {
  return (
    <div className="slide-up flex flex-col gap-6">
      {/* Header */}
      <div>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
          Review before submitting
        </p>
        <h2 className="text-xl font-semibold text-[#e2e4eb]">{job.title}</h2>
        <div className="mt-1.5 flex flex-wrap items-center gap-2.5 text-sm text-[#7c8096]">
          <span>{job.company}</span>
          <span className="text-[#252a35]">·</span>
          <span>{job.location}</span>
          <span className="text-[#252a35]">·</span>
          <PortalBadge portal={job.portal} size="sm" />
        </div>
      </div>

      <hr className="border-[#1c1f28]" />

      {/* Resume changes */}
      <div>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
          Resume — what changed
        </p>
        <ul className="flex flex-col gap-2">
          {result.resumeChanges.map((change, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-[#7c8096]">
              <span className="mt-0.5 shrink-0 text-[#22c55e]">–</span>
              <span>{change}</span>
            </li>
          ))}
        </ul>
      </div>

      <hr className="border-[#1c1f28]" />

      {/* Cover letter preview */}
      <div>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
          Cover letter — opening paragraph
        </p>
        <blockquote className="rounded border-l-2 border-[#f59e0b]/40 bg-[#0d0f14] px-4 py-3 font-mono text-sm leading-relaxed text-[#7c8096]">
          {result.coverLetterOpening}
        </blockquote>
      </div>

      <hr className="border-[#1c1f28]" />

      {/* Output paths */}
      <div>
        <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
          Output files
        </p>
        <div className="flex flex-col gap-1">
          <span className="font-mono text-xs text-[#4a4d5e]">{result.resumeFile}</span>
          <span className="font-mono text-xs text-[#4a4d5e]">{result.coverLetterFile}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          onClick={onCancel}
          disabled={isSubmitting}
          className="rounded border border-[#1c1f28] px-4 py-2 text-sm text-[#7c8096] transition-colors hover:border-[#252a35] hover:text-[#e2e4eb] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={isSubmitting}
          className="rounded bg-[#f59e0b] px-5 py-2 text-sm font-medium text-[#07080b] transition-colors hover:bg-[#d97706] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? 'Submitting…' : 'Submit Application →'}
        </button>
      </div>
    </div>
  );
}
