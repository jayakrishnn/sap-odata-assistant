import React, { useState, useEffect } from 'react'

export default function App() {
  const [question, setQuestion] = useState('')
  const [limit, setLimit] = useState(5)
  const [offset, setOffset] = useState(0)
  const [plan, setPlan] = useState(null)
  const [results, setResults] = useState([])
  const [pagination, setPagination] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = async (newOffset = offset) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, limit, offset: newOffset })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Unknown error')
      }
      const data = await res.json()
      setPlan(data.plan)
      setResults(data.results)
      setPagination(data.pagination || null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleQuery = () => {
    setOffset(0)
    fetchData(0)
  }

  const handleNext = () => {
    if (pagination?.next_offset != null) {
      setOffset(pagination.next_offset)
      fetchData(pagination.next_offset)
    }
  }

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">SAP OData Assistant</h1>

      <div className="mb-4 grid grid-cols-3 gap-2">
        <input
          type="text"
          placeholder="Enter your question"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          className="col-span-3 p-2 border rounded"
        />
        <input
          type="number"
          min={1}
          value={limit}
          onChange={e => setLimit(Number(e.target.value))}
          className="p-2 border rounded"
        />
        <button
          onClick={handleQuery}
          className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Query
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {plan && (
        <div className="mb-4">
          <h2 className="text-xl font-semibold">Plan</h2>
          <pre className="bg-gray-100 p-2 rounded overflow-x-auto">
            {JSON.stringify(plan, null, 2)}
          </pre>
        </div>
      )}

      {results.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-2">Results</h2>
          <table className="min-w-full border-collapse">
            <thead>
              <tr>
                {Object.keys(results[0]).map(key => (
                  <th key={key} className="border p-2 text-left uppercase text-sm">
                    {key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  {Object.values(row).map((val, i) => (
                    <td key={i} className="border p-2">
                      {String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {pagination?.next_offset != null && (
            <button
              onClick={handleNext}
              className="mt-4 p-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Load More
            </button>
          )}
        </div>
      )}
    </div>
  )
}
 