export type AtsPortal = 'greenhouse' | 'workday' | 'lever' | 'ashby' | 'unknown';

export type StepStatus = 'pending' | 'running' | 'done' | 'error';

export type ApplicationStatus = 'submitted' | 'error' | 'pending';

export interface PipelineStep {
  id: string;
  label: string;
  description: string;
  status: StepStatus;
  elapsedMs?: number;
  detail?: string;
  errorMessage?: string;
}

export interface ParsedJob {
  title: string;
  company: string;
  location: string;
  portal: AtsPortal;
  url: string;
  wordCount: number;
}

export interface TailoringResult {
  resumeChanges: string[];
  coverLetterOpening: string;
  resumeFile: string;
  coverLetterFile: string;
}

export interface ApplicationEntry {
  id: string;
  date: string;
  company: string;
  role: string;
  portal: AtsPortal;
  url: string;
  status: ApplicationStatus;
  resumePath: string;
  coverLetterPath: string;
}
