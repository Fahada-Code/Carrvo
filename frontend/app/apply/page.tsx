import { Suspense } from 'react';
import ApplyFlow from './ApplyFlow';

function Loading() {
  return (
    <div className="flex min-h-full items-center justify-center">
      <span className="font-mono text-sm text-[#4a4d5e]">Loading…</span>
    </div>
  );
}

export default function ApplyPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ApplyFlow />
    </Suspense>
  );
}
