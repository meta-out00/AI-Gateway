import { useState } from 'react'
import { Plus, Search } from 'lucide-react'
import { StatusBadge } from '../components/Shared'
import type { ApiKey } from '../types'

export function ApiKeysPage({
  apiKeys,
  onCreate,
  onRevoke,
}: {
  apiKeys: ApiKey[]
  onCreate: () => void
  onRevoke: (id: number) => void
}) {
  const [search, setSearch] = useState('')
  const filtered = apiKeys.filter((key) =>
    `${key.key_name} ${key.key_prefix} ${key.role_name || ''}`.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <>
      <section className="page-heading">
        <div><p className="eyebrow">ACCESS CONTROL</p><h1>API Keys</h1></div>
        <button className="primary-button" onClick={onCreate}><Plus size={16} /> Create Key</button>
      </section>
      <section className="panel">
        <div className="table-toolbar">
          <div className="search-field"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search API keys..." /></div>
          <span>{filtered.length} results</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Key</th><th>Role</th><th>RPM</th><th>Budget</th><th>Spend</th><th>Expires</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {filtered.map((key) => (
                <tr key={key.id}>
                  <td><strong>{key.key_name}</strong><div className="subtext">{key.key_prefix}</div></td>
                  <td>{key.role_name || '—'}</td>
                  <td>{key.rate_limit_per_minute ?? 'Role default'}</td>
                  <td>{key.max_budget_usd == null ? 'No limit' : `$${key.max_budget_usd}`}</td>
                  <td>${key.current_spend_usd.toFixed(4)}</td>
                  <td>{key.expires_at ? new Date(key.expires_at).toLocaleString() : 'Never'}</td>
                  <td><StatusBadge active={key.is_active} /></td>
                  <td>{key.is_active && <button className="danger-text" onClick={() => onRevoke(key.id)}>Revoke</button>}</td>
                </tr>
              ))}
              {!filtered.length && <tr><td colSpan={8}><div className="table-empty">No API keys found</div></td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
