import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center px-6 py-20 text-center">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-[#4a4d5e]">
        404
      </p>
      <h1 className="mb-2 text-xl font-semibold text-[#e2e4eb]">Page not found</h1>
      <p className="mb-6 text-sm text-[#7c8096]">
        This page doesn&apos;t exist.
      </p>
      <Link
        href="/"
        className="rounded border border-[#1c1f28] px-4 py-2 text-sm text-[#7c8096] transition-colors hover:border-[#252a35] hover:text-[#e2e4eb]"
      >
        ← Back to home
      </Link>
    </div>
  );
}
