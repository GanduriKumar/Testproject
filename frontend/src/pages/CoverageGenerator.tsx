import React, { useEffect, useMemo, useState } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import { Checkbox, Select } from '../components/Form'

type Pair = {
  domain: string
  behavior: string
  raw_total: number
  final_total: number
  breakdown: { name: string, type: string, removed_exclude: number, removed_cap: number }[]
}

export default function CoverageGeneratorPage() {
  const [domains, setDomains] = useState<string[]>([])
  const [behaviors, setBehaviors] = useState<string[]>([])
  const [selectedDomains, setSelectedDomains] = useState<string[]>([])
  const [selectedBehaviors, setSelectedBehaviors] = useState<string[]>([])
  const [manifestPairs, setManifestPairs] = useState<Pair[]>([])
  const [combined, setCombined] = useState(true)
  const [save, setSave] = useState(false)
  const [overwrite, setOverwrite] = useState(false)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string| null>(null)
  const [err, setErr] = useState<string| null>(null)

  useEffect(() => {
    const load = async () => {
      const r = await fetch('/coverage/taxonomy')
      const js = await r.json()
      setDomains(js.domains || [])
      setBehaviors(js.behaviors || [])
    }
    load()
  }, [])

  const loadManifest = async () => {
    setBusy(true); setErr(null)
    try {
      const params = new URLSearchParams()
      if (selectedDomains.length) params.set('domains', selectedDomains.join(','))
      if (selectedBehaviors.length) params.set('behaviors', selectedBehaviors.join(','))
      const r = await fetch('/coverage/manifest' + (params.toString() ? `?${params.toString()}` : ''))
      const js = await r.json()
      setManifestPairs(js.pairs || [])
    } catch (e:any) {
      setErr(e.message || 'Failed to load manifest')
    } finally {
      setBusy(false)
    }
  }

  const triggerGenerate = async () => {
    setBusy(true); setErr(null); setMsg(null)
    try {
      const body = {
        combined,
        dry_run: !save,
        save,
        overwrite,
        domains: selectedDomains.length ? selectedDomains : undefined,
        behaviors: selectedBehaviors.length ? selectedBehaviors : undefined,
        version: '1.0.0'
      }
      const r = await fetch('/coverage/generate', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
      const js = await r.json()
      if (!r.ok) throw new Error(js?.detail || 'Generation failed')
      if (js.saved) setMsg(`Saved ${js.files?.length || 0} dataset(s) to server`)
      else setMsg(`Generated ${js.outputs?.length || 0} dataset(s) (dry run)`) 
    } catch (e:any) {
      setErr(e.message || 'Generation failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-4">
      <Card title="Coverage Generator">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
          <label className="flex items-center gap-2"><span className="w-28">Domains</span>
            <Select multiple value={selectedDomains} onChange={e => setSelectedDomains(Array.from(e.target.selectedOptions).map(o => o.value))} className="grow min-h-28">
              {domains.map(d => <option key={d} value={d}>{d}</option>)}
            </Select>
          </label>
          <label className="flex items-center gap-2"><span className="w-28">Behaviors</span>
            <Select multiple value={selectedBehaviors} onChange={e => setSelectedBehaviors(Array.from(e.target.selectedOptions).map(o => o.value))} className="grow min-h-28">
              {behaviors.map(b => <option key={b} value={b}>{b}</option>)}
            </Select>
          </label>
          <div className="flex flex-col gap-2">
            <label className="inline-flex items-center gap-2"><Checkbox checked={combined} onChange={e => setCombined((e.target as HTMLInputElement).checked)} /> Combined (per-domain + global)</label>
            <label className="inline-flex items-center gap-2"><Checkbox checked={save} onChange={e => setSave((e.target as HTMLInputElement).checked)} /> Save to server</label>
            <label className="inline-flex items-center gap-2"><Checkbox checked={overwrite} onChange={e => setOverwrite((e.target as HTMLInputElement).checked)} disabled={!save} /> Overwrite</label>
            <div className="flex gap-2 mt-1">
              <Button variant="primary" onClick={loadManifest} disabled={busy}>Preview coverage</Button>
              <Button variant="success" onClick={triggerGenerate} disabled={busy}>Generate</Button>
            </div>
            {msg && <div className="text-success">{msg}</div>}
            {err && <div className="text-danger">{err}</div>}
          </div>
        </div>
      </Card>

      <Card title="Coverage Preview">
        {!manifestPairs.length && <div className="text-sm text-gray-700">No selection yet. Click Preview coverage.</div>}
        {!!manifestPairs.length && (
          <div className="space-y-4">
            {manifestPairs.map(p => (
              <div key={`${p.domain}-${p.behavior}`} className="rounded border border-gray-200 p-3">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-semibold">{p.domain}</span>
                  <span className="text-gray-500">/ {p.behavior}</span>
                  <div className="grow" />
                  <span className="text-xs">Raw: {p.raw_total} | Final: {p.final_total}</span>
                </div>
                <div className="mt-2 text-xs text-gray-700">
                  {p.breakdown.map(b => (
                    <div key={b.name} className="flex gap-2">
                      <span className="w-56 truncate" title={b.name}>{b.name}</span>
                      <span className="text-gray-500">({b.type})</span>
                      <span className="ml-auto">-exclude: {b.removed_exclude}, -cap: {b.removed_cap}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
