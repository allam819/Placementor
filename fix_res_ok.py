import os
import glob
import re

for filepath in glob.glob('frontend/src/pages/*.tsx'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. if (res.ok) setSomething(await res.json()) -> setSomething(res)
    # 2. if (res.ok) { const data = res; ... } else { alert(...) }
    
    # Let's do string replacement for the common patterns:
    
    content = content.replace("if (res.ok) {\n        const data = res\n        setResumeId(data.id)\n        alert('Resume uploaded and parsed successfully!')\n      } else {\n        alert('Failed to upload: ' + String(res))\n      }", "const data = res\n      setResumeId(data.id)\n      alert('Resume uploaded and parsed successfully!')")
    
    content = content.replace("if (res.ok) {\n        const data = res\n        setAnalysis(data.analysis)\n      } else {\n        alert('Analysis failed: ' + String(res))\n      }", "const data = res\n      setAnalysis(data.analysis)")

    content = content.replace("if (res.ok) {\n        const data = res\n        if (!data.text || data.text.trim() === '') {\n          alert('Could not extract any text from this PDF. It might be a scanned image rather than a text document.')\n        } else {\n          setJd(data.text)\n        }\n      } else {\n        alert('Failed to parse JD PDF: ' + String(res))\n      }", "const data = res\n      if (!data.text || data.text.trim() === '') {\n        alert('Could not extract any text from this PDF. It might be a scanned image rather than a text document.')\n      } else {\n        setJd(data.text)\n      }")
    
    content = content.replace("if (res.ok) {\n      const data = res\n      setName(data.name || '')\n      setTargetRole(data.target_role || '')\n      setTargetCompany(data.target_company || '')\n    }", "const data = res\n    setName(data.name || '')\n    setTargetRole(data.target_role || '')\n    setTargetCompany(data.target_company || '')")

    content = content.replace("if (res.ok) {\n      alert('Profile saved!')\n    } else {\n      alert('Failed to save profile')\n    }", "alert('Profile saved!')")
    
    content = content.replace("if (res.ok) setGoals(res)", "setGoals(res)")
    content = content.replace("if (res.ok) {\n      setGoals([...goals, res])\n      setNewGoal('')\n    }", "setGoals([...goals, res])\n    setNewGoal('')")

    content = content.replace("if (res.ok) setRecommendations(res)", "setRecommendations(res)")
    content = content.replace("if (res.ok) setActivities(res)", "setActivities(res)")
    content = content.replace("if (res.ok) {\n        setSearchResults(res)\n      }", "setSearchResults(res)")
    content = content.replace("if (res.ok) {\n        setMessages(prev => [...prev, { role: 'assistant', content: res.message }])\n      }", "setMessages(prev => [...prev, { role: 'assistant', content: res.message }])")
    content = content.replace("if (res.ok) setSelectedActivity(res)", "setSelectedActivity(res)")
    
    content = content.replace("if (res.ok) {\n      setProblem(res)\n      // Update tests\n      setTests(res.test_cases?.map((t: any) => ({\n        input: t.input_data,\n        expected: t.expected_output,\n        actual: '',\n        passed: false,\n        hidden: t.is_hidden\n      })) || [])\n    }", "setProblem(res)\n    // Update tests\n    setTests(res.test_cases?.map((t: any) => ({\n      input: t.input_data,\n      expected: t.expected_output,\n      actual: '',\n      passed: false,\n      hidden: t.is_hidden\n    })) || [])")
    
    content = content.replace("if (res.ok) {\n        setTests(tests.map(t => {\n          const tRes = res.test_results?.find((tr: any) => tr.input === t.input)\n          if (tRes) {\n            return { ...t, actual: tRes.actual, passed: tRes.passed }\n          }\n          return t\n        }))\n        setSubmitResult({ status: res.status, feedback: res.feedback, time_ms: res.execution_time_ms })\n      }", "setTests(tests.map(t => {\n        const tRes = res.test_results?.find((tr: any) => tr.input === t.input)\n        if (tRes) {\n          return { ...t, actual: tRes.actual, passed: tRes.passed }\n        }\n        return t\n      }))\n      setSubmitResult({ status: res.status, feedback: res.feedback, time_ms: res.execution_time_ms })")
    
    content = content.replace("if (res.ok) {\n        setMessages(prev => [...prev, { role: 'assistant', content: res.hint }])\n      }", "setMessages(prev => [...prev, { role: 'assistant', content: res.hint }])")
    
    content = content.replace("if (res.ok) {\n        setProblem(res.problem)\n        setSessionId(res.session_id)\n        setMessages([{ role: 'assistant', content: res.message }])\n      }", "setProblem(res.problem)\n      setSessionId(res.session_id)\n      setMessages([{ role: 'assistant', content: res.message }])")
    
    content = content.replace("if (res.ok) {\n        const data = res\n        // Map test results\n        setTests(tests.map(t => {\n          const tr = data.test_results?.find((r: any) => r.input === t.input)\n          if (tr) return { ...t, actual: tr.actual, passed: tr.passed }\n          return t\n        }))\n        if (data.ai_feedback) {\n          setMessages(prev => [...prev, { role: 'assistant', content: data.ai_feedback }])\n        }\n      }", "const data = res\n      // Map test results\n      setTests(tests.map(t => {\n        const tr = data.test_results?.find((r: any) => r.input === t.input)\n        if (tr) return { ...t, actual: tr.actual, passed: tr.passed }\n        return t\n      }))\n      if (data.ai_feedback) {\n        setMessages(prev => [...prev, { role: 'assistant', content: data.ai_feedback }])\n      }")

    content = content.replace("if (res.ok) {\n        setMessages(prev => [...prev, { role: 'assistant', content: res.message }])\n      }", "setMessages(prev => [...prev, { role: 'assistant', content: res.message }])")
    
    content = content.replace("if (res.ok) {\n        navigate('/interview', { state: { evaluation: res } })\n      }", "navigate('/interview', { state: { evaluation: res } })")
    
    content = content.replace("if (res.ok) setProblems(res)", "setProblems(res)")
    content = content.replace("if (res.ok) {\n        setProblems(problems.filter(p => p.id !== id))\n      }", "setProblems(problems.filter(p => p.id !== id))")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("done")
