(() => {
  'use strict';
  const root = document.getElementById('rescue-days');
  if (!root) return;
  const picker = document.getElementById('rescue-stream'), readout = document.getElementById('rescue-count');
  let data, selected = null;
  function render() {
    const stream = data.streams[picker.value]; root.replaceChildren();
    stream.daily.forEach((d, index) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'rescue-day';
      b.setAttribute('aria-pressed', String(selected === index));
      b.setAttribute('aria-label', `September ${19 + index}, ${d.count} captured candidates${d.partial ? ', partial date' : ''}`);
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', '0 0 120 120'); svg.setAttribute('aria-hidden', 'true');
      for (let i = 0; i < d.count; i++) {
        const columns = 4, x = 21 + i % columns * 25 + (Math.floor(i / columns) % 2 ? 2 : -2), y = 24 + Math.floor(i / columns) * 24;
        const stem = document.createElementNS(svg.namespaceURI, 'path');
        stem.setAttribute('d', `M${x},${y + 11} Q${x - 1},${y + 3} ${x},${y - 4} M${x - 3},${y - 5} a3,3 0 1,0 6,0 a3,3 0 1,0 -6,0`);
        stem.setAttribute('fill', 'none'); stem.setAttribute('stroke', '#234f9a'); stem.setAttribute('stroke-width', '1.8'); stem.setAttribute('stroke-linecap', 'round'); svg.append(stem);
      }
      b.append(svg);
      for (const [tag, text] of [['span', 'SEP ' + (19 + index)], ['strong', d.count], ['small', d.partial ? 'partial date' : 'full date']]) { const n = document.createElement(tag); n.textContent = text; b.append(n); }
      b.onclick = () => { selected = selected === index ? null : index; render(); root.children[index]?.focus(); }; root.append(b);
    });
    const label = picker.value === 'sarasota' ? 'Sarasota' : 'Charlotte County';
    readout.textContent = selected === null ? `${label} Rescue 1 · ${stream.total} captured alert candidates in this saved week.` : `September ${19 + selected} · ${stream.daily[selected].count} captured candidates${stream.daily[selected].partial ? ' in a partial date' : ''}. Select the date again to return to the whole week.`;
  }
  picker.onchange = () => { selected = null; render(); };
  fetch('/assets/rescue-one/counts.json', { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error('Snapshot unavailable'); return r.json(); }).then(value => {
    for (const key of ['sarasota', 'charlotte']) { const s = value.streams?.[key]; if (!s || s.daily?.length !== 8 || s.daily.some(d => !Number.isInteger(d.count) || d.count < 0) || s.daily.reduce((n, d) => n + d.count, 0) !== s.total) throw new Error('Invalid counts'); }
    data = value; render();
  }).catch(() => { readout.textContent = 'The saved aggregate study is temporarily unavailable. The private explorer remains available through the link.'; picker.disabled = true; });
})();
