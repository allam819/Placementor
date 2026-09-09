import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function Resume() {
  const [file, setFile] = useState<File | null>(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [resumeId, setResumeId] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
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
        alert('Resume uploaded and parsed successfully!')
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
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-4">Resume Analyzer</h2>
        <p className="text-gray-600 mb-6">Upload your PDF resume and paste a target job description to get an AI match score and tailored improvements.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">1. Upload Resume</h3>
          <form onSubmit={handleUpload} className="space-y-4">
            <input 
              type="file" 
              accept=".pdf" 
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <button 
              type="submit" 
              disabled={!file || loading}
              className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Uploading...' : 'Upload & Parse PDF'}
            </button>
          </form>
          {resumeId && <p className="text-sm text-green-600 mt-2">✓ Resume parsed and ready</p>}
        </div>

        {/* JD Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">2. Target Job Description</h3>
            <label className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
              Upload PDF instead
              <input type="file" accept=".pdf" className="hidden" onChange={handleJdUpload} />
            </label>
          </div>
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste the full job description here or upload a PDF..."
            className="w-full h-32 rounded-md border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
          />
          <button 
            onClick={handleAnalyze}
            disabled={!resumeId || !jd || loading}
            className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Analyzing Match...' : 'Generate Analysis'}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {analysis && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-6">
          <div className="flex items-center gap-4 border-b pb-4">
            <div className="text-4xl font-bold text-blue-600">{analysis.overall_score}%</div>
            <div>
              <h3 className="text-lg font-semibold">Match Score</h3>
              <p className="text-sm text-gray-500">Based on semantic mapping of your experience to the JD requirements.</p>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-red-600 mb-2">Identified Gaps</h4>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              {analysis.gaps.map((gap: str, i: number) => <li key={i}>{gap}</li>)}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-green-600 mb-2">Recommendations to Improve</h4>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              {analysis.recommendations.map((rec: str, i: number) => <li key={i}>{rec}</li>)}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
