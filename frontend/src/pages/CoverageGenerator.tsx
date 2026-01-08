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
  const [regenBusy, setRegenBusy] = useState(false)
  const [regenMsg, setRegenMsg] = useState<string | null>(null)

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

  // --- Regenerate (optimized) for an existing combined dataset id ---
  const [existingDatasetId, setExistingDatasetId] = useState('')
  const slugify = (s: string) => s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
  const parseCoverageCombined = (id: string) => {
    if (!id || !id.startsWith('coverage-')) return null
    const parts = id.split('-')
    if (parts.length < 4) return null
    const last = parts[parts.length - 1]
    const penultimate = parts[parts.length - 2]
    if (penultimate !== 'combined') return null
    const version = last
    const domainSlug = parts.slice(1, parts.length - 2).join('-')
    if (!domainSlug) return null
    return { domainSlug, version }
  }
  const regenerateOptimized = async () => {
    setRegenMsg(null)
    if (!existingDatasetId) { setRegenMsg('Enter an existing combined dataset id.'); return }
    const parsed = parseCoverageCombined(existingDatasetId)
    if (!parsed) { setRegenMsg('Only coverage-<domain>-combined-<version> dataset ids are supported.'); return }
    setRegenBusy(true)
    try {
      const t = await fetch('/coverage/taxonomy')
      if (!t.ok) throw new Error(`Taxonomy HTTP ${t.status}`)
      const tj = await t.json()
      const domains: string[] = Array.isArray(tj.domains) ? tj.domains : []
      const match = domains.find(d => slugify(d) === parsed.domainSlug)
      if (!match) throw new Error('Domain not found in taxonomy for dataset id.')
      const body = { combined: true, dry_run: false, save: true, overwrite: true, domains: [match], version: parsed.version }
      const r = await fetch('/coverage/generate', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
      const js = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(js?.detail || `Generate HTTP ${r.status}`)
      setRegenMsg('Regenerated with optimized coverage (pairwise). Files overwritten.')
    } catch (e:any) {
      setRegenMsg(e.message || 'Failed to regenerate')
    } finally {
      setRegenBusy(false)
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
              <a className="rounded-md px-3 py-2 bg-primary text-white text-sm" href={`/coverage/report.csv?type=summary${selectedDomains.length?`&domains=${encodeURIComponent(selectedDomains.join(','))}`:''}${selectedBehaviors.length?`&behaviors=${encodeURIComponent(selectedBehaviors.join(','))}`:''}`} download>
                Download Summary CSV
              </a>
              <a className="rounded-md px-3 py-2 bg-success text-white text-sm" href={`/coverage/report.csv?type=heatmap${selectedDomains.length?`&domains=${encodeURIComponent(selectedDomains.join(','))}`:''}${selectedBehaviors.length?`&behaviors=${encodeURIComponent(selectedBehaviors.join(','))}`:''}`} download>
                Download Heatmap CSV
              </a>
            </div>
            {msg && <div className="text-success">{msg}</div>}
            {err && <div className="text-danger">{err}</div>}
            <div className="mt-4 border-t pt-3">
              <div className="font-medium mb-1">Regenerate (optimized)</div>
              <div className="flex items-center gap-2">
                <input className="border rounded px-2 py-1 grow" placeholder="coverage-<domain>-combined-<version>" value={existingDatasetId} onChange={e => setExistingDatasetId(e.target.value)} />
                <Button onClick={regenerateOptimized} disabled={regenBusy}>{regenBusy ? 'Regenerating…' : 'Run'}</Button>
              </div>
              <div className="text-xs text-gray-600 mt-1">Overwrites the specified combined dataset using current optimization settings (configs/coverage.json)</div>
              {regenMsg && <div className="text-xs mt-1">{regenMsg}</div>}
            </div>
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
                  <a className="ml-2 text-xs underline text-primary" href={`/coverage/report.csv?type=summary&domains=${encodeURIComponent(p.domain)}&behaviors=${encodeURIComponent(p.behavior)}`} download>
                    CSV
                  </a>
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
