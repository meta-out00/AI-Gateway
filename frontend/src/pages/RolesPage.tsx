import { Plus, ShieldCheck } from 'lucide-react'
import type { Role } from '../types'

export function RolesPage({
  roles,
  onAdd,
  onEdit,
  onDelete,
}: {
  roles: Role[]
  onAdd: () => void
  onEdit: (role: Role) => void
  onDelete: (role: Role) => void
}) {
  return (
    <>
      <section className="page-heading">
        <div><p className="eyebrow">ACCESS CONTROL</p><h1>Users / Roles</h1></div>
        <button className="primary-button" onClick={onAdd}><Plus size={16} /> Add Role</button>
      </section>
      <section className="panel">
        <div className="role-grid">
          {roles.map((role) => (
            <article className="role-card" key={role.id}>
              <div className="role-card-header">
                <div className="role-icon"><ShieldCheck size={18} /></div>
                <span className={`role-name ${role.role_name === 'admin' ? 'admin' : ''}`}>{role.role_name}</span>
              </div>
              <p>{role.description || 'No description'}</p>
              <dl>
                <div><dt>RPM limit</dt><dd>{role.default_rate_limit_per_minute}</dd></div>
                <div><dt>Budget</dt><dd>{role.default_max_budget_usd == null ? 'Unlimited' : `$${role.default_max_budget_usd}`}</dd></div>
                <div><dt>Allowed models</dt><dd>{role.allowed_models}</dd></div>
              </dl>
              <div className="role-actions">
                <button className="secondary-button role-edit" onClick={() => onEdit(role)}>Edit role</button>
                {role.role_name !== 'admin' && (
                  <button className="danger-text role-delete" onClick={() => onDelete(role)}>Delete role</button>
                )}
              </div>
            </article>
          ))}
          {!roles.length && <div className="table-empty">No roles found</div>}
        </div>
      </section>
    </>
  )
}
