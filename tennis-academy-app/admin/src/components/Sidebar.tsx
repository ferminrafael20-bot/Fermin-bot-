import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

interface NavItem {
  label: string;
  path?: string;
  children?: { label: string; path: string }[];
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Clases',
    children: [
      { label: 'Clases grupales', path: '/clases/grupales' },
      { label: 'Clases particulares', path: '/clases/particulares' },
    ],
  },
  { label: 'Profesores', path: '/profesores' },
  { label: 'Tienda', path: '/tienda' },
  { label: 'Descuentos exclusivos', path: '/descuentos' },
  { label: 'Reservas', path: '/reservas' },
];

export default function Sidebar() {
  const [expanded, setExpanded] = useState(true);
  const [openGroup, setOpenGroup] = useState<string | null>('Clases');

  return (
    <aside
      style={{
        width: expanded ? 240 : 64,
        transition: 'width 0.2s ease',
        background: '#fff',
        borderRight: '1px solid var(--color-border)',
        height: '100vh',
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: expanded ? 'space-between' : 'center', padding: '16px 12px' }}>
        {expanded && <strong style={{ color: 'var(--color-primary)', fontSize: 15 }}>Academia de Tenis</strong>}
        <button
          className="btn-secondary"
          onClick={() => setExpanded((v) => !v)}
          aria-label={expanded ? 'Colapsar menu' : 'Expandir menu'}
          style={{ border: 'none', background: 'transparent', fontSize: 18, padding: 6 }}
        >
          {expanded ? '◀' : '▶'}
        </button>
      </div>

      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 8px' }}>
        {NAV_ITEMS.map((item) => {
          if (!item.children) {
            return (
              <NavLink
                key={item.label}
                to={item.path!}
                style={({ isActive }) => navLinkStyle(isActive, expanded)}
              >
                {expanded ? item.label : item.label.charAt(0)}
              </NavLink>
            );
          }

          const isOpen = openGroup === item.label;
          return (
            <div key={item.label}>
              <button
                onClick={() => setOpenGroup(isOpen ? null : item.label)}
                style={{
                  ...navLinkStyle(false, expanded),
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  display: 'flex',
                  justifyContent: expanded ? 'space-between' : 'center',
                  alignItems: 'center',
                }}
              >
                <span>{expanded ? item.label : item.label.charAt(0)}</span>
                {expanded && <span style={{ fontSize: 11 }}>{isOpen ? '▲' : '▼'}</span>}
              </button>
              {isOpen && expanded && (
                <div style={{ paddingLeft: 16 }}>
                  {item.children.map((child) => (
                    <NavLink
                      key={child.path}
                      to={child.path}
                      style={({ isActive }) => navLinkStyle(isActive, expanded, true)}
                    >
                      {child.label}
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}

function navLinkStyle(isActive: boolean, expanded: boolean, isChild = false): React.CSSProperties {
  return {
    display: 'block',
    padding: isChild ? '8px 12px' : '10px 12px',
    marginBottom: 2,
    borderRadius: 8,
    fontSize: isChild ? 13 : 14,
    fontWeight: isActive ? 700 : 500,
    color: isActive ? 'var(--color-primary)' : 'var(--color-text)',
    background: isActive ? '#e8f5e9' : 'transparent',
    textDecoration: 'none',
    textAlign: expanded ? 'left' : 'center',
    whiteSpace: 'nowrap',
  };
}
