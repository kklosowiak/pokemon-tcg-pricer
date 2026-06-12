import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Camera, FileSpreadsheet, Layers, RefreshCw } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Scanner from './components/Scanner';
import SpreadsheetUploader from './components/SpreadsheetUploader';
import InventorySheet from './components/InventorySheet';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [inventory, setInventory] = useState([]);
  const [lots, setLots] = useState(['Main Lot']);
  const [loading, setLoading] = useState(true);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/inventory');
      const data = await res.json();
      if (Array.isArray(data)) setInventory(data);

      const lotsRes = await fetch('/api/lots');
      if (lotsRes.ok) {
        const lotsData = await lotsRes.json();
        if (Array.isArray(lotsData)) setLots(lotsData);
      }
    } catch (e) {
      console.error('Failed to load inventory', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchInventory(); }, []);

  const tabs = [
    { id: 'dashboard',    label: 'Dashboard',  Icon: LayoutDashboard },
    { id: 'scanner',      label: 'Scanner',    Icon: Camera },
    { id: 'spreadsheet',  label: 'Spreadsheet',Icon: FileSpreadsheet },
    { id: 'inventory',    label: 'Inventory',  Icon: Layers },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Header ── */}
      <header
        className="glass-panel"
        style={{
          margin: '12px 12px 0',
          padding: '12px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderRadius: '16px',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 38, height: 38,
            background: 'linear-gradient(135deg, var(--primary), var(--success))',
            borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 900, fontSize: 14,
            boxShadow: '0 4px 14px var(--primary-glow)',
          }}>
            TCG
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 15, letterSpacing: '-0.3px' }}>Pokémon Pricer</div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
              {loading ? 'Loading…' : `${inventory.length} cards · ${lots.length} lot${lots.length !== 1 ? 's' : ''}`}
            </div>
          </div>
        </div>

        {/* Tab bar */}
        <div className="tab-bar">
          {tabs.map(({ id, label, Icon }) => (
            <button
              key={id}
              className={`tab-btn${activeTab === id ? ' active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>

        {/* Refresh */}
        <button className="btn btn-ghost btn-sm" onClick={fetchInventory} disabled={loading}>
          <RefreshCw size={13} className={loading ? 'spin' : ''} />
          Refresh
        </button>
      </header>

      {/* ── Page content ── */}
      <main style={{ flex: 1, padding: '16px 0 0' }}>
        {activeTab === 'dashboard' && (
          <Dashboard inventory={inventory} lots={lots} />
        )}
        {activeTab === 'scanner' && (
          <Scanner onSaved={fetchInventory} />
        )}
        {activeTab === 'spreadsheet' && (
          <SpreadsheetUploader onSaved={fetchInventory} />
        )}
        {activeTab === 'inventory' && (
          <InventorySheet
            inventory={inventory}
            onDelete={fetchInventory}
            onRefresh={fetchInventory}
          />
        )}
      </main>
    </div>
  );
}
