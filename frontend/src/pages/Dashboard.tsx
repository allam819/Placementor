import { usePreparationProfile } from '../hooks/useApi'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { EmptyState } from '../components/ui/empty-state'
import { FullPageLoader } from '../components/ui/spinner'
import { 
  Briefcase, 
  Target, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ArrowRight,
  BookOpen,
  Code2
} from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: prepProfile, isLoading, isError } = usePreparationProfile()

  if (isLoading) return <FullPageLoader />
  
  if (isError) {
    return (
      <div className="flex h-full items-center justify-center">
        <EmptyState 
          icon={AlertCircle} 
          title="Something went wrong" 
          description="We couldn't load your preparation profile." 
          action={<Button onClick={() => window.location.reload()}>Retry</Button>}
        />
      </div>
    )
  }

  const resume = prepProfile?.resume
  const interview = prepProfile?.interview
  const learning = prepProfile?.learning
  const preparation = prepProfile?.preparation
  
  const targetRole = prepProfile?.target_role || 'Not set'
  
  // Greeting logic
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  // Determine priority action
  const topAction = preparation?.next_recommended_actions?.[0]

  return (
    <div className="space-y-8 pb-10">
      
      {/* Header Section */}
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">{greeting}</h1>
        <p className="text-gray-500">
          Preparing for <span className="font-semibold text-gray-900">{targetRole}</span>
        </p>
      </section>

      {/* Top Action Section */}
      {topAction && (
        <section>
          <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-6 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1.5 h-full bg-blue-600"></div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">Your Next Best Action</p>
                <h3 className="text-xl font-semibold text-gray-900 mb-1">
                  {topAction.action?.replace('_', ' ')}: {topAction.topic}
                </h3>
                <p className="text-sm text-gray-600 max-w-2xl">
                  {topAction.source === 'MULTIPLE' 
                    ? 'This is a high-priority gap identified in both your resume and recent interviews.'
                    : topAction.reason || `Identified from your ${topAction.source.toLowerCase()}`}
                </p>
              </div>
              <div className="shrink-0">
                <Button size="lg" className="shadow-sm" onClick={() => navigate(topAction.link || '/interview')}>
                  Take Action <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Metrics Row */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Resume Match</p>
                <p className="text-3xl font-bold text-gray-900">
                  {resume?.latest_resume_score ? `${resume.latest_resume_score}%` : '--'}
                </p>
              </div>
              <div className="p-2 bg-blue-50 rounded-lg">
                <Briefcase className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            {resume && (
              <div className="mt-4 flex items-center text-sm text-gray-600">
                <span className="font-medium text-red-600 mr-1">{resume.major_resume_gaps?.length || 0}</span> gaps identified
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Interview Average</p>
                <p className="text-3xl font-bold text-gray-900">
                  {interview?.average_interview_score ? `${interview.average_interview_score}/100` : '--'}
                </p>
              </div>
              <div className="p-2 bg-emerald-50 rounded-lg">
                <Target className="h-5 w-5 text-emerald-600" />
              </div>
            </div>
            {interview && interview.total_completed_interviews > 0 && (
              <div className="mt-4 flex items-center text-sm text-gray-600">
                Across <span className="font-medium mx-1">{interview.total_completed_interviews}</span> completed interviews
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Learning Streak</p>
                <p className="text-3xl font-bold text-gray-900">
                  {learning?.total_learning_activities || 0}
                </p>
              </div>
              <div className="p-2 bg-purple-50 rounded-lg">
                <TrendingUp className="h-5 w-5 text-purple-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-gray-600">
              Total concepts logged
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: Gaps & Weaknesses */}
        <div className="space-y-8">
          {/* Preparation Gaps */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Current Gaps</h3>
              {resume && <Link to="/resume" className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center">View Resume <ArrowRight className="ml-1 h-3 w-3"/></Link>}
            </div>
            
            {resume?.major_resume_gaps && resume.major_resume_gaps.length > 0 ? (
              <Card>
                <div className="divide-y divide-gray-100">
                  {resume.major_resume_gaps.slice(0, 4).map((gap: string, i: number) => (
                    <div key={i} className="p-4 flex gap-3">
                      <AlertCircle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{gap}</p>
                        <p className="text-xs text-gray-500 mt-1">Missing from resume</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ) : (
              <Card>
                <EmptyState 
                  icon={CheckCircle2}
                  title="No major gaps"
                  description="Your resume currently satisfies the target requirements."
                />
              </Card>
            )}
          </section>

          {/* Recurring Weaknesses */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recurring Weaknesses</h3>
              {interview?.total_completed_interviews > 0 && <Link to="/interview" className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center">View History <ArrowRight className="ml-1 h-3 w-3"/></Link>}
            </div>
            
            {interview?.interview_weaknesses && interview.interview_weaknesses.length > 0 ? (
              <Card>
                <div className="divide-y divide-gray-100">
                  {interview.interview_weaknesses.slice(0, 4).map((w: any, i: number) => (
                    <div key={i} className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{w.topic}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {w.occurrences} {w.occurrences === 1 ? 'occurrence' : 'occurrences'}
                        </p>
                      </div>
                      <Badge variant={w.severity === 'HIGH' ? 'destructive' : w.severity === 'MEDIUM' ? 'warning' : 'secondary'}>
                        {w.severity}
                      </Badge>
                    </div>
                  ))}
                </div>
              </Card>
            ) : (
              <Card>
                <EmptyState 
                  icon={CheckCircle2}
                  title="No weaknesses found"
                  description="Complete an interview to identify areas for improvement."
                  action={<Button variant="outline" size="sm" className="mt-2" onClick={() => navigate('/interview')}>Start Interview</Button>}
                />
              </Card>
            )}
          </section>
        </div>

        {/* Right Column: Recommendations & Learning */}
        <div className="space-y-8">
          
          {/* Actionable Recommendations */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
            </div>
            
            {preparation?.next_recommended_actions && preparation.next_recommended_actions.length > 1 ? (
              <div className="space-y-3">
                {preparation.next_recommended_actions.slice(1, 4).map((action: any, i: number) => (
                  <Card key={i}>
                    <div className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="bg-gray-50 text-[10px] uppercase tracking-wider">{action.action?.replace('_', ' ')}</Badge>
                          <span className="text-sm font-semibold text-gray-900">{action.topic}</span>
                        </div>
                        <Badge variant={action.priority === 'HIGH' ? 'destructive' : action.priority === 'MEDIUM' ? 'warning' : 'secondary'} className="text-[10px]">
                          {action.priority}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2 mt-2">
                        {action.reason || `Identified from ${action.source.toLowerCase()}`}
                      </p>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <EmptyState 
                  icon={Target}
                  title="You're all caught up"
                  description="No pending recommendations at this time."
                />
              </Card>
            )}
          </section>

          {/* Recent Learning */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recent Learning</h3>
              {learning?.recently_learned && learning.recently_learned.length > 0 && <Link to="/learning" className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center">View Library <ArrowRight className="ml-1 h-3 w-3"/></Link>}
            </div>
            
            {learning?.recently_learned && learning.recently_learned.length > 0 ? (
              <Card>
                <div className="divide-y divide-gray-100">
                  {learning.recently_learned.slice(0, 4).map((activity: any) => (
                    <div key={activity.id} className="p-4 flex gap-4">
                      <div className="mt-0.5 rounded-full bg-blue-50 p-2 text-blue-600 shrink-0">
                        <BookOpen className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{activity.topic}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Clock className="h-3 w-3 text-gray-400" />
                          <p className="text-xs text-gray-500">
                            {new Date(activity.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                          </p>
                          <span className="text-gray-300">&bull;</span>
                          <span className="text-xs text-gray-500 capitalize">{activity.activity_type?.replace('_', ' ') || 'Learning'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ) : (
              <Card>
                <EmptyState 
                  icon={BookOpen}
                  title="No learning recorded"
                  description="Log what you learn to improve your recommendations."
                  action={<Button variant="outline" size="sm" className="mt-2" onClick={() => navigate('/learning')}>Add Learning</Button>}
                />
              </Card>
            )}
          </section>

        </div>
      </div>
    </div>
  )
}
