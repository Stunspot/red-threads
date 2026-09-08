(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root && root.document) {
    const document = root.document;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        api.initEvidenceBoard(document);
      }, { once: true });
    } else {
      api.initEvidenceBoard(document);
    }
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const records = Object.freeze({
    award: Object.freeze({
      id: 'award',
      edge: 'e-grant',
      nodes: Object.freeze(['cobalt', 'meridian']),
      announcement: 'The award notice: Cobalt Foundation awarded a research grant to Meridian Institute.'
    }),
    agreement: Object.freeze({
      id: 'agreement',
      edge: 'e-approval',
      nodes: Object.freeze(['cobalt', 'brief']),
      announcement: 'The signed agreement: Cobalt Foundation holds approval rights over the funded policy brief.'
    }),
    revision: Object.freeze({
      id: 'revision',
      edge: 'e-leo-revisions',
      nodes: Object.freeze(['leo', 'brief']),
      announcement: 'The revision register: Leo Venn requested in-scope revisions to the funded policy brief.'
    })
  });
  const edgeIds = ['e-grant', 'e-approval', 'e-leo-revisions', 'e-direction'];
  const nodeIds = ['cobalt', 'meridian', 'leo', 'brief', 'astera'];
  const controllers = new WeakMap();

  function getRecord(id) {
    return typeof id === 'string' && Object.prototype.hasOwnProperty.call(records, id)
      ? records[id] : null;
  }

  function unique(scope, selector) {
    const matches = scope.querySelectorAll(selector);
    return matches.length === 1 ? matches[0] : null;
  }

  function initEvidenceBoard(document) {
    if (!document || typeof document.querySelectorAll !== 'function') return null;
    const board = unique(document, '#evidence-board');
    if (!board) return null;
    if (controllers.has(board)) return controllers.get(board);

    // Resolve the whole contract before changing the readable HTML fallback.
    const controls = unique(board, '[data-record-controls]');
    const announcement = unique(board, '[data-record-announcement]');
    if (!controls || !announcement) return null;
    const entries = Object.keys(records).map(function (id) {
      return {
        record: records[id],
        article: unique(board, '[data-record="' + id + '"]'),
        button: unique(controls, '[data-select-record="' + id + '"]')
      };
    });
    const edges = edgeIds.map(function (id) {
      return { id: id, element: unique(board, '[data-edge="' + id + '"]') };
    });
    const nodes = nodeIds.map(function (id) {
      return { id: id, element: unique(board, '[data-node="' + id + '"]') };
    });
    const validEntries = entries.every(function (entry) {
      return entry.article && entry.button &&
        entry.article.tagName.toLowerCase() === 'article' &&
        entry.button.tagName.toLowerCase() === 'button' &&
        entry.article.id === 'record-' + entry.record.id &&
        entry.button.getAttribute('aria-controls') === entry.article.id;
    });
    if (!validEntries || !edges.every(function (edge) { return edge.element; }) ||
        !nodes.every(function (node) { return node.element; }) ||
        board.querySelectorAll('[data-record]').length !== entries.length ||
        controls.querySelectorAll('[data-select-record]').length !== entries.length ||
        announcement.getAttribute('role') !== 'status' ||
        announcement.getAttribute('aria-live') !== 'polite' ||
        entries.some(function (entry) { return entry.article.contains(announcement); })) return null;

    let selectedId = null;
    function select(id, fromUser) {
      const record = getRecord(id);
      if (!record) return false;
      if (selectedId === id) return true;
      entries.forEach(function (entry) {
        const active = entry.record.id === id;
        entry.article.hidden = !active;
        entry.button.setAttribute('aria-pressed', String(active));
      });
      edges.forEach(function (edge) {
        edge.element.classList.toggle('is-active', edge.id === record.edge);
      });
      nodes.forEach(function (node) {
        node.element.classList.toggle('is-active', record.nodes.indexOf(node.id) !== -1);
      });
      selectedId = id;
      if (fromUser) announcement.textContent = record.announcement;
      return true;
    }

    entries.forEach(function (entry) {
      // Native button activation supplies keyboard behavior and retains focus.
      entry.button.addEventListener('click', function () { select(entry.record.id, true); });
    });
    select('award', false);
    board.classList.add('is-enhanced');
    controls.hidden = false;
    const controller = Object.freeze({
      select: function (id) { return select(id, false); },
      get selectedId() { return selectedId; }
    });
    controllers.set(board, controller);
    return controller;
  }

  return Object.freeze({ getRecord: getRecord, initEvidenceBoard: initEvidenceBoard });
}));
