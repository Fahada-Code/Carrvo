'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 border-b border-[#1c1f28] bg-[#07080b]/90 backdrop-blur-sm">
      <div className="mx-auto flex h-12 max-w-4xl items-center justify-between px-6">
        <Link
          href="/"
          className="font-mono text-sm font-semibold tracking-widest text-[#e2e4eb] hover:text-[#f59e0b] transition-colors uppercase"
        >
          Carrvo
        </Link>

        <div className="flex items-center gap-6">
          <Link
            href="/log"
            className={`text-xs font-medium transition-colors ${
              pathname === '/log'
                ? 'text-[#e2e4eb]'
                : 'text-[#7c8096] hover:text-[#e2e4eb]'
            }`}
          >
            Log
          </Link>
          <a
            href="https://github.com/Fahadada-code/Carrvo"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-[#7c8096] hover:text-[#e2e4eb] transition-colors"
          >
            GitHub ↗
          </a>
        </div>
      </div>
    </nav>
  );
}
