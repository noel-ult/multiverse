/* tree.js — SVG tree renderer with top-down hierarchical layout */
(function () {
    'use strict';

    var uid = window.__universeId;
    if (!uid) return;

    var svg = document.getElementById('treeSvg');
    var viewport = document.getElementById('treeViewport');
    if (!svg || !viewport) return;

    var NS = 'http://www.w3.org/2000/svg';
    var LEVEL_GAP = 180;
    var NODE_GAP = 60;
    var ROOT_R = 22;
    var NODE_R = 16;
    var H_PAD = 120;
    var V_PAD = 100;
    var MIN_SCALE = 0.15;
    var MAX_SCALE = 3;

    var treeData = null;
    var allNodes = [];
    var selectedNode = null;
    var zoom = 1;
    var panX = 0, panY = 0;
    var dragging = false, dragStartX = 0, dragStartY = 0;
    var lastSvgW = 0, lastSvgH = 0;
    var depthMode = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var tiltX = 0, tiltY = 0;

    function escapeHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function showLoading() {
        svg.innerHTML = '';
        var g = document.createElementNS(NS, 'g');
        g.setAttribute('text-anchor', 'middle');
        var t1 = document.createElementNS(NS, 'text');
        t1.setAttribute('fill', '#7a80a4');
        t1.setAttribute('font-size', '13');
        t1.setAttribute('font-weight', '600');
        t1.setAttribute('letter-spacing', '2');
        t1.textContent = 'BUILDING MULTIVERSE...';
        g.appendChild(t1);
        for (var i = 0; i < 3; i++) {
            var dot = document.createElementNS(NS, 'circle');
            dot.setAttribute('cx', String(-20 + i * 20));
            dot.setAttribute('cy', '28');
            dot.setAttribute('r', '3');
            dot.setAttribute('fill', '#6c5ce7');
            dot.setAttribute('opacity', '0.3');
            var anim = document.createElementNS(NS, 'animate');
            anim.setAttribute('attributeName', 'opacity');
            anim.setAttribute('values', '0.3;1;0.3');
            anim.setAttribute('dur', '1.2s');
            anim.setAttribute('begin', (i * 0.3) + 's');
            anim.setAttribute('repeatCount', 'indefinite');
            dot.appendChild(anim);
            g.appendChild(dot);
        }
        svg.appendChild(g);
    }

    function showError() {
        svg.innerHTML = '';
        var g = document.createElementNS(NS, 'g');
        g.setAttribute('text-anchor', 'middle');
        var t1 = document.createElementNS(NS, 'text');
        t1.setAttribute('fill', '#e0e4f0');
        t1.setAttribute('font-size', '14');
        t1.setAttribute('font-weight', '700');
        t1.setAttribute('letter-spacing', '2');
        t1.textContent = 'UNIVERSE TREE UNAVAILABLE';
        g.appendChild(t1);
        var t2 = document.createElementNS(NS, 'text');
        t2.setAttribute('y', '28');
        t2.setAttribute('fill', '#7a80a4');
        t2.setAttribute('font-size', '12');
        t2.textContent = 'Unable to load this timeline.';
        g.appendChild(t2);
        svg.appendChild(g);
    }

    showLoading();

    fetch('/universe/' + uid + '/tree.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) { treeData = data; render(); })
        .catch(function () { showError(); });

    function isSingleChain(node) {
        if (!node) return true;
        if (!node.children || !node.children.length) return true;
        if (node.children.length > 1) return false;
        return isSingleChain(node.children[0]);
    }

    function updateChainHint() {
        var hint = document.getElementById('treeChainHint');
        if (!hint) return;
        hint.hidden = !isSingleChain(treeData);
    }

    function subtreeWidth(node) {
        if (!node.children || !node.children.length) return 1;
        return node.children.reduce(function (s, c) { return s + subtreeWidth(c); }, 0);
    }

    function layoutNode(node, left, depth) {
        node._y = depth * LEVEL_GAP;
        node._depth = depth;
        allNodes.push(node);

        if (!node.children || !node.children.length) {
            node._x = left + NODE_GAP / 2;
            return;
        }

        var startLeft = left;
        for (var i = 0; i < node.children.length; i++) {
            var child = node.children[i];
            child._parent = node;
            var w = subtreeWidth(child) * NODE_GAP;
            layoutNode(child, startLeft, depth + 1);
            startLeft += w;
        }

        var first = node.children[0];
        var last = node.children[node.children.length - 1];
        node._x = (first._x + last._x) / 2;
    }

    function getBounds() {
        var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        allNodes.forEach(function (n) {
            if (n._x < minX) minX = n._x;
            if (n._x > maxX) maxX = n._x;
            if (n._y < minY) minY = n._y;
            if (n._y > maxY) maxY = n._y;
        });
        return { minX: minX, maxX: maxX, minY: minY, maxY: maxY };
    }

    function starPath(cx, cy, r) {
        var pts = [];
        for (var i = 0; i < 10; i++) {
            var rad = i % 2 === 0 ? r : r * 0.45;
            var a = -Math.PI / 2 + (i * Math.PI) / 5;
            pts.push((cx + rad * Math.cos(a)).toFixed(1) + ',' + (cy + rad * Math.sin(a)).toFixed(1));
        }
        return pts.join(' ');
    }

    function addBadge(g, cx, cy, r, type) {
        if (type === 'star') {
            var s = document.createElementNS(NS, 'polygon');
            s.setAttribute('points', starPath(cx, cy, r));
            s.setAttribute('fill', '#feca57');
            s.setAttribute('stroke', 'rgba(20,20,35,0.8)');
            s.setAttribute('stroke-width', '1');
            s.classList.add('tree-badge');
            g.appendChild(s);
        } else if (type === 'warn') {
            var t = document.createElementNS(NS, 'path');
            t.setAttribute('d', 'M -5,4 L 0,-5 L 5,4 Z');
            t.setAttribute('fill', '#f39c12');
            t.setAttribute('stroke', 'rgba(20,20,35,0.8)');
            t.setAttribute('stroke-width', '1');
            t.classList.add('tree-badge');
            g.appendChild(t);
        }
    }

    function render() {
        if (!treeData) return;

        allNodes = [];
        layoutNode(treeData, 0, 0);

        var b = getBounds();
        lastSvgW = b.maxX - b.minX + H_PAD * 2;
        lastSvgH = b.maxY - b.minY + V_PAD * 2;

        svg.setAttribute('viewBox', '0 0 ' + lastSvgW + ' ' + lastSvgH);
        svg.innerHTML = '';

        var defs = document.createElementNS(NS, 'defs');
        ['glow', 'glow-strong'].forEach(function (id, idx) {
            var filter = document.createElementNS(NS, 'filter');
            filter.setAttribute('id', id);
            filter.setAttribute('x', '-50%');
            filter.setAttribute('y', '-50%');
            filter.setAttribute('width', '200%');
            filter.setAttribute('height', '200%');
            var blur = document.createElementNS(NS, 'feGaussianBlur');
            blur.setAttribute('stdDeviation', idx === 0 ? '3' : '6');
            blur.setAttribute('result', 'g');
            filter.appendChild(blur);
            var merge = document.createElementNS(NS, 'feMerge');
            var m1 = document.createElementNS(NS, 'feMergeNode');
            m1.setAttribute('in', 'g');
            merge.appendChild(m1);
            var m2 = document.createElementNS(NS, 'feMergeNode');
            m2.setAttribute('in', 'SourceGraphic');
            merge.appendChild(m2);
            filter.appendChild(merge);
            defs.appendChild(filter);
        });
        svg.appendChild(defs);

        var linksG = document.createElementNS(NS, 'g');
        svg.appendChild(linksG);
        var nodesG = document.createElementNS(NS, 'g');
        svg.appendChild(nodesG);

        var animDelay = 0;

        allNodes.forEach(function (n) {
            if (!n._parent) return;
            var x1 = n._parent._x - b.minX + H_PAD;
            var y1 = n._parent._y - b.minY + V_PAD + (n._parent === treeData ? ROOT_R : NODE_R);
            var x2 = n._x - b.minX + H_PAD;
            var y2 = n._y - b.minY + V_PAD - NODE_R;
            var midY = (y1 + y2) / 2;

            var path = document.createElementNS(NS, 'path');
            path.setAttribute('d', 'M' + x1 + ',' + y1 + ' C' + x1 + ',' + midY + ' ' + x2 + ',' + midY + ' ' + x2 + ',' + y2);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', 'rgba(100,120,255,0.2)');
            path.setAttribute('stroke-width', '2');
            path.classList.add('tree-link');
            path.style.opacity = '0';
            path.style.transition = 'opacity 0.4s ease';
            linksG.appendChild(path);
            setTimeout(function () { path.style.opacity = '1'; }, 80 + animDelay);
        });

        allNodes.forEach(function (n) {
            var cx = n._x - b.minX + H_PAD;
            var cy = n._y - b.minY + V_PAD;
            var isRoot = !n._parent;
            var isCurrent = n.id === uid;
            var r = isRoot ? ROOT_R : NODE_R;

            var g = document.createElementNS(NS, 'g');
            g.setAttribute('data-id', String(n.id));
            g.classList.add('tree-node');
            g.classList.add('tree-node--depth-' + Math.min(n._depth, 5));
            if (isRoot) g.classList.add('tree-node--root');
            if (isCurrent) g.classList.add('tree-node--current');
            g.setAttribute('transform', 'translate(' + cx + ',' + cy + ')');
            g.style.opacity = '0';
            g.style.transition = 'opacity 0.35s ease, filter 0.2s ease';
            g.style.cursor = 'pointer';

            var ring = document.createElementNS(NS, 'circle');
            ring.setAttribute('r', String(r + 5));
            ring.setAttribute('fill', 'none');
            ring.setAttribute('stroke', isCurrent ? 'rgba(0,206,201,0.35)' : isRoot ? 'rgba(108,92,231,0.25)' : 'rgba(108,92,231,0.08)');
            ring.setAttribute('stroke-width', isCurrent ? '2' : '1');
            g.appendChild(ring);

            var circle = document.createElementNS(NS, 'circle');
            circle.setAttribute('r', String(r));
            circle.setAttribute('fill', isCurrent ? '#00cec9' : isRoot ? '#6c5ce7' : 'rgba(108,92,231,0.55)');
            circle.setAttribute('stroke', isCurrent ? '#00cec9' : isRoot ? '#6c5ce7' : 'rgba(108,92,231,0.3)');
            circle.setAttribute('stroke-width', isCurrent ? '3' : '1.5');
            if (isCurrent || isRoot) circle.setAttribute('filter', 'url(#glow)');
            if (n.score >= 80) circle.setAttribute('filter', 'url(#glow-strong)');
            g.appendChild(circle);

            var inner = document.createElementNS(NS, 'circle');
            inner.setAttribute('r', String(r * 0.35));
            inner.setAttribute('fill', 'rgba(255,255,255,0.12)');
            inner.setAttribute('cy', String(-r * 0.15));
            g.appendChild(inner);

            var idText = document.createElementNS(NS, 'text');
            idText.setAttribute('y', String(-r - 8));
            idText.setAttribute('text-anchor', 'middle');
            idText.setAttribute('fill', '#7a80a4');
            idText.setAttribute('font-size', '9');
            idText.setAttribute('font-family', 'Segoe UI, system-ui, sans-serif');
            idText.textContent = '#' + n.id;
            g.appendChild(idText);

            var label = n.name.indexOf(' \u2014 ') !== -1 ? n.name.split(' \u2014 ').pop() : n.name;
            if (label.length > 16) label = label.slice(0, 14) + '..';
            var text = document.createElementNS(NS, 'text');
            text.setAttribute('y', String(r + 15));
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', '#e0e4f0');
            text.setAttribute('font-size', '11');
            text.setAttribute('font-weight', '600');
            text.setAttribute('font-family', 'Segoe UI, system-ui, sans-serif');
            text.textContent = label;
            g.appendChild(text);

            if (isRoot) addBadge(g, 0, -r + 6, 7, 'star');
            if (n.milestones > 0) addBadge(g, r - 4, -r + 4, 5, 'star');
            if (n.energy <= 20) addBadge(g, r + 2, r - 5, 0, 'warn');

            g.addEventListener('click', function (e) { e.stopPropagation(); selectNode(n); });
            g.addEventListener('mouseenter', function () {
                circle.setAttribute('r', String(r * 1.15));
                ring.setAttribute('r', String(r * 1.15 + 5));
                if (!isCurrent && !isRoot && n.score < 80) circle.setAttribute('filter', 'url(#glow)');
            });
            g.addEventListener('mouseleave', function () {
                circle.setAttribute('r', String(r));
                ring.setAttribute('r', String(r + 5));
                if (!isCurrent && !isRoot && n.score < 80) circle.removeAttribute('filter');
            });

            nodesG.appendChild(g);
            g.style.transformOrigin = 'center';
            setTimeout(function () { g.style.opacity = '1'; g.classList.add('tree-node--arrived'); }, 40 + animDelay);
            animDelay += 50;
        });

        requestAnimationFrame(function () { fitTreeToViewport(); });
        updateChainHint();
        renderExplorer(allNodes);

        var current = allNodes.find(function (n) { return n.id === uid; });
        if (current) selectNode(current);
    }

    function shortName(node) {
        var parts = node.name.split(' — ');
        return parts[parts.length - 1];
    }

    function renderExplorer(nodes) {
        var explorer = document.getElementById('treeExplorer');
        var search = document.getElementById('treeSearch');
        if (!explorer) return;
        var draw = function () {
            var query = search ? search.value.trim().toLowerCase() : '';
            explorer.innerHTML = '';
            nodes.filter(function (node) { return !query || node.name.toLowerCase().indexOf(query) !== -1; })
                .forEach(function (node) {
                    var item = document.createElement('button');
                    item.type = 'button'; item.className = 'tree-explorer__item';
                    item.setAttribute('role', 'listitem');
                    item.innerHTML = '<span class="tree-explorer__depth">L' + node._depth + '</span><span><b></b><strong></strong><small></small></span>';
                    item.querySelector('b').textContent = shortName(node);
                    item.querySelector('strong').textContent = node.score + ' SCORE';
                    item.querySelector('small').textContent = node.parent_id ? 'BRANCH #' + node.parent_id : 'ORIGIN REALITY';
                    item.addEventListener('click', function () { selectNode(node); focusNode(node); });
                    explorer.appendChild(item);
                });
            if (!explorer.children.length) explorer.textContent = 'No realities match this signal.';
        };
        draw();
        if (search) search.addEventListener('input', draw);
    }

    function focusNode(node) {
        var bounds = getBounds();
        var rect = viewport.getBoundingClientRect();
        var cx = node._x - bounds.minX + H_PAD;
        var cy = node._y - bounds.minY + V_PAD;
        panX = rect.width / 2 - cx * zoom;
        panY = rect.height / 2 - cy * zoom;
        applyTransform();
    }

    function fitTreeToViewport() {
        var rect = viewport.getBoundingClientRect();
        var vw = rect.width;
        var vh = rect.height;
        if (vw === 0 || vh === 0 || lastSvgW === 0) return;
        zoom = Math.min(vw / lastSvgW, vh / lastSvgH, 1) * 0.9;
        panX = (vw - lastSvgW * zoom) / 2;
        panY = (vh - lastSvgH * zoom) / 2;
        applyTransform();
    }

    function applyTransform() {
        var tilt = depthMode ? ' rotateX(' + tiltX.toFixed(2) + 'deg) rotateY(' + tiltY.toFixed(2) + 'deg)' : '';
        svg.style.transform = 'translate(' + panX + 'px,' + panY + 'px) scale(' + zoom + ')' + tilt;
        svg.style.transformOrigin = '50% 50%';
        viewport.classList.toggle('tree-viewport--depth', depthMode);
    }

    function selectNode(node) {
        selectedNode = node;

        svg.querySelectorAll('.tree-node--selected').forEach(function (el) {
            el.classList.remove('tree-node--selected');
        });
        var el = svg.querySelector('[data-id="' + node.id + '"]');
        if (el) el.classList.add('tree-node--selected');

        var empty = document.getElementById('treeSidebarEmpty');
        var content = document.getElementById('treeSidebarContent');
        if (empty) empty.style.display = 'none';
        if (content) {
            content.style.display = 'block';
            document.getElementById('sidebarName').textContent = node.name;
            document.getElementById('sidebarParent').textContent = node.parent_id ? '#' + node.parent_id : 'None (Root)';
            document.getElementById('sidebarParentLink').href = node.parent_id
                ? '/universe/' + node.parent_id : '#';
            document.getElementById('sidebarParentLink').style.display = node.parent_id ? '' : 'none';
            document.getElementById('sidebarOpen').href = '/universe/' + node.id;
            document.getElementById('sidebarBranch').href = '/universe/' + node.id + '#decisions';
        }

        fetch('/universe/' + node.id + '/api')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var details = document.getElementById('sidebarDetails');
                if (details) {
                    var state = data.state || {};
                    var labels = { money: 'Money', energy: 'Energy', knowledge: 'Knowledge', career: 'Career', relationships: 'Relationships' };
                    var html = '';
                    Object.keys(labels).forEach(function (k) {
                        var v = state[k];
                        html += '<div class="sidebar-stat"><span class="sidebar-stat__label">' + labels[k] + '</span><span class="sidebar-stat__value">' + (v !== undefined ? v : '-') + '</span></div>';
                    });
                    details.innerHTML = html;
                }
                document.getElementById('sidebarCreated').textContent = data.created_at || '-';
                document.getElementById('sidebarDecision').textContent = data.created_from || '-';
                document.getElementById('sidebarScore').textContent =
                    (data.reality_score !== undefined ? data.reality_score : '-') +
                    (data.reality_status ? '  ' + data.reality_status : '');
                if (data.parent_name) {
                    document.getElementById('sidebarParent').textContent = data.parent_name;
                    document.getElementById('sidebarParent').innerHTML =
                        '<a href="/universe/' + data.parent_id + '" class="sidebar-info__link">' +
                        escapeHtml(data.parent_name) + '</a>';
                } else {
                    document.getElementById('sidebarParent').textContent = 'None (Root)';
                }
            })
            .catch(function () {});
    }

    document.getElementById('zoomIn').addEventListener('click', function () {
        zoom = Math.min(zoom * 1.25, MAX_SCALE);
        applyTransform();
    });
    document.getElementById('zoomOut').addEventListener('click', function () {
        zoom = Math.max(zoom / 1.25, MIN_SCALE);
        applyTransform();
    });
    document.getElementById('resetView').addEventListener('click', function () {
        fitTreeToViewport();
    });
    document.getElementById('fitTree').addEventListener('click', function () {
        fitTreeToViewport();
    });

    var depthToggle = document.getElementById('toggleDepth');
    if (depthToggle) {
        depthToggle.addEventListener('click', function () {
            depthMode = !depthMode;
            tiltX = 0; tiltY = 0;
            depthToggle.setAttribute('aria-pressed', String(depthMode));
            depthToggle.textContent = depthMode ? '3D DEPTH: ON' : '3D DEPTH: OFF';
            var readout = document.getElementById('treeDepthReadout');
            if (readout) readout.textContent = depthMode ? 'DEPTH / ACTIVE' : 'DEPTH / FLAT';
            applyTransform();
        });
    }

    viewport.addEventListener('pointermove', function (e) {
        if (!depthMode || dragging || e.pointerType === 'touch') return;
        var rect = viewport.getBoundingClientRect();
        tiltY = ((e.clientX - rect.left) / rect.width - 0.5) * 7;
        tiltX = -((e.clientY - rect.top) / rect.height - 0.5) * 5;
        applyTransform();
    });
    viewport.addEventListener('pointerleave', function () {
        if (!depthMode || dragging) return;
        tiltX = 0; tiltY = 0; applyTransform();
    });

    viewport.addEventListener('wheel', function (e) {
        e.preventDefault();
        var factor = e.deltaY > 0 ? 0.9 : 1.1;
        var newZoom = Math.max(MIN_SCALE, Math.min(MAX_SCALE, zoom * factor));
        var rect = viewport.getBoundingClientRect();
        var mx = e.clientX - rect.left;
        var my = e.clientY - rect.top;
        panX = mx - (mx - panX) * (newZoom / zoom);
        panY = my - (my - panY) * (newZoom / zoom);
        zoom = newZoom;
        applyTransform();
    }, { passive: false });

    viewport.addEventListener('mousedown', function (e) {
        if (e.target.closest('.tree-node')) return;
        dragging = true;
        dragStartX = e.clientX - panX;
        dragStartY = e.clientY - panY;
        viewport.style.cursor = 'grabbing';
    });
    window.addEventListener('mousemove', function (e) {
        if (!dragging) return;
        panX = e.clientX - dragStartX;
        panY = e.clientY - dragStartY;
        applyTransform();
    });
    window.addEventListener('mouseup', function () {
        dragging = false;
        viewport.style.cursor = 'grab';
    });

    var touchStart = null;
    viewport.addEventListener('touchstart', function (e) {
        if (e.touches.length === 1) {
            touchStart = { x: e.touches[0].clientX - panX, y: e.touches[0].clientY - panY };
        }
    });
    viewport.addEventListener('touchmove', function (e) {
        if (!touchStart || e.touches.length !== 1) return;
        e.preventDefault();
        panX = e.touches[0].clientX - touchStart.x;
        panY = e.touches[0].clientY - touchStart.y;
        applyTransform();
    }, { passive: false });
    viewport.addEventListener('touchend', function () { touchStart = null; });
})();
