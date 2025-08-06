import React, { useState } from 'react'

export default function App() {
  const [question, setQuestion] = useState('')
  const [limit, setLimit] = useState(5)
  const [offset, setOffset] = useState(0)
  const [plan, setPlan] = useState(null)
  const [results, setResults] = useState([])
  const [pagination, setPagination] = useState(null)
  const [error, setError] = useState(null)

  // Read API base from env (set REACT_APP_API_URL in Render frontend env)
  const API_BASE = process.env.REACT_APP_API_URL || ''

  const fetchData = async (newOffset=0) => {
    setError(null)
    const payload = { question, limit, offset: newOffset }
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
      const data = await res.json()
      setPlan(data.plan)
      setResults(data.results)
      setPagination(data.pagination || null)
      setOffset(newOffset)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl">SAP OData Assistant</h1>
      <input
        type="text"
        placeholder="Your question"
        value={question}
        onChange={e=>setQuestion(e.target.value)}
        className="border p-2 w-full my-2"
      />
      <div>
        <button onClick={()=>fetchData(0)} className="bg-blue-500 text-white px-4 py-2">
          Query
        </button>
        {pagination?.next_offset!=null && (
          <button onClick={()=>fetchData(pagination.next_offset)}
            className="ml-2 bg-green-500 text-white px-4 py-2">
            Load More
          </button>
        )}
      </div>
      {error && <p className="text-red-600">Error: {error}</p>}
      {plan && <pre className="bg-gray-100 p-2 mt-4">{JSON.stringify(plan, null,2)}</pre>}
      {results.length>0 && (
        <table className="mt-4 border-collapse w-full">
          <thead>
            <tr>{Object.keys(results[0]).map(k=>(<th key={k} className="border p-1">{k}</th>))}</tr>
          </thead>
          <tbody>
            {results.map((r,i)=>(
              <tr key={i} className="hover:bg-gray-50">
                {Object.values(r).map((v,j)=>(<td key={j} className="border p-1">{String(v)}</td>))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}