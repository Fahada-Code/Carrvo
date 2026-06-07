import type { ApplicationEntry, ParsedJob, TailoringResult, PipelineStep } from './types';

export const MOCK_LOG: ApplicationEntry[] = [
  {
    id: '1',
    date: '2026-06-05',
    company: 'Stripe',
    role: 'Senior Backend Engineer',
    portal: 'greenhouse',
    url: 'https://boards.greenhouse.io/stripe/jobs/6123456',
    status: 'submitted',
    resumePath: '~/.carrvo/jobs/stripe_senior-backend-engineer/resume.pdf',
    coverLetterPath: '~/.carrvo/jobs/stripe_senior-backend-engineer/coverletter.pdf',
  },
  {
    id: '2',
    date: '2026-06-03',
    company: 'Vercel',
    role: 'Frontend Infrastructure Engineer',
    portal: 'lever',
    url: 'https://jobs.lever.co/vercel/abc123',
    status: 'submitted',
    resumePath: '~/.carrvo/jobs/vercel_frontend-infrastructure/resume.pdf',
    coverLetterPath: '~/.carrvo/jobs/vercel_frontend-infrastructure/coverletter.pdf',
  },
  {
    id: '3',
    date: '2026-06-01',
    company: 'Anthropic',
    role: 'ML Engineer, Reinforcement Learning',
    portal: 'ashby',
    url: 'https://jobs.ashby.io/anthropic/abc456',
    status: 'error',
    resumePath: '~/.carrvo/jobs/anthropic_ml-engineer-rl/resume.pdf',
    coverLetterPath: '~/.carrvo/jobs/anthropic_ml-engineer-rl/coverletter.pdf',
  },
  {
    id: '4',
    date: '2026-05-29',
    company: 'Linear',
    role: 'Product Engineer',
    portal: 'ashby',
    url: 'https://jobs.ashby.io/linear/def789',
    status: 'submitted',
    resumePath: '~/.carrvo/jobs/linear_product-engineer/resume.pdf',
    coverLetterPath: '~/.carrvo/jobs/linear_product-engineer/coverletter.pdf',
  },
  {
    id: '5',
    date: '2026-05-27',
    company: 'Figma',
    role: 'Senior Software Engineer, Editor',
    portal: 'greenhouse',
    url: 'https://boards.greenhouse.io/figma/jobs/7654321',
    status: 'submitted',
    resumePath: '~/.carrvo/jobs/figma_sr-swe-editor/resume.pdf',
    coverLetterPath: '~/.carrvo/jobs/figma_sr-swe-editor/coverletter.pdf',
  },
];

export function getMockParsedJob(url: string): ParsedJob {
  const portal =
    url.includes('greenhouse.io') ? 'greenhouse' :
    url.includes('lever.co') ? 'lever' :
    url.includes('ashby.io') ? 'ashby' :
    url.includes('myworkdayjobs.com') || url.includes('workday') ? 'workday' :
    'unknown';

  return {
    title: 'Senior Software Engineer',
    company: 'Acme Corp',
    location: 'San Francisco, CA',
    portal,
    url,
    wordCount: 1247,
  };
}

export function getMockTailoringResult(): TailoringResult {
  return {
    resumeChanges: [
      'Reordered 3 bullet points in Work Experience to lead with impact',
      'Added keywords: distributed systems, gRPC, observability',
      'Updated professional summary to highlight infrastructure focus',
    ],
    coverLetterOpening:
      "Acme Corp's obsession with developer experience is what drew me to this role — and my three years shipping payment infrastructure gave me a front-row seat to exactly the kind of latency and reliability problems your team is solving. I've spent the last year reducing p99 API response times by 40% through a combination of query optimization and strategic caching, and I'm excited to bring that mindset to Acme.",
    resumeFile: '~/.carrvo/jobs/acme-corp_senior-swe/resume.pdf',
    coverLetterFile: '~/.carrvo/jobs/acme-corp_senior-swe/coverletter.pdf',
  };
}

export function getInitialSteps(): PipelineStep[] {
  return [
    {
      id: 'scrape',
      label: 'Scraping job description',
      description: 'Fetching and parsing the full job listing',
      status: 'pending',
    },
    {
      id: 'resume',
      label: 'Tailoring your resume',
      description: 'Analyzing keywords and rewriting bullet points',
      status: 'pending',
    },
    {
      id: 'cover',
      label: 'Writing cover letter',
      description: 'Generating a role-specific, human-sounding cover letter',
      status: 'pending',
    },
    {
      id: 'compile',
      label: 'Compiling PDFs',
      description: 'Running LaTeX to produce final documents',
      status: 'pending',
    },
    {
      id: 'submit',
      label: 'Submitting application',
      description: 'Filling the ATS form and uploading documents',
      status: 'pending',
    },
  ];
}
