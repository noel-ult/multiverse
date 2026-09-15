/* universe.js — timeline loading, decision preview, stat animations */
(function () {
    'use strict';

    var uid = window.__universeId;
    if (!uid) return;

    var currentState = window.__universeState || {};
    var decisions = window.__decisions || [];
    var universeName = window.__universeName || 'this reality';

    var EVENT_META = {
        creation: { icon: '\u25CF', label: 'UNIVERSE CREATED' },
        decision: { icon: '\u25C6', label: 'DECISION' },
        consequence: { icon: '\u2726', label: 'CONSEQUENCE' },
        milestone: { icon: '\u2605', label: 'MILESTONE' }
    };

    function escapeHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    // Load timeline with per-event visuals
    var timelineEl = document.getElementById('timeline');
    if (timelineEl) {
        fetch('/universe/' + uid + '/timeline.json')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                timelineEl.innerHTML = '';
                var steps = [];
                data.forEach(function (step) {
                    var nameShort = step.name.indexOf(' \u2014 ') !== -1
                        ? step.name.split(' \u2014 ').pop() : step.name;
                    var events = step.events.map(function (e) {
                        var meta = EVENT_META[e.type] || { icon: '\u25CF', label: (e.type || '').toUpperCase() };
                        var title = e.metadata && e.metadata.title ? e.metadata.title : meta.label;
                        return '<div class="timeline__event timeline__event--' + e.type + '">' +
                            '<span class="timeline__event-icon">' + meta.icon + '</span>' +
                            '<div class="timeline__event-body">' +
                            '<span class="timeline__event-label">' + escapeHtml(title) + '</span>' +
                            '<span class="timeline__event-desc">' + escapeHtml(e.description) + '</span>' +
                            '</div></div>';
                    });
                    steps.push('<div class="timeline__step">' +
                        '<div class="timeline__name">' + escapeHtml(nameShort) + '</div>' +
                        events.join('') +
                        '</div>');
                });
                timelineEl.innerHTML = steps.join('<div class="timeline__connector"></div>');
            })
            .catch(function () {
                timelineEl.innerHTML = '<div class="timeline__loading">Could not load timeline.</div>';
            });
    }

    // Decision preview
    var previewEl = document.getElementById('decisionPreview');
    if (previewEl) {
        document.querySelectorAll('.decision-card').forEach(function (card) {
            var key = card.getAttribute('data-decision');
            var cfg = decisions.find(function (d) { return d.key === key; });
            if (!cfg) return;
            var show = function () {
                if (!cfg.unlocked) {
                    previewEl.innerHTML = '<div class="decision-preview__row decision-preview__row--locked">' +
                        '<strong>' + escapeHtml(cfg.label) + '</strong> — ' + escapeHtml(cfg.unlock_reason) +
                        '</div>';
                    return;
                }
                var after = {};
                var keys = Object.keys(currentState);
                keys.forEach(function (k) { after[k] = currentState[k]; });
                Object.keys(cfg.effects || {}).forEach(function (k) {
                    after[k] = (after[k] || 0) + cfg.effects[k];
                    if (k === 'money') after[k] = Math.max(0, after[k]);
                    else after[k] = Math.max(0, Math.min(100, after[k]));
                });
                var rows = keys.map(function (k) {
                    var delta = (after[k] || 0) - (currentState[k] || 0);
                    var cls = delta > 0 ? 'decision-preview__delta--pos' : delta < 0 ? 'decision-preview__delta--neg' : '';
                    var sign = delta > 0 ? '+' : '';
                    return '<div class="decision-preview__row">' +
                        '<span class="decision-preview__stat">' + k.toUpperCase() + ':</span>' +
                        '<span>' + currentState[k] + ' &rarr; <strong>' + after[k] + '</strong></span>' +
                        '<span class="decision-preview__delta ' + cls + '">' + sign + delta + '</span>' +
                        '</div>';
                });
                previewEl.innerHTML = '<div class="decision-preview__title">AFTER ' +
                    escapeHtml(cfg.label.toUpperCase()) + '</div>' + rows.join('') +
                    '<div class="decision-preview__cons">' + escapeHtml(cfg.consequence) + '</div>';
            };
            card.addEventListener('mouseenter', show);
            card.addEventListener('focusin', show);
        });
    }

    // Animate stat bars on load
    setTimeout(function () {
        document.querySelectorAll('.stat-bar__fill').forEach(function (bar) {
            var w = bar.style.width;
            bar.style.width = '0%';
            requestAnimationFrame(function () { bar.style.width = w; });
        });
    }, 100);

    // CREATE ALTERNATE REALITY CTA: reveal + focus the decision grid
    var altButton = document.getElementById('createAltReality');
    var decisionsPanel = document.getElementById('decisions');
    if (altButton && decisionsPanel) {
        altButton.addEventListener('click', function () {
            var grid = decisionsPanel.querySelector('.decisions-grid');
            if (grid) {
                grid.classList.remove('decisions-grid--focus');
                void grid.offsetWidth;
                grid.classList.add('decisions-grid--focus');
            }
            decisionsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    // Branch confirmation modal (no browser alert)
    var modal = document.getElementById('branchModal');
    var brFrom = document.getElementById('branchFrom');
    var brDecision = document.getElementById('branchDecision');
    var brPreview = document.getElementById('branchPreview');
    var confirmBtn = document.getElementById('branchConfirm');
    var cancelBtn = document.getElementById('branchCancel');
    var activeForm = null;

    if (modal && confirmBtn && cancelBtn) {
        document.querySelectorAll('.decision-card').forEach(function (card) {
            card.addEventListener('submit', function (e) {
                if (card.dataset.submitting) return;
                e.preventDefault();
                var isLocked = card.classList.contains('decision-card--locked') ||
                    (card.querySelector('button[type="submit"]') || {}).disabled;
                if (isLocked) return;

                var cfg = decisions.find(function (d) { return d.key === card.getAttribute('data-decision'); });
                activeForm = card;
                brFrom.textContent = universeName;
                brDecision.textContent = cfg ? cfg.label : card.getAttribute('data-decision');
                brPreview.textContent = cfg ? cfg.consequence : '';
                modal.hidden = false;
                confirmBtn.focus();
            });
        });

        var closeModal = function () {
            modal.hidden = true;
        };

        confirmBtn.addEventListener('click', function () {
            if (!activeForm) return;
            closeModal();
            activeForm.dataset.submitting = '1';
            activeForm.submit();
            setTimeout(function () { delete activeForm.dataset.submitting; }, 2000);
        });

        cancelBtn.addEventListener('click', closeModal);

        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !modal.hidden) closeModal();
        });
    }
})();