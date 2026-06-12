import React, { useState, useMemo } from 'react';
import { Search, Trash2, RefreshCw, Copy, Check } from 'lucide-react';

function fmt(v) {
  if (v == null || isNaN(Number(v))) return '—';
  return '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function InventorySheet({ inventory, onDelete, onRefresh }) {
  const [query, setQuery]       = useState('');
  const [lotFilter, setLotFilter] = useState('');
  const [copied, setCopied]     = useState(false);
  const [repricing, setRepricing] = useState(new Set());

  const lots = useMemo(() => {
    const s = new Set(inventory.map(c => c.lot_name || 'Main Lot'));
    return ['', ...Array.from(s).sort()];
  }, [inventory]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return inventory.filter(c => {
      const matchQ = !q || [c.name, c.set_name, c.num].some(f => String(f || '').toLowerCase().includes(q));
      const matchL = !lotFilter || (c.lot_name || 'Main Lot') === lotFilter;
      return matchQ && matchL;
    });
  }, [inventory, query, lotFilter]);

  const copyTSV = () => {
    const header = ['Name', 'Set', '#', 'Lot', 'Slab', 'Cost', 'Collectr', 'TCG Raw', 'PC Raw', 'PSA 8', 'PSA 9', 'PSA 10'];
    const rows = filtered.map(c => [
      c.name, c.set_name, c.num, c.lot_name || '',
      c.slab_grade || '', c.cost_paid || '', c.collectr || '',
      c.tcgplayer || '', c.raw || '', c.psa_8 || '', c.psa_9 || '', c.psa_10 || ''
    ]);
    const tsv = [header, ...rows].map(r => r.join('\t')).join('\n');
    navigator.clipboard.writeText(tsv);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const repriceCard = async (card) => {
    setRepricing(prev => new Set([...prev, card.id]));
    try {
      const res = await fetch('/api/reprice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: card.name, set_name: card.set_name, num: card.num, card_id: card.id }),
      });
      await res.json();
      if (onRefresh) onRefresh();
    } catch {}
    setRepricing(prev => { const n = new Set(prev); n.delete(card.id); return n; });
  };

  const deleteCard = async (id) => {
    if (!window.confirm('Delete this card?')) return;
    await fetch(`/api/inventory/${id}`, { method: 'DELETE' });
    if (onDelete) onDelete();
  };

  return (
    <div className="fade-in" style={{ padding: '0 16px 24px' }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>📋 Inventory</h1>
        <p className="text-muted" style={{ fontSize: 13, marginTop: 4 }}>
          {inventory.length} cards across {lots.length - 1} lot{lots.length !== 2 ? 's' : ''}
        </p>
      </div>

      {/* Filters + actions */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 200px', minWidth: 180 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', pointerEvents: 'none' }} />
          <input
            className="input"
            style={{ paddingLeft: 32 }}
            placeholder="Search name, set, number…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
        <select
          className="input"
          style={{ maxWidth: 200, flex: '0 0 auto' }}
          value={lotFilter}
          onChange={e => setLotFilter(e.target.value)}
        >
          {lots.map(l => <option key={l} value={l}>{l || 'All Lots'}</option>)}
        </select>
        <button className="btn btn-ghost btn-sm" onClick={copyTSV} style={{ whiteSpace: 'nowrap' }}>
          {copied ? <><Check size={12} /> Copied!</> : <><Copy size={12} /> Copy to Sheets</>}
        </button>
        <button className="btn btn-ghost btn-sm" onClick={onRefresh}>
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-dim)' }}>
          <Search size={36} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <p>{inventory.length === 0 ? 'No cards yet.' : 'No cards match your search.'}</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ minWidth: 160 }}>Card Name</th>
                <th style={{ minWidth: 160 }}>Set Name</th>
                <th style={{ minWidth: 60 }}>Card #</th>
                <th style={{ minWidth: 120 }}>Lot Name</th>
                <th>Slab</th>
                <th>Cost</th>
                <th>Collectr</th>
                <th>TCG Raw</th>
                <th>PC Raw</th>
                <th>PSA 8</th>
                <th>PSA 9</th>
                <th>PSA 10</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(card => (
                <tr key={card.id}>
                  <td style={{ fontWeight: 600, maxWidth: 220 }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={card.name}>
                      {card.name}
                    </div>
                  </td>
                  <td style={{ maxWidth: 200 }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={card.set_name}>
                      {card.set_name}
                    </div>
                  </td>
                  <td>{card.num || '—'}</td>
                  <td>
                    <span className="badge badge-purple" style={{ maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis' }} title={card.lot_name}>
                      {card.lot_name || 'Main Lot'}
                    </span>
                  </td>
                  <td>{card.slab_grade ? <span className="badge badge-yellow">{card.slab_grade}</span> : <span className="text-muted">Raw</span>}</td>
                  <td className="text-warning">{fmt(card.cost_paid)}</td>
                  <td><span className="price-chip chip-tcg">{fmt(card.collectr)}</span></td>
                  <td><span className="price-chip chip-tcg">{fmt(card.tcgplayer)}</span></td>
                  <td><span className="price-chip chip-raw">{fmt(card.raw)}</span></td>
                  <td><span className="price-chip chip-psa8">{fmt(card.psa_8)}</span></td>
                  <td><span className="price-chip chip-psa9">{fmt(card.psa_9)}</span></td>
                  <td><span className="price-chip chip-psa10">{fmt(card.psa_10)}</span></td>
                  <td className="text-dim" style={{ fontSize: 11 }}>{card.last_updated ? card.last_updated.split(' ')[0] : '—'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button
                        className="btn btn-info btn-sm"
                        title="Re-price"
                        onClick={() => repriceCard(card)}
                        disabled={repricing.has(card.id)}
                      >
                        <RefreshCw size={12} className={repricing.has(card.id) ? 'spin' : ''} />
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        title="Delete"
                        onClick={() => deleteCard(card.id)}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
