import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface SpinnerProps {
  className?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

export function Spinner({ className, size = 'md' }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  }
  
  return (
    <Loader2 className={cn("animate-spin text-blue-600", sizeClasses[size], className)} />
  )
}

export function FullPageLoader() {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center p-8">
      <Spinner size="lg" />
      <p className="mt-4 text-sm text-gray-500 animate-pulse">Loading...</p>
    </div>
  )
}
