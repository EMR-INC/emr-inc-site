/* ==========================================================================
   DISPATCH VIEWS  ·  dispatch-views.html
   Draws data/dispatch-views.json. Six figures, no charting library, no build
   step, no dependency of any kind.

   THE ONE RULE: not a single number is written in this file or in the HTML.
   Every value, axis tick, sample count and caption figure is read from the
   JSON at runtime. The JSON is built by data/build-dispatch-views.py from
   data/dispatch-events.csv, which is the file the open data page publishes, so
   a reader can reproduce every mark on the page from a public download. Typing
   a statistic into this file breaks that chain silently, which is the worst way
   for it to break.

   COLOUR CARRIES NOTHING QUANTITATIVE. design_system.md is explicit that value
   carries magnitude and hue never does, so magnitude is length in the flat
   figures and height in the surface, and the surface blocks are a single
   colour. The two navy shades on a block are lighting, identical on every
   block, not a second reading of the data. beam/500 already means "invalid
   code" elsewhere in this stylesheet and is not used as a data mark here.

   Geometry is in the viewBox and is fixed there. Ink is in styles.css section
   10c. Nothing in this file sets a colour.

   EVERY EDITION LOOKS DIFFERENT, AND NONE OF IT IS RANDOM. doc.composition
   carries a camera angle, an elevation, a lighting direction, a mark shape for
   the nights figure, a sort order for the ranked bars and a section order, all
   derived from the build date by build-dispatch-views.py. A Math.random() here
   would be one line shorter and would quietly end the page's reproducibility,
   because two readers would get two drawings of one file while the page went on
   claiming they could reproduce it. Seeded from the date, anyone can.

   The line between the two kinds of choice is the thing to hold: COMPOSITION
   VARIES, ENCODING NEVER DOES. The seed may move the camera and reorder the
   page. It may not decide that height means something else this week. If a new
   axis of variation would change what a reader concludes from a figure, it is
   not composition and does not belong in the table.
   ========================================================================== */
