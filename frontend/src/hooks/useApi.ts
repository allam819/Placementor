import { useQuery } from '@tanstack/react-query'
import { fetchApi } from '../lib/api'

export const useProfile = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => fetchApi('/profiles/'),
  })
}

export const usePreparationProfile = () => {
  return useQuery({
    queryKey: ['profile', 'preparation'],
    queryFn: () => fetchApi('/profiles/preparation'),
  })
}

export const useRecentLearning = () => {
  return useQuery({
    queryKey: ['learning', 'recent'],
    queryFn: () => fetchApi('/learning/recent'),
  })
}

export const useGoals = () => {
  return useQuery({
    queryKey: ['goals'],
    queryFn: () => fetchApi('/goals/'),
  })
}

export const useInterviews = () => {
  return useQuery({
    queryKey: ['interviews'],
    queryFn: () => fetchApi('/interviews'),
  })
}
