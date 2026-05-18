import axios from 'axios'
import type { HealthResponse, MatrixResponse, Member, Milestone } from '@/types'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

export async function fetchMilestones(): Promise<Milestone[]> {
  const response = await api.get<Milestone[]>('/milestones')
  return response.data
}

export async function fetchCurrentMilestone(): Promise<Milestone | null> {
  const response = await api.get<Milestone | null>('/milestones/current')
  return response.data
}

export async function fetchMatrix(milestoneId?: number | null): Promise<MatrixResponse> {
  const path = milestoneId ? `/matrix/${milestoneId}` : '/matrix'
  const response = await api.get<MatrixResponse>(path)
  return response.data
}

export async function fetchMembers(): Promise<Member[]> {
  const response = await api.get<Member[]>('/members')
  return response.data
}

export async function refreshDashboard(): Promise<void> {
  await api.post('/refresh')
}