(function () {
  'use strict';

  var SRC = 'data/dispatch-views.json';
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  /* ---- formatting ------------------------------------------------------ */
  /* Thousands separators always, per design_system.md. Plex Mono is applied by
     the stylesheet and is tabular, so columns of these line up. */
  function fmt(n) { return Number(n).toLocaleString('en-US'); }
  function dec(n, p) {
    return Number(n).toLocaleString('en-US',
      { minimumFractionDigits: p, maximumFractionDigits: p });
  }
  function pct(share, p) { return dec(share * 100, p) + '%'; }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  /* Dates arrive as plain ISO dates. new Date() on one of those parses as UTC
     and then prints in the viewer's zone, which silently shifts every label
     back a day for anyone west of Greenwich. Split the string instead. */
  function shortDate(iso) {
    var p = iso.slice(0, 10).split('-');
    return MON[+p[1] - 1] + ' ' + (+p[2]);
  }
  function longDate(iso) {
    var p = iso.slice(0, 10).split('-');
    return MON[+p[1] - 1] + ' ' + (+p[2]) + ', ' + p[0];
  }
  function hourLabel(h) { return (h < 10 ? '0' : '') + h + ':00'; }

  function fig(name) { return document.querySelector('[data-fig="' + name + '"]'); }
  function svgFor(name) { return document.querySelector('[data-draw="' + name + '"]'); }

  /* An axis that ends on a round number, with four or five ticks. */
  function niceScale(max) {
    var steps = [0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50,
                 100, 200, 250, 500, 1000, 2000, 2500, 5000];
    for (var i = 0; i < steps.length; i++) {
      var top = Math.ceil(max / steps[i]) * steps[i];
      if (top / steps[i] <= 5) return { top: top, step: steps[i] };
    }
    return { top: max, step: max / 4 };
  }

  /* ---- svg primitives, as strings -------------------------------------- */
  function pt(p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }
  function poly(cls, pts) {
    return '<polygon class="' + cls + '" points="' + pts.map(pt).join(' ') + '"/>';
  }
  function seg(cls, a, b) {
    return '<line class="' + cls + '" x1="' + a[0].toFixed(1) + '" y1="' +
           a[1].toFixed(1) + '" x2="' + b[0].toFixed(1) + '" y2="' +
           b[1].toFixed(1) + '"/>';
  }
  function rect(cls, x, y, w, h) {
    return '<rect class="' + cls + '" x="' + x.toFixed(1) + '" y="' + y.toFixed(1) +
           '" width="' + Math.max(0, w).toFixed(1) + '" height="' +
           Math.max(0, h).toFixed(1) + '"/>';
  }
  function txt(cls, x, y, s) {
    return '<text class="' + cls + '" x="' + x.toFixed(1) + '" y="' + y.toFixed(1) +
           '">' + esc(s) + '</text>';
  }

  /* ---- html primitives ------------------------------------------------- */
  function rowsInto(host, pairs) {
    if (!host) return;
    host.innerHTML = pairs.map(function (p) {
      return '<div class="row"><p class="t-data row__key">' + esc(p[0]) +
             '</p><p class="t-body">' + p[1] + '</p></div>';
    }).join('');
  }
  function legendInto(host, keys) {
    if (!host) return;
    host.innerHTML = keys.map(function (k) {
      return '<p class="viz__key"><span class="swatch ' + k[0] + '"></span>' +
             esc(k[1]) + '</p>';
    }).join('');
  }
  function caption(name, parts) {
    var host = fig(name);
    if (host) host.textContent = parts.filter(Boolean).join(' ');
  }

  /* ======================================================================
     1 · THE SURFACE
     Day of week by hour of day, as blocks standing on a ground plane.

     Height is the rate, not the count. A sixty four day window does not hold
     equal numbers of each weekday, so each row is divided by its own
     days_observed. Drawing the raw counts would put ridges on whichever
     weekdays the window happened to contain one more of, and those ridges
     would look exactly like demand.

     Painter's algorithm: every block is sorted by its depth along the view
     direction and the near ones are drawn last. There is no z buffer in SVG,
     so draw order IS the occlusion. Only the two side faces whose outward
     normal points toward the viewer are emitted; the other two are always
     hidden and drawing them costs 336 polygons for nothing.
     ================================================================== */
  var surfaceState = null;

  /* Lighting directions, one per edition. These are vectors on the ground
     plane, and a side face reads as lit when its outward normal points with
     the light rather than against it.

     They are deliberately off axis. A light of exactly (-1, 0) puts a dot
     product of zero on the two faces at right angles to it, which would leave
     those faces neither lit nor shaded and would flatten the figure at some
     camera angles. Tilting each vector a little guarantees every visible face
     lands on one side or the other.

     This is lighting and only lighting. The value a face gets depends on which
     way the face points, never on how tall the block is, so the shading cannot
     be read as a second encoding of the data on top of the height. */
  var LIGHTS = {
    left:  [-0.92,  0.38],
    right: [ 0.92,  0.38],
    front: [ 0.38,  0.92],
    back:  [ 0.38, -0.92]
  };

  function drawSurface(deg) {
    var st8 = surfaceState;
    if (!st8) return;
    var s = st8.s, rate = st8.rate, scale = st8.scale, dows = s.days_of_week;
    var comp = st8.comp;
    var svg = svgFor('surface');

    var TH = deg * Math.PI / 180;
    var ct = Math.cos(TH), stn = Math.sin(TH);
    var light = LIGHTS[comp.lighting] || LIGHTS.left;

    /* Centre, half widths and the height of a full scale block. SY is already
       the foreshortened depth: the ground plane is squashed rather than
       genuinely perspective projected, which keeps every block the same size
       and so keeps height comparable across the whole figure. A real
       perspective would make the near Sunday blocks taller than identical
       Monday ones, which would be a lie told by the projection.

       Elevation is the edition's, so the plane is flatter or steeper from one
       build to the next, and the frame has to follow it.

       THE PLANE IS DEEPER THAN IT LOOKS. A corner at (1, 1) projects to
       (sin + cos) * SY, and sin + cos peaks at root two, not at one, when the
       camera is near forty five degrees. Sizing the frame to 2 * SY is the
       obvious arithmetic and it is wrong by forty per cent at the worst angle:
       it clipped the near row clean off the bottom at the steeper elevations.
       The extent is 2 * root two * SY, so that is what the viewBox gets, plus
       the block height above the far corner and the hour labels below the near
       one. Height is recomputed per edition rather than fixed in the markup,
       which also means a flat edition does not carry a band of dead space. */
    var CX = 434, SX = 276, ZH = 234;
    var SY = SX * comp.elevation;
    var DEEP = Math.SQRT2 * SY;        /* half depth of the plane, worst case */
    var PAD = 20, LABEL = 19;
    var VH = Math.ceil(2 * DEEP + ZH + LABEL + 2 * PAD);
    var CY = DEEP + ZH + PAD;
    svg.setAttribute('viewBox', '0 0 960 ' + VH);
    function P(x, y, z) {
      return [CX + (x * ct - y * stn) * SX,
              CY + (x * stn + y * ct) * SY - z * ZH];
    }
    function depth(x, y) { return x * stn + y * ct; }

    function hx(h) { return h / 24 * 2 - 1; }
    function dyv(i) { return i / 7 * 2 - 1; }
    var GX = (2 / 24) * 0.13, GY = (2 / 7) * 0.13;

    var out = [];

    /* ground plane and its grid */
    out.push(poly('sur-ground', [P(-1, -1, 0), P(1, -1, 0), P(1, 1, 0), P(-1, 1, 0)]));
    for (var i = 0; i <= 7; i++) {
      out.push(seg('sur-grid', P(-1, dyv(i), 0), P(1, dyv(i), 0)));
    }
    for (var h = 0; h <= 24; h += 6) {
      out.push(seg('sur-grid', P(hx(h), -1, 0), P(hx(h), 1, 0)));
    }

    /* the vertical scale, at the left hand corner of the plane. For every
       rotation in the slider's range that corner is the leftmost point of the
       figure, so the ruler is never buried inside the blocks. */
    var RX = -1, RY = 1;
    out.push(seg('sur-axis', P(RX, RY, 0), P(RX, RY, 1)));
    for (var v = 0; v <= scale.top + 1e-9; v += scale.step) {
      var p = P(RX, RY, v / scale.top);
      out.push(seg('sur-axis', p, [p[0] - 7, p[1]]));
      out.push(txt('sur-tick sur-tick--end', p[0] - 11, p[1] + 4, dec(v, 1)));
    }
    out.push(txt('sur-eyebrow', 16, 24, 'TRANSMISSIONS PER DAY OBSERVED'));

    /* hour labels on the near edge, day labels on the right edge */
    for (h = 0; h < 24; h += 3) {
      var ph = P(hx(h) + 1 / 24, 1, 0);
      out.push(txt('sur-tick', ph[0], ph[1] + 19, hourLabel(h)));
    }
    for (i = 0; i < 7; i++) {
      var pd = P(1, dyv(i) + 1 / 7, 0);
      out.push(txt('sur-day', pd[0] + 13, pd[1] + 5, dows[i].slice(0, 3)));
    }

    /* the blocks */
    var cells = [];
    for (i = 0; i < 7; i++) {
      for (h = 0; h < 24; h++) {
        cells.push({
          d: i, h: h, v: rate[i][h], c: s.grid[i][h],
          x0: hx(h) + GX, x1: hx(h + 1) - GX,
          y0: dyv(i) + GY, y1: dyv(i + 1) - GY
        });
      }
    }
    cells.forEach(function (c) {
      c.z = scale.top ? c.v / scale.top : 0;
      c.depth = depth((c.x0 + c.x1) / 2, (c.y0 + c.y1) / 2);
    });
    cells.sort(function (a, b) { return a.depth - b.depth; });

    cells.forEach(function (c) {
      var tag = ' data-d="' + c.d + '" data-h="' + c.h + '"';
      var topFace = [P(c.x0, c.y0, c.z), P(c.x1, c.y0, c.z),
                     P(c.x1, c.y1, c.z), P(c.x0, c.y1, c.z)];
      /* A measured zero is a tile on the plane, not an absence. Every hour of
         every weekday was observed, so a zero here means nobody called, and
         that is a finding rather than a hole. */
      if (c.z <= 0) {
        out.push('<polygon class="sur-zero"' + tag + ' points="' +
                 topFace.map(pt).join(' ') + '"/>');
        return;
      }
      var g = ['<g class="sur-cell"' + tag + '>'];
      [[1, 0, [c.x1, c.y0], [c.x1, c.y1]],
       [-1, 0, [c.x0, c.y0], [c.x0, c.y1]],
       [0, 1, [c.x0, c.y1], [c.x1, c.y1]],
       [0, -1, [c.x0, c.y0], [c.x1, c.y0]]].forEach(function (f) {
        if (f[0] * stn + f[1] * ct <= 0) return;   /* faces away, never seen */
        var a = f[2], b = f[3];
        /* Lit or shaded by which way the face points, not by how tall it is. */
        var cls = (f[0] * light[0] + f[1] * light[1]) > 0
          ? 'sur-side' : 'sur-side--dim';
        g.push(poly(cls, [P(a[0], a[1], c.z), P(b[0], b[1], c.z),
                          P(b[0], b[1], 0), P(a[0], a[1], 0)]));
      });
      g.push(poly('sur-top', topFace));
      g.push('</g>');
      out.push(g.join(''));
    });

    svg.innerHTML = out.join('');
  }

  function surfaceReadout(d, h) {
    var st8 = surfaceState;
    var s = st8.s;
    fig('surface-readout').textContent =
      s.days_of_week[d] + ' ' + hourLabel(h) + '  \u00b7  ' +
      dec(st8.rate[d][h], 2) + ' ' + s.unit + '  \u00b7  ' +
      fmt(s.grid[d][h]) + ' transmissions over ' + fmt(s.days_observed[d]) +
      ' ' + s.days_of_week[d] + 's observed';
  }

  function initSurface(doc) {
    var s = doc.demand_surface;
    var rate = s.grid.map(function (row, i) {
      return row.map(function (c) { return s.days_observed[i] ? c / s.days_observed[i] : 0; });
    });
    var max = 0;
    rate.forEach(function (r) { r.forEach(function (v) { if (v > max) max = v; }); });
    surfaceState = { s: s, rate: rate, scale: niceScale(max), comp: doc.composition };

    /* The edition sets where the camera starts. The slider still spans its
       whole range from there, so nothing an edition chooses takes a view away
       from the reader; it only decides which one they are handed first. */
    var slider = document.getElementById('surface-rotate');
    slider.value = doc.composition.azimuth;
    drawSurface(+slider.value);
    /* Direct manipulation, redrawn synchronously. No transition, so this is
       not one of the page's four motions and it respects reduced motion by
       having no motion to reduce. */
    slider.addEventListener('input', function () { drawSurface(+slider.value); });

    var svg = svgFor('surface');
    var hot = null;
    function hit(e) {
      var el = e.target.closest ? e.target.closest('[data-d]') : null;
      if (!el || el === hot) return;
      if (hot) hot.classList.remove('is-hot');
      hot = el;
      hot.classList.add('is-hot');
      surfaceReadout(+el.getAttribute('data-d'), +el.getAttribute('data-h'));
    }
    svg.addEventListener('mousemove', hit);
    svg.addEventListener('touchstart', function (e) {
      if (e.touches && e.touches.length === 1) hit({ target: e.target });
    }, { passive: true });

    /* The readout starts on the peak rather than empty, so the figure says
       something before it is touched and on a device with no hover at all. */
    var peaks = flatPeaks(s, rate);
    surfaceReadout(peaks[0].d, peaks[0].h);

    rowsInto(fig('surface-peaks'), peaks.slice(0, 6).map(function (c) {
      return [s.days_of_week[c.d] + ' ' + hourLabel(c.h),
              '<strong>' + dec(c.v, 2) + '</strong> ' + esc(s.unit) +
              '. ' + fmt(c.c) + ' transmissions over ' +
              fmt(s.days_observed[c.d]) + ' days observed.'];
    }));

    var w = doc.window;
    caption('surface-caption', [
      s.title + '.', 'Height is ' + s.unit + '.',
      'n = ' + fmt(s.n) + ' transmissions,',
      longDate(w.first_local) + ' to ' + longDate(w.last_local) + ',',
      fmt(w.days) + ' days, ' + w.timezone + '.',
      s.note
    ]);
  }

  function flatPeaks(s, rate) {
    var all = [];
    for (var i = 0; i < 7; i++) {
      for (var h = 0; h < 24; h++) {
        all.push({ d: i, h: h, v: rate[i][h], c: s.grid[i][h] });
      }
    }
    return all.sort(function (a, b) { return b.v - a.v; });
  }

  /* ======================================================================
     2 · HOUR PROFILE AGAINST THE FLORIDA NFIRS RECORD
     Shares, because the denominators are four orders of magnitude apart.
     Both denominators are printed in the caption so the shares can be turned
     back into counts by anyone who wants to.
     ================================================================== */
  function drawHours(doc) {
    var hp = doc.hour_profile;
    var L = 82, R = 930, T = 48, B = 338;
    var max = 0;
    hp.by_hour.forEach(function (r) {
      max = Math.max(max, r.ohpah_share, r.nfirs_share);
    });
    var scale = niceScale(max * 100);
    function X(h) { return L + (h + 0.5) / 24 * (R - L); }
    function Y(share) { return B - (share * 100 / scale.top) * (B - T); }

    var out = [];
    for (var v = 0; v <= scale.top + 1e-9; v += scale.step) {
      var y = Y(v / 100);
      out.push(seg(v === 0 ? 'viz-zero' : 'viz-grid-line', [L, y], [R, y]));
      out.push(txt('sur-tick sur-tick--end', L - 12, y + 4, dec(v, 1) + '%'));
    }
    out.push(txt('sur-eyebrow', 16, 24, 'SHARE OF ALL INCIDENTS, BY HOUR'));

    for (var h = 0; h < 24; h += 2) {
      out.push(txt('sur-tick', X(h), B + 24, hourLabel(h)));
    }

    out.push('<polyline class="ser-nfirs" points="' + hp.by_hour.map(function (r) {
      return pt([X(r.hour), Y(r.nfirs_share)]);
    }).join(' ') + '"/>');
    out.push('<polyline class="ser-ohpah" points="' + hp.by_hour.map(function (r) {
      return pt([X(r.hour), Y(r.ohpah_share)]);
    }).join(' ') + '"/>');
    hp.by_hour.forEach(function (r) {
      out.push('<circle class="dot-ohpah" cx="' + X(r.hour).toFixed(1) + '" cy="' +
               Y(r.ohpah_share).toFixed(1) + '" r="2.6"/>');
    });

    svgFor('hours').innerHTML = out.join('');

    legendInto(fig('hours-legend'), [
      ['sw-ohpah', 'OHPAH capture, n = ' + fmt(hp.ohpah_n) + ' transmissions'],
      ['sw-nfirs', 'Florida NFIRS, n = ' + fmt(hp.nfirs_n) + ' incidents']
    ]);
    caption('hours-caption', [
      hp.title + '.', 'Unit is ' + hp.unit + '.',
      'Baseline years ' + hp.nfirs_years + '.',
      hp.nfirs_source + '.', hp.nfirs_scope
    ]);
  }

  /* ======================================================================
     3 · THE NIGHTS
     One bar per night, every night, never averaged.

     A night the receiver heard nothing at all is drawn as absent, not as a
     full length gap. Those two are indistinguishable from inside the file and
     the restful reading is the flattering one, so it does not get the benefit
     of the doubt.
     ================================================================== */
  function drawNights(doc) {
    var ov = doc.overnight;
    var L = 74, R = 930, T = 48, B = 262;
    var nights = ov.by_night;
    var max = 0;
    nights.forEach(function (n) {
      if (n.longest_gap_min != null) max = Math.max(max, n.longest_gap_min);
    });
    /* Minutes read in hours, so the axis steps in hours whatever the data. */
    var top = Math.max(60, Math.ceil(max / 60) * 60), step = 60;
    var W = (R - L) / nights.length;
    function Y(m) { return B - (m / top) * (B - T); }

    var out = [];
    for (var v = 0; v <= top + 1e-9; v += step) {
      var y = Y(v);
      out.push(seg(v === 0 ? 'viz-zero' : 'viz-grid-line', [L, y], [R, y]));
      if (v % 120 === 0) {
        out.push(txt('sur-tick sur-tick--end', L - 12, y + 4, fmt(v)));
      }
    }
    out.push(txt('sur-eyebrow', 16, 24, 'MINUTES, LONGEST UNBROKEN GAP'));

    /* Three mark shapes, one per edition. All three draw the same sixty four
       numbers and none of them aggregates: the figure is a distribution and
       stays one whatever it is drawn with.

       The absence stub is identical in all three. A night the receiver heard
       nothing is never drawn as a tall bar, a tall stem or a high step,
       because that would read as a long restful gap, and a quiet night and a
       deaf receiver are indistinguishable from inside the file. The steps
       variant additionally BREAKS its line at those nights rather than running
       through them, since a continuous line across a hole asserts a value
       that was never measured. */
    var mark = (doc.composition || {}).night_mark || 'bars';
    var prevY = null;
    nights.forEach(function (n, i) {
      var x = L + i * W;
      if (n.capture_gap) {
        out.push(rect('bar-gap', x + 1, B - 7, W - 2, 7));
        prevY = null;                 /* break the line, never bridge the hole */
        return;
      }
      var y = Y(n.longest_gap_min);
      if (mark === 'stems') {
        out.push(seg('stem-night', [x + W / 2, B], [x + W / 2, y]));
        out.push('<circle class="stem-head" cx="' + (x + W / 2).toFixed(1) +
                 '" cy="' + y.toFixed(1) + '" r="2.8"/>');
      } else if (mark === 'steps') {
        if (prevY !== null) out.push(seg('step-night', [x, prevY], [x, y]));
        out.push(seg('step-night', [x, y], [x + W, y]));
        prevY = y;
      } else {
        out.push(rect('bar-night', x + 1, y, W - 2, B - y));
      }
    });

    nights.forEach(function (n, i) {
      if (i % 7) return;
      out.push(txt('sur-tick', L + i * W + W / 2, B + 24, shortDate(n.night)));
    });

    svgFor('nights').innerHTML = out.join('');

    legendInto(fig('nights-legend'), [
      ['sw-night', 'Longest unbroken gap, ' + ov.window_local + ' local'],
      ['sw-gap', 'Receiver heard nothing that day, ' +
                 fmt(ov.nights_capture_gap) + ' of ' + fmt(ov.nights) + ' nights']
    ]);
    caption('nights-caption', [
      ov.title + '.', 'Unit is ' + ov.unit + '.',
      'n = ' + fmt(ov.nights) + ' nights, ' + fmt(ov.nights_with_capture) +
        ' of them with capture.',
      'Window from ' + ov.window_source + '.', ov.note
    ]);
  }

  /* ======================================================================
     4 · NATURE COMPOSITION
     The distinct spelling count sits next to each group because it is the
     honest measure of how soft the grouping is. Unclassified is drawn at full
     length and marked as not a category, because it is the largest single
     statement this field makes about itself.
     ================================================================== */
  /* Ranked bars are shown either biggest first or alphabetically, by edition.
     Both are honest orderings of the same set and each answers a different
     question: by value tells you what dominates, alphabetically lets you find
     the one you came for. The set itself never changes, so an alphabetical
     edition is still exactly the top twenty and the caption still says so.
     Sorting a copy, because the JSON is shared with the captions. */
  function ranked(rows, key, order) {
    var copy = rows.slice();
    if (order === 'alpha') {
      copy.sort(function (a, b) { return String(a[key]).localeCompare(String(b[key])); });
    }
    return copy;
  }

  function drawNature(doc) {
    var n = doc.nature;
    var groups = ranked(n.groups, 'group', (doc.composition || {}).rank_order);
    var LBL = 200, L = 216, R = 812, T = 54, RH = 42;
    var max = 0;
    groups.forEach(function (g) { max = Math.max(max, g.count); });
    var scale = niceScale(max);
    function X(c) { return L + (c / scale.top) * (R - L); }

    var out = [];
    out.push(txt('sur-eyebrow', 16, 24, 'TRANSMISSIONS'));
    for (var v = 0; v <= scale.top + 1e-9; v += scale.step) {
      var x = X(v);
      out.push(seg(v === 0 ? 'viz-zero' : 'viz-grid-line',
                   [x, T - 14], [x, T + groups.length * RH - 12]));
      out.push(txt('sur-tick', x, T + groups.length * RH + 8, fmt(v)));
    }

    groups.forEach(function (g, i) {
      var y = T + i * RH;
      var soft = g.group === 'Unclassified';
      out.push(txt('viz-cat', LBL, y + 2, g.group));
      out.push(txt('viz-cat--sub sur-tick--end', LBL, y + 19,
                   fmt(g.distinct_spellings) + ' spellings'));
      out.push(rect(soft ? 'bar-soft' : 'bar-nature', L, y - 11, X(g.count) - L, 20));
      out.push(txt('viz-pt', X(g.count) + 10, y + 3, fmt(g.count)));
    });

    svgFor('nature').innerHTML = out.join('');

    caption('nature-caption', [
      n.title + '.', 'Unit is ' + n.unit + '.',
      'n = ' + fmt(n.n_with_nature) + ' transmissions carried a nature, ' +
        fmt(n.n_without_nature) + ' did not,',
      'across ' + fmt(n.distinct_raw_values) + ' distinct raw spellings.',
      n.note
    ]);
  }

  /* ======================================================================
     5 · UNIT WORKLOAD
     Unit is the finest grain allowed on this page. Transmissions rather than
     incidents, because a unit is heard more than once on a call and the
     incident key is blank on a large share of rows.
     ================================================================== */
  function drawUnits(doc) {
    var u = doc.units;
    var top20 = ranked(u.top, 'unit', (doc.composition || {}).rank_order);
    var LBL = 150, L = 166, R = 812, T = 54, RH = 34;
    var max = 0;
    top20.forEach(function (r) { max = Math.max(max, r.count); });
    var scale = niceScale(max);
    function X(c) { return L + (c / scale.top) * (R - L); }

    var out = [];
    out.push(txt('sur-eyebrow', 16, 24, 'TRANSMISSIONS'));
    for (var v = 0; v <= scale.top + 1e-9; v += scale.step) {
      var x = X(v);
      out.push(seg(v === 0 ? 'viz-zero' : 'viz-grid-line',
                   [x, T - 14], [x, T + top20.length * RH - 12]));
      out.push(txt('sur-tick', x, T + top20.length * RH + 8, fmt(v)));
    }

    top20.forEach(function (r, i) {
      var y = T + i * RH;
      out.push(txt('viz-cat', LBL, y + 4, r.unit));
      out.push(rect('bar-unit', L, y - 8, X(r.count) - L, 16));
      out.push(txt('viz-pt', X(r.count) + 10, y + 5, fmt(r.count)));
    });

    svgFor('units').innerHTML = out.join('');

    caption('units-caption', [
      u.title + '.', 'Unit is ' + u.unit + '.',
      'Showing the ' + fmt(top20.length) + ' most heard of ' + fmt(u.distinct) +
        ' distinct units,',
      'n = ' + fmt(u.n) + ' transmissions that carried a unit.',
      u.note
    ]);
  }

  /* ======================================================================
     6 · THE STAMP AND THE DENOMINATORS
     ================================================================== */
  function drawStamp(doc) {
    var w = doc.window, c = doc.composition;
    rowsInto(fig('stamp'), [
      ['Window', longDate(w.first_local) + ' to ' + longDate(w.last_local) +
                 '. ' + fmt(w.days) + ' days, ' + w.timezone + '.'],
      ['Read', fmt(w.transmissions) + ' transmissions'],
      ['Built', longDate(doc.built) + '. Rebuilt ' + esc(doc.cadence) + '.'],
      ['Edition', fmt(c.edition) + ', drawn from ' + esc(c.seed) +
                  '. Camera ' + fmt(c.azimuth) + '\u00b0, lit from the ' +
                  esc(c.lighting) + '.'],
      ['From', '<code>' + esc(doc.source) + '</code>'],
      ['Grain', esc(doc.grain)]
    ]);
    var note = fig('edition-note');
    if (note) note.textContent = c.note;
  }

  /* ======================================================================
     7 · THE EDITION
     The page is rebuilt three times a week and is drawn differently every
     time. This moves the sections, renumbers them and reassigns the light and
     dark banding, so nothing about the order is written into the markup.

     Say so on the page. A layout that changes on its own, silently, invites a
     returning reader to think the data moved when only the camera did, and a
     figure that misleads by its framing is no better than one that misleads by
     its numbers. The stamp prints the edition and the date it came from, so
     the change is declared and checkable rather than merely noticed.

     The closing section stays last in every edition. It is the one that says
     what the file is not, and that argument only lands after the figures it
     qualifies; rotating it into the lead would turn the page's own caveat into
     its opening claim.
     ================================================================== */
  function arrange(doc) {
    var order = { surface:  ['surface', 'baseline', 'nights'],
                  baseline: ['baseline', 'surface', 'nights'],
                  nights:   ['nights', 'surface', 'baseline'] };
    var lead = order[(doc.composition || {}).flow] || order.surface;
    var names = lead.concat(['composition', 'denominators']);

    var nodes = {}, anchor = null;
    names.forEach(function (name) {
      nodes[name] = document.querySelector('[data-section="' + name + '"]');
      if (nodes[name] && !anchor) anchor = nodes[name].parentNode;
    });
    if (!anchor) return;

    names.forEach(function (name, i) {
      var el = nodes[name];
      if (!el) return;
      anchor.insertBefore(el, document.querySelector('.footer'));
      /* Banding alternates down the page as ordered, not as authored, so the
         sections never end up two whites deep after a swap. */
      el.classList.remove('field-white', 'field-ivory');
      el.classList.add(i % 2 ? 'field-ivory' : 'field-white');
      var num = fig('num-' + name);
      if (num) {
        num.textContent = (i + 1 < 10 ? '0' : '') + (i + 1);
        num.style.color = 'var(--steel-400)';
      }
    });
  }

  function drawCapture(doc) {
    var c = doc.capture;
    var n = c.transmissions;
    function withPct(k) {
      return fmt(c[k]) + ' of ' + fmt(n) + ' rows, ' + pct(c[k] / n, 1);
    }
    var status = Object.keys(c.status).sort(function (a, b) {
      return c.status[b] - c.status[a];
    }).map(function (k) {
      return esc(k) + ' ' + fmt(c.status[k]);
    }).join(' \u00b7 ');

    rowsInto(fig('capture-rows'), [
      ['Transmissions', fmt(c.transmissions) + ' over ' + fmt(c.days) +
                        ' days, ' + dec(c.transmissions_per_day, 1) + ' per day'],
      ['Incidents', fmt(c.incidents) + ', ' + dec(c.incidents_per_day, 1) +
                    ' per day. Grouped by <code>incident_key</code>.'],
      ['No incident key', fmt(c.rows_without_incident_key) + ' of ' + fmt(n) +
                          ' rows, ' + pct(c.rows_without_incident_key / n, 1) +
                          '. These cannot be grouped into an incident at all.'],
      ['Carried a unit', withPct('with_unit')],
      ['Carried a nature', withPct('with_nature')],
      ['Carried a severity', withPct('with_severity')],
      ['Carried a street', withPct('with_street')],
      ['Distinct units', fmt(c.distinct_units)],
      ['Match status', status]
    ]);
    var note = fig('capture-note');
    if (note) note.textContent = c.note;
  }

  /* ---- boot ------------------------------------------------------------ */
  function fail(message) {
    ['surface-caption', 'hours-caption', 'nights-caption',
     'nature-caption', 'units-caption'].forEach(function (name) {
      var host = fig(name);
      if (host) host.textContent = message;
    });
  }

  fetch(SRC, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error(r.status + ' on ' + SRC);
      return r.json();
    })
    .then(function (doc) {
      arrange(doc);
      drawStamp(doc);
      initSurface(doc);
      drawHours(doc);
      drawNights(doc);
      drawNature(doc);
      drawUnits(doc);
      drawCapture(doc);
    })
    .catch(function (err) {
      /* Opened from the filesystem rather than served, a browser refuses the
         fetch on origin grounds and there is nothing the page can do about it.
         Say so, rather than showing empty frames that look like no data. */
      fail('The figures could not be loaded: ' + err.message +
           '. This page reads data/dispatch-views.json over HTTP, so it has ' +
           'to be served rather than opened as a local file. The numbers ' +
           'themselves are in data/dispatch-events.csv either way.');
    });
})();
