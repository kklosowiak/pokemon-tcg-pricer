import React, { useState, useRef } from 'react';
import { Camera, Upload, RefreshCw, Plus, X } from 'lucide-react';

function fmt(v) {
  if (v == null || isNaN(v)) return '—';
  return '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function Scanner({ onSaved }) {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedIds, setSavedIds] = useState(new Set());
  const [lotName, setLotName] = useState('Main Lot');
  const fileRef = useRef();

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setError('');
    setCards([]);
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/api/upload-image', { method: 'POST', body: form });
      const data = await res.json();
      if (data.error) { setError(data.error); return; }
      setCards((data.cards || []).map(c => ({ ...c, lot_name: lotName })));
    } catch (e) {
      setError('Failed to upload image: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const updateCard = (idx, field, val) => {
    setCards(prev => prev.map((c, i) => i === idx ? { ...c, [field]: val } : c));
  };

  const removeCard = (idx) => setCards(prev => prev.filter((_, i) => i !== idx));

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
      if (data.raw !== undefined) updateCard(idx, 'raw', data.raw);
      if (data.psa_8 !== undefined) updateCard(idx, 'psa_8', data.psa_8);
      if (data.psa_9 !== undefined) updateCard(idx, 'psa_9', data.psa_9);
      if (data.psa_10 !== undefined) updateCard(idx, 'psa_10', data.psa_10);
      if (data.tcgplayer !== undefined) updateCard(idx, 'tcgplayer', data.tcgplayer);
    } catch (e) {}
    updateCard(idx, '_repricing', false);
  };

  const saveCard = async (idx) => {
    const card = cards[idx];
    setSaving(true);
    try {
      const res = await fetch('/api/inventory/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...card, lot_name: card.lot_name || lotName }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSavedIds(prev => new Set([...prev, idx]));
        if (onSaved) onSaved();
      }
    } catch (e) {}
    setSaving(false);
  };

  const saveAll = async () => {
    for (let i = 0; i < cards.length; i++) {
      if (!savedIds.has(i)) await saveCard(i);
    }
  };

  return (
    <div className="fade-in" style={{ padding: '0 16px 24px' }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>📷 Card Scanner</h1>
        <p className="text-muted" style={{ fontSize: 13, marginTop: 4 }}>
          Upload a photo of your cards — Gemini AI will identify and price them automatically.
        </p>
      </div>

      {/* Lot Name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <label style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Default Lot:</label>
        <input
          className="input"
          style={{ maxWidth: 260 }}
          value={lotName}
          onChange={e => setLotName(e.target.value)}
          placeholder="Lot name..."
        />
      </div>

      {/* Dropzone */}
      <div
        className="dropzone"
        style={{ marginBottom: 20 }}
        onClick={() => fileRef.current?.click()}
        onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
      >
        <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <RefreshCw size={36} className="spin" style={{ color: 'var(--primary)' }} />
            <p style={{ color: 'var(--primary)', fontWeight: 600 }}>Analyzing with Gemini AI…</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
            <Camera size={40} style={{ color: 'var(--primary)', opacity: 0.7 }} />
            <p style={{ fontWeight: 700, fontSize: 15 }}>Drop card photo here or click to upload</p>
            <p className="text-muted" style={{ fontSize: 12 }}>Supports JPG, PNG, HEIC</p>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'var(--danger-dim)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '12px 16px', color: 'var(--danger)', marginBottom: 16, fontSize: 13 }}>
          ⚠️ {error}
        </div>
      )}

      {cards.length > 0 && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontWeight: 700, fontSize: 15 }}>
              {cards.length} Card{cards.length !== 1 ? 's' : ''} Detected
            </h2>
            <button className="btn btn-success btn-sm" onClick={saveAll} disabled={saving}>
              <Plus size={14} /> Save All to Inventory
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ minWidth: 140 }}>Card Name</th>
                  <th style={{ minWidth: 140 }}>Set Name</th>
                  <th style={{ minWidth: 60 }}>Card #</th>
                  <th style={{ minWidth: 120 }}>Lot Name</th>
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
                  <tr key={idx} style={{ opacity: savedIds.has(idx) ? 0.5 : 1 }}>
                    <td>
                      <input className="input" value={card.name || ''} onChange={e => updateCard(idx, 'name', e.target.value)} style={{ minWidth: 130 }} />
                    </td>
                    <td>
                      <input className="input" value={card.set_name || ''} onChange={e => updateCard(idx, 'set_name', e.target.value)} style={{ minWidth: 130 }} />
                    </td>
                    <td>
                      <input className="input" value={card.num || ''} onChange={e => updateCard(idx, 'num', e.target.value)} style={{ width: 60 }} />
                    </td>
                    <td>
                      <input className="input" value={card.lot_name || lotName} onChange={e => updateCard(idx, 'lot_name', e.target.value)} style={{ minWidth: 110 }} />
                    </td>
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
                            <button className="btn btn-info btn-sm" onClick={() => repriceCard(idx)} disabled={card._repricing}>
                              <RefreshCw size={12} className={card._repricing ? 'spin' : ''} />
                            </button>
                            <button className="btn btn-success btn-sm" onClick={() => saveCard(idx)} disabled={saving}>
                              <Plus size={12} />
                            </button>
                            <button className="btn btn-danger btn-sm" onClick={() => removeCard(idx)}>
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
