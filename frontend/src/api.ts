interface HealthResponse {
  status: 'ok'
}

async function checkApi(signal: AbortSignal): Promise<boolean> {
  const response = await fetch('/api/v1/health', { signal })
  if (!response.ok) return false
  const data = (await response.json()) as HealthResponse
  return data.status === 'ok'
}

export { checkApi }
