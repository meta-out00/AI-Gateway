import { ShieldCheck } from 'lucide-react'

export function SettingsPage() {
  return (
    <>
      <section className="page-heading"><div><p className="eyebrow">SYSTEM</p><h1>Settings</h1></div></section>
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-header"><div><p className="eyebrow">CONNECTION</p><h2>Gateway</h2></div></div>
          <dl className="settings-list">
            <div><dt>API endpoint</dt><dd>/api</dd></div>
            <div><dt>Chat endpoint</dt><dd>/v1/chat/completions</dd></div>
            <div><dt>Health endpoint</dt><dd>/health</dd></div>
          </dl>
        </article>
        <article className="panel">
          <div className="panel-header"><div><p className="eyebrow">SECURITY</p><h2>Authentication</h2></div></div>
          <div className="secure-row">
            <ShieldCheck size={20} />
            <div><strong>Admin JWT</strong><p>Protected control-plane routes use Bearer tokens.</p></div>
          </div>
        </article>
      </section>
    </>
  )
}
