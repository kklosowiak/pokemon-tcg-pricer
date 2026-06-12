import React, { useMemo } from 'react';
import { TrendingUp, Package, DollarSign, Award, BarChart2, Layers } from 'lucide-react';

function fmt(v) {
  if (v == null || isNaN(v)) return '—';
  return '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function Dashboard({ inventory, lots }) {
  const stats = useMemo(() => {
    const totalCards = inventory.length;
    const totalCost = inventory.reduce((s, c) => s + (c.cost_paid || 0), 0);
    const totalRaw = inventory.reduce((s, c) => s + (c.tcgplayer || c.raw || 0), 0);
    const totalPsa10 = inventory.reduce((s, c) => s + (c.psa_10 || 0), 0);
    const graded = inventory.filter(c => c.slab_grade && c.slab_grade !== '—').length;

    // per-lot breakdown
    const lotMap = {};
    inventory.forEach(c => {
      const lot = c.lot_name || 'Main Lot';
      if (!lotMap[lot]) lotMap[lot] = { count: 0, cost: 0, raw: 0, psa10: 0 };
      lotMap[lot].count++;
      lotMap[lot].cost  += c.cost_paid || 0;
      lotMap[lot].raw   += c.tcgplayer || c.raw || 0;
      lotMap[lot].psa10 += c.psa_10 || 0;
    });

    return { totalCards, totalCost, totalRaw, totalPsa10, graded, lotMap };
  }, [inventory]);

  const statCards = [
    { label: 'Total Cards',    value: stats.totalCards,   color: 'var(--primary)', icon: Package,   fmt: v => v.toLocaleString() },
    { label: 'Total Cost',     value: stats.totalCost,    color: 'var(--warning)', icon: DollarSign, fmt },
    { label: 'TCG Raw Value',  value: stats.totalRaw,     color: 'var(--success)', icon: TrendingUp, fmt },
    { label: 'PSA 10 Upside',  value: stats.totalPsa10,   color: 'var(--info)',    icon: Award,      fmt },
    { label: 'Graded Slabs',   value: stats.graded,       color: 'var(--danger)',  icon: BarChart2,  fmt: v => v.toLocaleString() },
    { label: 'Active Lots',    value: Object.keys(stats.lotMap).length, color: 'var(--primary)', icon: Layers, fmt: v => v.toLocaleString() },
  ];

  return (
    <div className="fade-in" style={{ padding: '0 16px 24px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #fff, var(--primary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Portfolio Dashboard
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Overview of your entire Pokémon TCG portfolio
        </p>
      </div>

      {/* Stat Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14, marginBottom: 28 }}>
        {statCards.map(s => (
          <div key={s.label} className="stat-card glass-panel">
            <div className="flex items-center gap-2">
              <div style={{ width: 32, height: 32, background: s.color + '22', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <s.icon size={16} style={{ color: s.color }} />
              </div>
              <span className="stat-label">{s.label}</span>
            </div>
            <div className="stat-value" style={{ color: s.color }}>{s.fmt(s.value)}</div>
          </div>
        ))}
      </div>

      {/* Per-Lot Breakdown */}
      {Object.keys(stats.lotMap).length > 0 && (
        <div className="glass-panel" style={{ padding: 20 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14, color: 'var(--text)' }}>
            📦 Lot Breakdown
          </h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Lot Name</th>
                  <th>Cards</th>
                  <th>Cost Paid</th>
                  <th>TCG Raw Value</th>
                  <th>PSA 10 Upside</th>
                  <th>Raw Profit</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.lotMap).map(([lot, d]) => {
                  const profit = d.raw - d.cost;
                  return (
                    <tr key={lot}>
                      <td><span className="badge badge-purple">📦 {lot}</span></td>
                      <td style={{ fontWeight: 700 }}>{d.count}</td>
                      <td className="text-warning">{fmt(d.cost)}</td>
                      <td className="text-success">{fmt(d.raw)}</td>
                      <td className="text-info">{fmt(d.psa10)}</td>
                      <td style={{ color: profit >= 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 700 }}>
                        {profit >= 0 ? '+' : ''}{fmt(profit)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {inventory.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-dim)' }}>
          <Package size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
          <p style={{ fontSize: 15, fontWeight: 600 }}>No cards in inventory yet</p>
          <p style={{ fontSize: 13, marginTop: 6 }}>Use the Scanner or Spreadsheet tab to add cards</p>
        </div>
      )}
    </div>
  );
}
