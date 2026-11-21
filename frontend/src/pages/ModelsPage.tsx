import { useState } from 'react'
import { Search } from 'lucide-react'
import { StatusBadge } from '../components/Shared'
import type { Provider } from '../types'

export function ModelsPage({ models }: { models: Provider[] }) {
  const [search, setSearch] = useState('')
  const filtered = models.filter((provider) =>
    `${provider.default_model} ${provider.name}`.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <>
      <section className="page-heading"><div><p className="eyebrow">MODEL CATALOG</p><h1>Models</h1></div></section>
      <section className="panel">
        <div className="table-toolbar">
          <div className="search-field"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search models..." /></div>
          <span>{filtered.length} results</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Model</th><th>Provider</th><th>Base URL</th><th>Status</th></tr></thead>
            <tbody>
              {filtered.map((provider) => (
                <tr key={provider.id}>
                  <td><strong>{provider.default_model}</strong></td>
                  <td>{provider.name}</td>
                  <td className="muted-cell">{provider.base_url}</td>
                  <td><StatusBadge active={provider.is_active} /></td>
                </tr>
              ))}
              {!filtered.length && <tr><td colSpan={4}><div className="table-empty">No models found</div></td></tr>}
            </tbody>
          </table>
        </div>
        <div className="panel-note">Models are derived from each provider&apos;s <code>default_model</code>. There is no separate model CRUD API.</div>
      </section>
    </>
  )
}
