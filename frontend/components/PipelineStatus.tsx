import type { PipelineStep, StepStatus } from '@/lib/types';

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'done') {
    return (
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#22c55e]/15 text-[#22c55e]">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2 5l2.5 2.5L8 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    );
  }
  if (status === 'error') {
    return (
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#ef4444]/15 text-[#ef4444]">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M3 3l4 4M7 3l-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }
  if (status === 'running') {
    return (
      <span className="flex h-5 w-5 items-center justify-center">
        <span className="pulse-ring h-3 w-3 rounded-full bg-[#f59e0b]" />
      </span>
    );
  }
  return (
    <span className="flex h-5 w-5 items-center justify-center">
      <span className="h-2 w-2 rounded-full border border-[#252a35]" />
    </span>
  );
}

function elapsedLabel(ms?: number): string {
  if (!ms) return '';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

interface Props {
  steps: PipelineStep[];
}

export default function PipelineStatus({ steps }: Props) {
  return (
    <div className="flex flex-col divide-y divide-[#1c1f28] rounded border border-[#1c1f28] bg-[#0d0f14]">
      {steps.map((step, i) => {
        const isActive = step.status === 'running' || step.status === 'error';
        return (
          <div
            key={step.id}
            className={`flex items-start gap-4 px-5 py-4 transition-colors duration-200 ${
              isActive ? 'bg-[#111420]' : ''
            }`}
          >
            {/* Step number + icon */}
            <div className="flex flex-col items-center gap-1 pt-0.5">
              <StepIcon status={step.status} />
              {i < steps.length - 1 && (
                <span
                  className={`w-px flex-1 min-h-[16px] ${
                    step.status === 'done' ? 'bg-[#22c55e]/30' : 'bg-[#1c1f28]'
                  }`}
                />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pb-1">
              <div className="flex items-baseline justify-between gap-4">
                <span
                  className={`text-sm font-medium ${
                    step.status === 'pending'
                      ? 'text-[#4a4d5e]'
                      : step.status === 'error'
                      ? 'text-[#ef4444]'
                      : 'text-[#e2e4eb]'
                  }`}
                >
                  {step.label}
                </span>
                {step.status === 'done' && step.elapsedMs !== undefined && (
                  <span className="shrink-0 font-mono text-[11px] text-[#4a4d5e]">
                    {elapsedLabel(step.elapsedMs)}
                  </span>
                )}
                {step.status === 'running' && (
                  <span className="shrink-0 font-mono text-[11px] text-[#f59e0b]">
                    running…
                  </span>
                )}
              </div>

              {step.status !== 'pending' && (
                <p
                  className={`mt-0.5 text-xs ${
                    step.status === 'error' ? 'text-[#ef4444]/70' : 'text-[#7c8096]'
                  }`}
                >
                  {step.errorMessage ?? step.detail ?? step.description}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
