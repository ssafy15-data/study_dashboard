export interface Milestone {
  id: number
  number: number
  title: string
  due_on: string | null
  state: string
  is_overdue: boolean
  days_left: number | null
  total_issues: number
  closed_issues: number
}

export interface Problem {
  issue_number: number
  title: string
  platform: string
  platform_number: string
  difficulty: string
  url: string
}

export interface CellStatus {
  status: 'merged' | 'open_pr' | 'not_submitted'
  pr_number?: number | null
  pr_url?: string | null
}

export interface MatrixResponse {
  milestone: Milestone
  problems: Problem[]
  members: string[]
  matrix: Record<string, Record<string, CellStatus>>
  summary: {
    total_submissions: number
    total_possible: number
    submission_rate: number
    missing_members: number
    total_members: number
  }
  last_refresh: string | null
}

export interface Member {
  github_id: string
  avatar_url: string | null
  total_solved: number
  total_possible: number
  attendance_rate: number
}

export interface HealthResponse {
  status: 'ok'
  last_refresh: string | null
}

