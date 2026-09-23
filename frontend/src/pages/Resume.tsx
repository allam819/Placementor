import { useState, useRef } from 'react'
import { supabase } from '../lib/supabase'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { FileText, Upload, Target, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Resume() {
  const [file, setFile] = useState<File | null>(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [resumeId, setResumeId] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const jdFileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected && selected.type === 'application/pdf') {
      setFile(selected)
    } else if (selected) {
      alert('Please upload a PDF file.')
    }
  }

  const handleUpload = async () => {
    if (!file) return alert('Select a PDF first')

    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return setLoading(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('http://127.0.0.1:8000/api/resume/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` },
        body: formData
      })
      if (res.ok) {
        const data = await res.json()
        setResumeId(data.id)
      } else {
        alert('Failed to upload: ' + await res.text())
      }
    } catch (err) {
      alert('Error uploading resume')
    }
    setLoading(false)
  }

  const handleAnalyze = async () => {
    if (!resumeId || !jd) return alert('Please upload a resume and paste a JD first')

    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return setLoading(false)

    try {
      const res = await fetch('http://127.0.0.1:8000/api/resume/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ resume_id: resumeId, job_description_raw: jd })
      })
      if (res.ok) {
        const data = await res.json()
        setAnalysis(data.analysis)
      } else {
        alert('Analysis failed: ' + await res.text())
      }
    } catch (err) {
      alert('Error analyzing resume')
    }
    setLoading(false)
  }

  const handleJdUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return setLoading(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('http://127.0.0.1:8000/api/resume/parse-jd-pdf', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` },
        body: formData
      })
      if (res.ok) {
        const data = await res.json()
        if (!data.text || data.text.trim() === '') {
          alert('Could not extract any text from this PDF. It might be a scanned image rather than a text document.')
        } else {
          setJd(data.text)
        }
      } else {
        alert('Failed to parse JD PDF: ' + await res.text())
      }
    } catch (err) {
      alert('Error parsing JD PDF')
    }
    e.target.value = ''
    setLoading(false)
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Resume Analysis</h1>
        <p className="text-gray-500">Upload your PDF resume and target job description to identify specific preparation gaps.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Step 1: Resume */}
        <Card className={cn("transition-colors", resumeId ? "border-emerald-200 bg-emerald-50/30" : "")}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-sm font-bold">1</span>
              Your Resume
              {resumeId && <CheckCircle2 className="h-5 w-5 text-emerald-600 ml-auto" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!resumeId ? (
              <>
                <input 
                  type="file" 
                  accept=".pdf" 
                  ref={fileInputRef}
                  className="hidden"
                  onChange={handleFileSelect}
                />
                
                {!file ? (
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors group"
                  >
                    <FileText className="h-8 w-8 text-gray-400 mx-auto mb-3 group-hover:text-blue-500" />
                    <p className="text-sm font-medium text-gray-900 mb-1">Click to upload resume</p>
                    <p className="text-xs text-gray-500">PDF documents only</p>
                  </div>
                ) : (
                  <div className="border border-gray-200 rounded-lg p-4 flex items-center justify-between bg-gray-50">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <FileText className="h-5 w-5 text-blue-600 shrink-0" />
                      <span className="text-sm font-medium text-gray-900 truncate">{file.name}</span>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setFile(null)} className="shrink-0 text-gray-500">Change</Button>
                  </div>
                )}

                <Button 
                  className="w-full" 
                  disabled={!file || loading} 
                  onClick={handleUpload}
                  isLoading={loading}
                >
                  <Upload className="mr-2 h-4 w-4" /> Upload & Parse
                </Button>
              </>
            ) : (
              <div className="text-sm text-emerald-700 font-medium flex items-center gap-2 bg-emerald-100/50 p-3 rounded-lg border border-emerald-200">
                <FileText className="h-4 w-4" />
                Resume parsed successfully
              </div>
            )}
          </CardContent>
        </Card>

        {/* Step 2: JD */}
        <Card className={cn("transition-colors", (!resumeId) ? "opacity-50 pointer-events-none" : "")}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-sm font-bold">2</span>
                Target Role
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => jdFileInputRef.current?.click()}
                className="text-xs text-blue-600 hover:text-blue-700 h-8"
              >
                <Upload className="mr-2 h-3 w-3" /> PDF instead
              </Button>
              <input type="file" accept=".pdf" className="hidden" ref={jdFileInputRef} onChange={handleJdUpload} />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              value={jd}
              onChange={e => setJd(e.target.value)}
              placeholder="Paste the full job description or requirements here..."
              className="w-full h-32 rounded-lg border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white"
            />
            
            <Button 
              onClick={handleAnalyze}
              disabled={!resumeId || !jd || loading}
              className="w-full"
              isLoading={loading && !!resumeId}
            >
              <Target className="mr-2 h-4 w-4" /> Generate Fit Analysis
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Analysis Document */}
      {analysis && (
        <div className="mt-8 animate-in">
          <Card className="overflow-hidden border-blue-100">
            {/* Document Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h2 className="text-2xl font-bold mb-2">Resume Fit Analysis</h2>
                <p className="text-blue-100 max-w-xl text-sm">
                  We've mapped your resume experience against the job requirements to identify structural gaps and technical areas you must prepare for.
                </p>
              </div>
              <div className="flex flex-col items-center bg-white/10 rounded-2xl p-4 backdrop-blur-sm shrink-0 border border-white/20">
                <div className="text-5xl font-extrabold mb-1">{analysis.overall_score}<span className="text-2xl opacity-70">%</span></div>
                <div className="text-xs font-semibold tracking-wider uppercase text-blue-100">Match Score</div>
              </div>
            </div>

            {/* Document Body */}
            <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-12 bg-white">
              
              {/* Left Column: Gaps */}
              <div>
                <div className="flex items-center gap-2 mb-6 pb-2 border-b border-gray-100">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                  <h3 className="text-lg font-bold text-gray-900">Identified Gaps</h3>
                </div>
                
                {analysis.gaps?.length > 0 ? (
                  <ul className="space-y-4">
                    {analysis.gaps.map((gap: string, i: number) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-gray-700 bg-red-50/50 p-3 rounded-lg border border-red-100">
                        <span className="text-red-500 font-bold mt-0.5">•</span>
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500 italic">No major gaps identified.</p>
                )}
              </div>

              {/* Right Column: Recommendations */}
              <div>
                <div className="flex items-center gap-2 mb-6 pb-2 border-b border-gray-100">
                  <Target className="h-5 w-5 text-blue-500" />
                  <h3 className="text-lg font-bold text-gray-900">Recommended Preparation</h3>
                </div>
                
                {analysis.preparation_recommendations && analysis.preparation_recommendations.length > 0 ? (
                  <div className="space-y-4">
                    {analysis.preparation_recommendations.map((rec: any, i: number) => (
                      <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-4 relative overflow-hidden">
                        <div className={`absolute top-0 left-0 w-1 h-full ${
                          rec.severity === 'HIGH' ? 'bg-red-500' : 
                          rec.severity === 'MEDIUM' ? 'bg-amber-500' : 'bg-blue-500'
                        }`} />
                        <div className="flex justify-between items-start mb-2 pl-2">
                          <h4 className="font-semibold text-gray-900 text-sm">{rec.topic}</h4>
                          <Badge variant={rec.severity === 'HIGH' ? 'destructive' : rec.severity === 'MEDIUM' ? 'warning' : 'secondary'} className="text-[10px]">
                            {rec.severity}
                          </Badge>
                        </div>
                        <div className="pl-2">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-blue-600 mb-1">{rec.recommendation_type?.replace('_', ' ')}</p>
                          <p className="text-xs text-gray-600 leading-relaxed">{rec.reason}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <ul className="space-y-4">
                    {analysis.recommendations?.map((rec: string, i: number) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-100">
                        <ArrowRight className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
