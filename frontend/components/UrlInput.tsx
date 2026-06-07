'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isValidJobUrl, detectPortal, PORTAL_LABELS } from '@/lib/ats';

export default function UrlInput() {
  const [value, setValue] = useState('');
  const [touched, setTouched] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const isValid = isValidJobUrl(value);
  const portal = value.length > 0 ? detectPortal(value) : null;
  const showError = touched && value.length > 0 && !isValid;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (!isValid) return;
    setIsSubmitting(true);
    router.push(`/apply?url=${encodeURIComponent(value)}`);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleSubmit(e as unknown as React.FormEvent);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl">
      <div
        className={`flex items-center rounded border transition-colors duration-150 ${
          showError
            ? 'border-[#ef4444]/60 bg-[#ef4444]/5'
            : isValid
            ? 'border-[#f59e0b]/40 bg-[#0d0f14]'
            : 'border-[#1c1f28] bg-[#0d0f14] focus-within:border-[#252a35]'
        }`}
      >
        {/* URL scheme prefix */}
        <span className="select-none pl-4 font-mono text-sm text-[#4a4d5e]">↗</span>

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            if (touched) setTouched(false);
          }}
          onBlur={() => setTouched(true)}
          onKeyDown={handleKeyDown}
          placeholder="https://boards.greenhouse.io/company/jobs/..."
          spellCheck={false}
          autoComplete="off"
          className="flex-1 bg-transparent px-3 py-3.5 font-mono text-sm text-[#e2e4eb] placeholder-[#4a4d5e] outline-none"
        />

        <button
          type="submit"
          disabled={isSubmitting || (touched && !isValid)}
          className={`m-1.5 rounded px-4 py-2 text-sm font-medium transition-all duration-150 ${
            isValid && !isSubmitting
              ? 'bg-[#f59e0b] text-[#07080b] hover:bg-[#d97706] cursor-pointer'
              : 'bg-[#1c1f28] text-[#4a4d5e] cursor-not-allowed'
          }`}
        >
          {isSubmitting ? 'Starting…' : 'Start →'}
        </button>
      </div>

      {/* Portal badge / error message */}
      <div className="mt-2.5 h-5 pl-1">
        {showError && (
          <span className="text-xs text-[#ef4444]">
            Enter a valid job listing URL starting with https://
          </span>
        )}
        {!showError && portal && portal !== 'unknown' && (
          <span className="flex items-center gap-1.5 text-xs text-[#7c8096]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e]" />
            {PORTAL_LABELS[portal]} detected
          </span>
        )}
        {!showError && portal === 'unknown' && value.length > 8 && (
          <span className="flex items-center gap-1.5 text-xs text-[#7c8096]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#7c8096]" />
            Portal not identified — will detect on page load
          </span>
        )}
      </div>
    </form>
  );
}
