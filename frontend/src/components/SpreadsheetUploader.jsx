import React, { useState, useRef, useCallback } from 'react';
import { Upload, RefreshCw, Plus, X, ChevronDown, ChevronUp, Zap } from 'lucide-react';

function fmt(v) {
  if (v == null || v === '' || isNaN(Number(v))) return '—';
  return '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function parseDollar(s) {
  if (!s) return null;
  const n = parseFloat(String(s).replace(/[$,]/g, '').trim());
  return isNaN(n) ? null : n;
}

export default function SpreadsheetUploader({ onSaved }) {
  const [cards, setCards]           = useState([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [saving, setSaving]         = useState(false);
  const [savedIds, setSavedIds]     = useState(new Set());
  const [defaultLot, setDefaultLot] = useState('Main Lot');

  // Progress bar for full reprice
  const [repricing, setRepricing]   = useState(false);
  const [repriceProgress, setRepriceProgress] = useState({ done: 0, total: 0 });
  const abortRef = useRef(false);

  const fileRef = useRef();

  // ──────────────────────────────────────────────
  // Upload & parse spreadsheet (no auto-pricing)
  // ──────────────────────────────────────────────
  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setError('');
    setCards([]);
    setSavedIds(new Set());

    const form = new FormData();
    form.append('file', file);
    form.append('lot_name', defaultLot);

    try {
      const res = await fetch('/api/upload-csv-preview', { method: 'POST', body: form });
      const data = await res.json();
      if (data.error) { setError(data.error); setLoading(false); return; }
      setCards(data.cards || []);
    } catch (e) {
      setError('Failed to upload file: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const updateCard = useCallback((idx, field, val) => {
    setCards(prev => prev.map((c, i) => i === idx ? { ...c, [field]: val } : c));
  }, []);

  const removeCard = (idx) => setCards(prev => prev.filter((_, i) => i !== idx));

  // ──────────────────────────────────────────────
  // Single card reprice
  // ──────────────────────────────────────────────
  const repriceCard = async (idx) => {
    const card = cards[idx];
    updateCard(idx, '_repricing', true);
    try {
      const res = await fetch('/api/reprice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: card.name, set_name: card.set_name, num: card.num }),
      });
      const data = await res.json();
      setCards(prev => prev.map((c, i) => {
        if (i !== idx) return c;
        return {
          ...c,
          raw:       data.raw       ?? c.raw,
          psa_8:     data.psa_8     ?? c.psa_8,
          psa_9:     data.psa_9     ?? c.psa_9,
          psa_10:    data.psa_10    ?? c.psa_10,
          tcgplayer: data.tcgplayer ?? c.tcgplayer,
          _repricing: false,
        };
      }));
    } catch (e) {
      updateCard(idx, '_repricing', false);
    }
  };

  // ──────────────────────────────────────────────
  // Full collection reprice (with delay + abort)
  // ──────────────────────────────────────────────
  const repriceAll = async () => {
    abortRef.current = false;
    setRepricing(true);
    setRepriceProgress({ done: 0, total: cards.length });

    for (let i = 0; i < cards.length; i++) {
      if (abortRef.current) break;
      const card = cards[i];

      // Skip cards that already have prices (preserve existing)
      const hasPrice = card.raw || card.psa_8 || card.psa_9 || card.psa_10 || card.tcgplayer;
      if (hasPrice) {
        setRepriceProgress({ done: i + 1, total: cards.length });
        continue;
      }

      updateCard(i, '_repricing', true);
      try {
        const res = await fetch('/api/reprice', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: card.name, set_name: card.set_name, num: card.num }),
        });
        const data = await res.json();
        setCards(prev => prev.map((c, idx) => {
          if (idx !== i) return c;
          return {
            ...c,
            raw:       data.raw       ?? c.raw,
            psa_8:     data.psa_8     ?? c.psa_8,
            psa_9:     data.psa_9     ?? c.psa_9,
            psa_10:    data.psa_10    ?? c.psa_10,
            tcgplayer: data.tcgplayer ?? c.tcgplayer,
            _repricing: false,
          };
        }));
      } catch {
        updateCard(i, '_repricing', false);
      }

      setRepriceProgress({ done: i + 1, total: cards.length });

      // Politeness delay (1.5 s)
      if (!abortRef.current) {
        await new Promise(r => setTimeout(r, 1500));
      }
    }

    setRepricing(false);
  };

  // ──────────────────────────────────────────────
  // Force reprice all (ignore existing prices)
  // ──────────────────────────────────────────────
  const forceRepriceAll = async () => {
    if (!window.confirm('This will overwrite ALL existing prices. Continue?')) return;
    abortRef.current = false;
    setRepricing(true);
    setRepriceProgress({ done: 0, total: cards.length });

    for (let i = 0; i < cards.length; i++) {
      if (abortRef.current) break;
      updateCard(i, '_repricing', true);
      try {
        const res = await fetch('/api/reprice', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: cards[i].name, set_name: cards[i].set_name, num: cards[i].num }),
        });
        const data = await res.json();
        setCards(prev => prev.map((c, idx) => {
          if (idx !== i) return c;
          return {
            ...c,
            raw:       data.raw       ?? c.raw,
            psa_8:     data.psa_8     ?? c.psa_8,
            psa_9:     data.psa_9     ?? c.psa_9,
            psa_10:    data.psa_10    ?? c.psa_10,
            tcgplayer: data.tcgplayer ?? c.tcgplayer,
            _repricing: false,
          };
        }));
      } catch {
        updateCard(i, '_repricing', false);
      }
      setRepriceProgress({ done: i + 1, total: cards.length });
      if (!abortRef.current) await new Promise(r => setTimeout(r, 1500));
    }

    setRepricing(false);
  };

  // ──────────────────────────────────────────────
  // Save cards to inventory
  // ──────────────────────────────────────────────
  const saveCard = async (idx) => {
    const card = cards[idx];
    try {
      const res = await fetch('/api/inventory/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: card.name,
          set_name: card.set_name,
          num: card.num,
          slab_grade: card.slab_grade || null,
          cost_paid: parseDollar(card.cost_paid),
          lot_name: card.lot_name || defaultLot,
          raw: card.raw,
          psa_8: card.psa_8,
          psa_9: card.psa_9,
          psa_10: card.psa_10,
          tcgplayer: card.tcgplayer,
          collectr: card.collectr,
        }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSavedIds(prev => new Set([...prev, idx]));
        if (onSaved) onSaved();
      }
    } catch (e) {}
  };

  const saveAll = async () => {
    setSaving(true);
    for (let i = 0; i < cards.length; i++) {
      if (!savedIds.has(i)) await saveCard(i);
    }
    setSaving(false);
  };

  // Drag handlers
  const onDrag = (e) => { e.preventDefault(); setDragActive(true); };
  const onDragLeave = () => setDragActive(false);
  const onDrop = (e) => { e.preventDefault(); setDragActive(false); handleFile(e.dataTransfer.files[0]); };

  const pct = repriceProgress.total > 0
    ? Math.round((repriceProgress.done / repriceProgress.total) * 100)
    : 0;

  return (
    <div className="fade-in" style={{ padding: '0 16px 24px' }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>📊 Spreadsheet Import</h1>
        <p className="text-muted" style={{ fontSize: 13, marginTop: 4 }}>
          Upload your Collectr CSV or Excel sheet. Existing prices from the spreadsheet will be preserved.
        </p>
      </div>

      {/* Default lot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <label style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Default Lot:</label>
        <input
          className="input"
          style={{ maxWidth: 260 }}
          value={defaultLot}
          onChange={e => setDefaultLot(e.target.value)}
          placeholder="Lot name..."
        />
      </div>

      {/* Dropzone */}
      <div
        className={`dropzone ${dragActive ? 'active' : ''}`}
        style={{ marginBottom: 20 }}
        onClick={() => fileRef.current?.click()}
        onDragOver={onDrag}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <RefreshCw size={36} className="spin" style={{ color: 'var(--primary)' }} />
            <p style={{ color: 'var(--primary)', fontWeight: 600 }}>Parsing spreadsheet…</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
            <Upload size={40} style={{ color: 'var(--primary)', opacity: 0.7 }} />
            <p style={{ fontWeight: 700, fontSize: 15 }}>Drop CSV / Excel here or click to browse</p>
            <p className="text-muted" style={{ fontSize: 12 }}>Supports Collectr exports, custom CSV, and XLSX</p>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'var(--danger-dim)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '12px 16px', color: 'var(--danger)', marginBottom: 16, fontSize: 13 }}>
          ⚠️ {error}
        </div>
      )}

      {/* Progress bar */}
      {repricing && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              Pricing {repriceProgress.done} / {repriceProgress.total} cards…
            </span>
            <button className="btn btn-danger btn-sm" onClick={() => { abortRef.current = true; }}>
              <X size={12} /> Stop
            </button>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: pct + '%' }} />
          </div>
          <p className="text-muted" style={{ fontSize: 11, marginTop: 4 }}>{pct}% complete — cards with existing prices are skipped</p>
        </div>
      )}

      {cards.length > 0 && (
        <>
          {/* Action bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
            <h2 style={{ fontWeight: 700, fontSize: 15 }}>
              Verify &amp; Review Spreadsheet Items ({cards.length})
            </h2>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn btn-info btn-sm" onClick={repriceAll} disabled={repricing || loading}>
                <RefreshCw size={12} className={repricing ? 'spin' : ''} />
                Price Missing
              </button>
              <button className="btn btn-warning btn-sm" onClick={forceRepriceAll} disabled={repricing || loading}>
                <Zap size={12} />
                Re-Price All
              </button>
              <button className="btn btn-success btn-sm" onClick={saveAll} disabled={saving || loading}>
                <Plus size={12} />
                Save All ({cards.length - savedIds.size})
              </button>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ minWidth: 160 }}>Card Name</th>
                  <th style={{ minWidth: 160 }}>Set Name</th>
                  <th style={{ minWidth: 60 }}>Card #</th>
                  <th style={{ minWidth: 160 }}>Lot Name</th>
                  <th style={{ minWidth: 80 }}>Slab/Grade</th>
                  <th style={{ minWidth: 80 }}>Cost Paid</th>
                  <th>Collectr</th>
                  <th>TCG Raw</th>
                  <th>PC Raw</th>
                  <th>PSA 8</th>
                  <th>PSA 9</th>
                  <th>PSA 10</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cards.map((card, idx) => (
                  <tr key={idx} style={{ opacity: savedIds.has(idx) ? 0.45 : 1 }}>
                    <td>
                      <input
                        className="input"
                        value={card.name || ''}
                        onChange={e => updateCard(idx, 'name', e.target.value)}
                        style={{ minWidth: 150 }}
                      />
                    </td>
                    <td>
                      <input
                        className="input"
                        value={card.set_name || ''}
                        onChange={e => updateCard(idx, 'set_name', e.target.value)}
                        style={{ minWidth: 150 }}
                      />
                    </td>
                    <td>
                      <input
                        className="input"
                        value={card.num || ''}
                        onChange={e => updateCard(idx, 'num', e.target.value)}
                        style={{ width: 60 }}
                      />
                    </td>
                    <td>
                      <input
                        className="input"
                        value={card.lot_name || defaultLot}
                        onChange={e => updateCard(idx, 'lot_name', e.target.value)}
                        style={{ minWidth: 150 }}
                      />
                    </td>
                    <td>
                      <input
                        className="input"
                        value={card.slab_grade || ''}
                        onChange={e => updateCard(idx, 'slab_grade', e.target.value)}
                        style={{ width: 75 }}
                        placeholder="CGC 9"
                      />
                    </td>
                    <td>
                      <input
                        className="input"
                        value={card.cost_paid != null ? card.cost_paid : ''}
                        onChange={e => updateCard(idx, 'cost_paid', e.target.value)}
                        style={{ width: 75 }}
                        placeholder="$0.00"
                      />
                    </td>
                    <td><span className="price-chip chip-tcg">{fmt(card.collectr)}</span></td>
                    <td><span className="price-chip chip-tcg">{fmt(card.tcgplayer)}</span></td>
                    <td><span className="price-chip chip-raw">{fmt(card.raw)}</span></td>
                    <td><span className="price-chip chip-psa8">{fmt(card.psa_8)}</span></td>
                    <td><span className="price-chip chip-psa9">{fmt(card.psa_9)}</span></td>
                    <td><span className="price-chip chip-psa10">{fmt(card.psa_10)}</span></td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        {savedIds.has(idx) ? (
                          <span className="badge badge-green">✓ Saved</span>
                        ) : (
                          <>
                            <button
                              className="btn btn-info btn-sm"
                              title="Re-price this card"
                              onClick={() => repriceCard(idx)}
                              disabled={card._repricing}
                            >
                              <RefreshCw size={12} className={card._repricing ? 'spin' : ''} />
                            </button>
                            <button
                              className="btn btn-success btn-sm"
                              title="Save to inventory"
                              onClick={() => saveCard(idx)}
                            >
                              <Plus size={12} />
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              title="Remove row"
                              onClick={() => removeCard(idx)}
                            >
                              <X size={12} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
