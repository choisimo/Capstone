import React, { useEffect, useMemo, useState } from 'react'

function Section({ title, children }) {
  return (
    <section style={{border: '1px solid #ddd', borderRadius: 6, padding: 16, marginBottom: 16}}>
      <h2 style={{marginTop: 0}}>{title}</h2>
      {children}
    </section>
  )
}

function Textarea({label, value, onChange, rows=4}) {
  return (
    <label style={{display: 'block', marginBottom: 8}}>
      <div style={{fontSize: 12, opacity: 0.8, marginBottom: 4}}>{label}</div>
      <textarea rows={rows} value={value} onChange={e => onChange(e.target.value)} style={{width: '100%'}} />
    </label>
  )
}

function Input({label, value, onChange, type='text'}) {
  return (
    <label style={{display: 'block', marginBottom: 8}}>
      <div style={{fontSize: 12, opacity: 0.8, marginBottom: 4}}>{label}</div>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} style={{width: '100%'}} />
    </label>
  )
}

function Button({children, ...props}) {
  return <button {...props} style={{padding: '6px 12px', marginRight: 8}}>{children}</button>
}

function StepsPreview({steps}) {
  return (
    <div>
      {!steps?.length && <div style={{opacity: 0.6}}>No steps.</div>}
      {steps?.map((s, i) => (
        <div key={i} style={{padding: '6px 0', borderBottom: '1px dashed #eee'}}>
          <div><b>Operation:</b> {s.operation}</div>
          {s.selector ? <div><b>Selector:</b> {s.selector}</div> : null}
          {s.optional_value ? <div><b>Value:</b> {s.optional_value}</div> : null}
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [info, setInfo] = useState(null)

  const apiBase = useMemo(() => '/api/v1', [])

  useEffect(() => {
    fetch('/api/v1/ui/agent-info').then(r => r.json()).then(setInfo).catch(() => setInfo(null))
  }, [])

  // Generate steps state
  const [url, setUrl] = useState('https://www.nps.or.kr')
  const [instruction, setInstruction] = useState('Click element containing text "More". Scroll down. Wait 1 seconds.')
  const [gen, setGen] = useState({steps: [], notes: ''})

  // Create watch state
  const [title, setTitle] = useState('Example watch')
  const [createResult, setCreateResult] = useState(null)
  const [recheck, setRecheck] = useState(true)

  // List watches
  const [watches, setWatches] = useState(null)

  const doGenerate = async () => {
    const r = await fetch(`${apiBase}/agent/generate-steps`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, instruction})
    })
    const j = await r.json()
    setGen(j)
  }

  const doCreate = async () => {
    const r = await fetch(`${apiBase}/agent/create-watch`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, title, steps: gen.steps, recheck})
    })
    const j = await r.json()
    setCreateResult(j)
  }

  const loadWatches = async () => {
    const r = await fetch(`${apiBase}/ui/watches`)
    const j = await r.json()
    setWatches(j)
  }

  return (
    <div style={{maxWidth: 1000, margin: '0 auto', padding: 16, fontFamily: 'ui-sans-serif, system-ui, sans-serif'}}>
      <h1>ChangeDetection Agent UI</h1>
      {info ? (
        <div style={{opacity: 0.8}}>
          <div><b>CD Base:</b> {info.cd_base_url} | <b>API Key:</b> {info.api_key_configured ? 'configured' : 'missing'}</div>
          <div><b>Agent:</b> port {info.agent.port} | allow JS: {String(info.agent.allow_execute_js)}</div>
        </div>
      ) : <div style={{opacity: 0.6}}>Loading agent info...</div>}

      <Section title="Step Generation">
        <Input label="URL" value={url} onChange={setUrl} />
        <Textarea label="Instruction" value={instruction} onChange={setInstruction} rows={4} />
        <Button onClick={doGenerate}>Generate</Button>
        {gen?.notes && <div style={{marginTop: 8, opacity: 0.8}}>{gen.notes}</div>}
        <div style={{marginTop: 12}}>
          <StepsPreview steps={gen.steps} />
        </div>
      </Section>

      <Section title="Create Watch">
        <Input label="Title" value={title} onChange={setTitle} />
        <label style={{display: 'inline-flex', alignItems: 'center', gap: 6}}>
          <input type="checkbox" checked={recheck} onChange={e => setRecheck(e.target.checked)} /> Recheck after create
        </label>
        <div style={{marginTop: 8}}>
          <Button onClick={doCreate}>Create Watch</Button>
        </div>
        {createResult && <pre>{JSON.stringify(createResult, null, 2)}</pre>}
      </Section>

      <Section title="Watches">
        <div style={{marginBottom: 8}}>
          <Button onClick={loadWatches}>Refresh</Button>
        </div>
        <pre style={{maxHeight: 300, overflow: 'auto'}}>{watches ? JSON.stringify(watches, null, 2) : 'No data'}</pre>
      </Section>

      <footer style={{marginTop: 24, fontSize: 12, opacity: 0.7}}>
        Ensure ChangeDetection.io is running with webdriver fetcher support.
      </footer>
    </div>
  )
}
