'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { test } = require('node:test');
const scriptPath = path.join(__dirname, '../docs/assets/evidence-board.js');
const { getRecord, initEvidenceBoard } = require(scriptPath);

// A deliberately small DOM fixture, not a browser or a keyboard emulator.
// It implements the DOM operations used by the shipped enhancement itself.
class Element {
  constructor(tagName, attributes = {}, children = []) {
    this.tagName = tagName.toUpperCase();
    this.attributes = { ...attributes };
    this.children = children;
    this.listeners = new Map();
    this.textContent = '';
    const classes = new Set((attributes.class || '').split(/\s+/).filter(Boolean));
    this.classList = {
      add: (value) => classes.add(value),
      contains: (value) => classes.has(value),
      toggle(value, force) {
        const enabled = force === undefined ? !classes.has(value) : force;
        if (enabled) classes.add(value);
        else classes.delete(value);
        return enabled;
      }
    };
  }
  get id() { return this.getAttribute('id') || ''; }
  get hidden() { return this.getAttribute('hidden') !== null; }
  set hidden(value) {
    if (value) this.setAttribute('hidden', '');
    else delete this.attributes.hidden;
  }
  getAttribute(name) { return Object.hasOwn(this.attributes, name) ? this.attributes[name] : null; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  contains(element) { return this === element || this.children.some((child) => child.contains(element)); }
  querySelectorAll(selector) {
    let matches;
    if (selector.startsWith('#')) matches = (element) => element.id === selector.slice(1);
    else {
      const attribute = selector.match(/^\[([\w-]+)(?:="([^"]*)")?\]$/);
      assert.ok(attribute, 'The fixture needs an explicit implementation for selector ' + selector);
      matches = (element) => element.getAttribute(attribute[1]) !== null &&
        (attribute[2] === undefined || element.getAttribute(attribute[1]) === attribute[2]);
    }
    const found = [];
    const visit = (element) => element.children.forEach((child) => {
      if (matches(child)) found.push(child);
      visit(child);
    });
    visit(this);
    return found;
  }
  addEventListener(type, listener, options) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push({ listener, options });
  }
  dispatch(type) {
    for (const handler of [...(this.listeners.get(type) || [])]) {
      handler.listener({ type, target: this, currentTarget: this });
      if (handler.options && handler.options.once) {
        this.listeners.set(type, this.listeners.get(type).filter((item) => item !== handler));
      }
    }
  }
  focus() { throw new Error('The enhancement must not move focus.'); }
}

function fixture() {
  const buttons = Object.fromEntries(['award', 'agreement', 'revision'].map((id) => [id,
    new Element('button', { type: 'button', 'data-select-record': id, 'aria-controls': 'record-' + id })
  ]));
  const articles = Object.fromEntries(['award', 'agreement', 'revision'].map((id) => [id,
    new Element('article', { id: 'record-' + id, 'data-record': id })
  ]));
  for (const [id, article] of Object.entries(articles)) article.textContent = 'Full readable ' + id + ' evidence.';
  const controls = new Element('div', { hidden: '', 'data-record-controls': '' }, Object.values(buttons));
  const announcement = new Element('p', { 'data-record-announcement': '', role: 'status', 'aria-live': 'polite' });
  const edges = Object.fromEntries(['e-grant', 'e-approval', 'e-leo-revisions', 'e-direction'].map((id) => [id,
    new Element('g', { 'data-edge': id }, [new Element('path'), new Element('text')])
  ]));
  const nodes = Object.fromEntries(['cobalt', 'meridian', 'leo', 'brief', 'astera'].map((id) => [id,
    new Element('g', { 'data-node': id }, [new Element('rect'), new Element('text')])
  ]));
  const svg = new Element('svg', {}, [...Object.values(edges), ...Object.values(nodes)]);
  const board = new Element('section', { id: 'evidence-board' }, [controls, svg, ...Object.values(articles), announcement]);
  const document = new Element('document', {}, [board]);
  document.readyState = 'complete';
  document.activeElement = new Element('a');
  return { document, board, controls, announcement, buttons, articles, edges, nodes, svg };
}

function activeIds(elements) {
  return Object.entries(elements).filter(([, element]) => element.classList.contains('is-active')).map(([id]) => id);
}
function assertReadableFallback(view) {
  assert.equal(view.controls.hidden, true);
  assert.equal(view.board.classList.contains('is-enhanced'), false);
  for (const article of Object.values(view.articles)) {
    assert.equal(article.hidden, false);
    assert.match(article.textContent, /^Full readable /);
  }
  for (const button of Object.values(view.buttons)) {
    assert.equal(button.getAttribute('aria-pressed'), null);
    assert.equal(button.listeners.size, 0);
  }
  assert.equal(view.announcement.textContent, '');
  assert.deepEqual(activeIds(view.edges), []);
  assert.deepEqual(activeIds(view.nodes), []);
}
function assertDiagramStillPresent(view) {
  for (const element of [...Object.values(view.edges), ...Object.values(view.nodes)]) {
    assert.equal(element.hidden, false);
    assert.equal(element.getAttribute('aria-hidden'), null);
  }
  assert.equal(view.edges['e-direction'].classList.contains('is-active'), false);
  assert.equal(view.nodes.astera.classList.contains('is-active'), false);
}

test('the record model preserves specific relationships and rejects unrecognized IDs', () => {
  assert.deepEqual(getRecord('award').nodes, ['cobalt', 'meridian']);
  assert.equal(getRecord('agreement').edge, 'e-approval');
  assert.deepEqual(getRecord('revision').nodes, ['leo', 'brief']);
  for (const id of ['', 'other', '__proto__', 'constructor', null, undefined, 1, {}]) {
    assert.equal(getRecord(id), null);
  }
  assert.throws(() => { getRecord('award').nodes.push('astera'); }, TypeError);
  assert.throws(() => { getRecord('agreement').edge = 'e-direction'; }, TypeError);
});

test('the fallback is readable and initialization selects the award without announcing or moving focus', () => {
  const view = fixture();
  assertReadableFallback(view);
  const previousFocus = view.document.activeElement;
  const controller = initEvidenceBoard(view.document);
  assert.equal(controller.selectedId, 'award');
  assert.equal(view.controls.hidden, false);
  assert.equal(view.board.classList.contains('is-enhanced'), true);
  assert.equal(view.articles.award.hidden, false);
  assert.equal(view.articles.agreement.hidden, true);
  assert.equal(view.articles.revision.hidden, true);
  assert.equal(view.buttons.award.getAttribute('aria-pressed'), 'true');
  assert.equal(view.buttons.agreement.getAttribute('aria-pressed'), 'false');
  assert.equal(view.buttons.revision.getAttribute('aria-pressed'), 'false');
  assert.deepEqual(activeIds(view.edges), ['e-grant']);
  assert.deepEqual(activeIds(view.nodes), ['cobalt', 'meridian']);
  assert.equal(view.announcement.textContent, '');
  assert.equal(view.document.activeElement, previousFocus);
  assertDiagramStillPresent(view);
});

test('native button clicks select the relation and its actual endpoints, preserving context and focus', () => {
  const view = fixture();
  const controller = initEvidenceBoard(view.document);
  for (const button of Object.values(view.buttons)) {
    assert.equal(button.tagName, 'BUTTON');
    assert.equal(button.getAttribute('type'), 'button');
    assert.deepEqual([...button.listeners.keys()], ['click']);
  }
  view.document.activeElement = view.buttons.agreement;
  view.buttons.agreement.dispatch('click');
  assert.equal(controller.selectedId, 'agreement');
  assert.equal(view.articles.award.hidden, true);
  assert.equal(view.articles.agreement.hidden, false);
  assert.equal(view.articles.revision.hidden, true);
  assert.equal(view.buttons.award.getAttribute('aria-pressed'), 'false');
  assert.equal(view.buttons.agreement.getAttribute('aria-pressed'), 'true');
  assert.deepEqual(activeIds(view.edges), ['e-approval']);
  assert.deepEqual(activeIds(view.nodes), ['cobalt', 'brief']);
  assert.equal(view.announcement.textContent,
    'The signed agreement: Cobalt Foundation holds approval rights over the funded policy brief.');
  assert.equal(view.document.activeElement, view.buttons.agreement);
  assertDiagramStillPresent(view);

  view.document.activeElement = view.buttons.revision;
  view.buttons.revision.dispatch('click');
  assert.equal(controller.selectedId, 'revision');
  assert.equal(view.articles.agreement.hidden, true);
  assert.equal(view.articles.revision.hidden, false);
  assert.equal(view.buttons.agreement.getAttribute('aria-pressed'), 'false');
  assert.equal(view.buttons.revision.getAttribute('aria-pressed'), 'true');
  assert.deepEqual(activeIds(view.edges), ['e-leo-revisions']);
  assert.deepEqual(activeIds(view.nodes), ['leo', 'brief']);
  assert.equal(view.announcement.textContent,
    'The revision register: Leo Venn requested in-scope revisions to the funded policy brief.');
  assert.equal(view.document.activeElement, view.buttons.revision);
  assertDiagramStillPresent(view);

  view.buttons.award.dispatch('click');
  assert.equal(controller.selectedId, 'award');
  assert.equal(view.articles.award.hidden, false);
  assert.equal(view.articles.revision.hidden, true);
  assert.deepEqual(activeIds(view.edges), ['e-grant']);
  assert.deepEqual(activeIds(view.nodes), ['cobalt', 'meridian']);
  assert.equal(view.announcement.textContent,
    'The award notice: Cobalt Foundation awarded a research grant to Meridian Institute.');
});

test('invalid or unchanged selections do not alter state or produce a new announcement', () => {
  const view = fixture();
  const controller = initEvidenceBoard(view.document);
  view.buttons.award.dispatch('click');
  assert.equal(view.announcement.textContent, '');
  for (const id of ['invalid', '__proto__', null, undefined]) {
    assert.equal(controller.select(id), false);
  }
  assert.equal(controller.selectedId, 'award');
  assert.equal(view.articles.award.hidden, false);
  assert.deepEqual(activeIds(view.edges), ['e-grant']);
  assert.equal(view.announcement.textContent, '');
  assert.equal(controller.select('revision'), true);
  assert.equal(controller.selectedId, 'revision');
  assert.equal(view.announcement.textContent, '', 'Programmatic changes stay quiet.');
});

test('reinitializing a board reuses its controller and does not reset selection or duplicate handlers', () => {
  const view = fixture();
  const original = initEvidenceBoard(view.document);
  view.buttons.revision.dispatch('click');
  assert.equal(initEvidenceBoard(view.document), original);
  assert.equal(original.selectedId, 'revision');
  for (const button of Object.values(view.buttons)) assert.equal(button.listeners.get('click').length, 1);
});

test('every missing required part preserves the unmodified readable fallback', () => {
  const missingParts = [
    '[data-record-controls]', '[data-record-announcement]',
    ...['award', 'agreement', 'revision'].map((id) => '[data-record="' + id + '"]'),
    ...['award', 'agreement', 'revision'].map((id) => '[data-select-record="' + id + '"]'),
    ...['e-grant', 'e-approval', 'e-leo-revisions', 'e-direction'].map((id) => '[data-edge="' + id + '"]'),
    ...['cobalt', 'meridian', 'leo', 'brief', 'astera'].map((id) => '[data-node="' + id + '"]')
  ];
  for (const selector of missingParts) {
    const view = fixture();
    const target = view.board.querySelectorAll(selector)[0];
    const remove = (element) => {
      element.children = element.children.filter((child) => child !== target);
      element.children.forEach(remove);
    };
    remove(view.board);
    assert.equal(initEvidenceBoard(view.document), null, selector);
    assertReadableFallback(view);
  }
  assert.equal(initEvidenceBoard(null), null);
  assert.equal(initEvidenceBoard({}), null);
  assert.equal(initEvidenceBoard(new Element('document')), null);
});

test('ambiguous markup, incorrect panel links, and an announcement inside a panel fail before mutation', () => {
  const mutations = [
    (view) => view.buttons.award.setAttribute('aria-controls', 'record-revision'),
    (view) => view.articles.award.setAttribute('id', 'wrong-panel'),
    (view) => { view.buttons.agreement.tagName = 'A'; },
    (view) => view.announcement.setAttribute('aria-live', 'assertive'),
    (view) => view.board.children.push(new Element('g', { 'data-node': 'leo' })),
    (view) => view.controls.children.push(new Element('button', { 'data-select-record': 'unexpected' })),
    (view) => view.board.children.push(new Element('article', { 'data-record': 'unexpected' })),
    (view) => {
      view.board.children = view.board.children.filter((child) => child !== view.announcement);
      view.articles.award.children.push(view.announcement);
    }
  ];
  for (const mutate of mutations) {
    const view = fixture();
    mutate(view);
    assert.equal(initEvidenceBoard(view.document), null);
    assertReadableFallback(view);
  }
});

test('the standalone script initializes after DOM readiness and can load with no document', () => {
  const source = fs.readFileSync(scriptPath, 'utf8');
  assert.doesNotThrow(() => vm.runInNewContext(source, {}));
  const ready = fixture();
  vm.runInNewContext(source, { document: ready.document });
  assert.equal(ready.controls.hidden, false);
  assert.equal(ready.announcement.textContent, '');
  const loading = fixture();
  loading.document.readyState = 'loading';
  vm.runInNewContext(source, { document: loading.document });
  assertReadableFallback(loading);
  loading.document.dispatch('DOMContentLoaded');
  assert.equal(loading.controls.hidden, false);
  assert.equal(loading.articles.award.hidden, false);
  assert.equal(loading.articles.agreement.hidden, true);
  assert.equal(loading.announcement.textContent, '');
  assert.equal(loading.document.listeners.get('DOMContentLoaded').length, 0);
});

function readHomepageDocument() {
  // HTMLParser reads the checked-in page, including nesting, attributes, and
  // fallback copy. The fixture supplies DOM operations, not browser rendering.
  const parser = String.raw`
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

class PageParser(HTMLParser):
    void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {'tag': 'document', 'attributes': {}, 'children': [], 'text': ''}
        self.stack = [self.root]

    def add_node(self, tag, attrs):
        node = {'tag': tag, 'attributes': {key: value if value is not None else '' for key, value in attrs}, 'children': [], 'text': ''}
        self.stack[-1]['children'].append(node)
        return node

    def handle_starttag(self, tag, attrs):
        node = self.add_node(tag, attrs)
        if tag not in self.void_tags:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.add_node(tag, attrs)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        for node in self.stack:
            node['text'] += data

parser = PageParser()
parser.feed(Path(sys.argv[1]).read_text(encoding='utf-8'))
parser.close()
print(json.dumps(parser.root, ensure_ascii=True))
`;
  const tree = JSON.parse(execFileSync('python', [
    '-c', parser, path.join(__dirname, '../docs/index.html')
  ], { encoding: 'utf8' }));
  const toElement = (node) => {
    const element = new Element(node.tag, node.attributes, node.children.map(toElement));
    element.textContent = node.text;
    return element;
  };
  const document = toElement(tree);
  document.readyState = 'complete';
  return document;
}

const canonicalCase = JSON.parse(fs.readFileSync(
  path.join(__dirname, '../src/red-threads/examples/meridian-case.json'), 'utf8'
));
const canonicalRouteIds = {
  award: 'e-grant', agreement: 'e-approval', revision: 'e-leo-revisions'
};

test('all record relations and endpoints agree with the canonical Meridian case', () => {
  for (const [recordId, edgeId] of Object.entries(canonicalRouteIds)) {
    const edge = canonicalCase.edges.find((candidate) => candidate.id === edgeId);
    assert.ok(edge, 'Canonical relation is missing: ' + edgeId);
    const record = getRecord(recordId);
    assert.equal(record.edge, edge.id, recordId + ' selects the canonical relationship.');
    assert.deepEqual(record.nodes, [edge.source, edge.target],
      recordId + ' highlights the actual source and target.');
    for (const endpoint of record.nodes) {
      assert.ok(canonicalCase.nodes.some((node) => node.id === endpoint),
        'Canonical endpoint is missing: ' + endpoint);
    }
  }
});

test('the actual homepage activates the shipped enhancement and selects every canonical route', () => {
  const document = readHomepageDocument();
  const scripts = document.querySelectorAll('[src="assets/evidence-board.js"]');
  assert.equal(scripts.length, 1, 'The homepage must load the shipped enhancement once.');
  assert.equal(scripts[0].tagName, 'SCRIPT');
  assert.notEqual(scripts[0].getAttribute('defer'), null);
  const board = document.querySelectorAll('#evidence-board')[0];
  assert.ok(board, 'The homepage must contain the evidence board.');
  const controls = board.querySelectorAll('[data-record-controls]')[0];
  const announcement = board.querySelectorAll('[data-record-announcement]')[0];
  assert.ok(controls);
  assert.ok(announcement);
  assert.equal(controls.hidden, true, 'Controls stay hidden until enhancement succeeds.');
  assert.equal(announcement.textContent.trim(), '');
  const byAttribute = (attribute) => Object.fromEntries(
    board.querySelectorAll('[' + attribute + ']').map((element) => [element.getAttribute(attribute), element])
  );
  const articles = byAttribute('data-record');
  const buttons = byAttribute('data-select-record');
  const edges = byAttribute('data-edge');
  const nodes = byAttribute('data-node');
  assert.deepEqual(Object.keys(articles).sort(), ['agreement', 'award', 'revision']);
  for (const article of Object.values(articles)) {
    assert.equal(article.hidden, false, 'Every actual article must be available without JavaScript.');
    assert.ok(article.textContent.trim(), 'Each fallback article must contain readable evidence.');
  }

  // Execute the same standalone boot path the page loads, against its parsed DOM.
  vm.runInNewContext(fs.readFileSync(scriptPath, 'utf8'), { document });
  assert.equal(board.classList.contains('is-enhanced'), true,
    'Actual page hooks must satisfy the enhancement preflight.');
  assert.equal(controls.hidden, false);
  assert.equal(articles.award.hidden, false);
  assert.equal(articles.agreement.hidden, true);
  assert.equal(articles.revision.hidden, true);
  assert.equal(announcement.textContent.trim(), '', 'Initial activation must stay quiet.');

  for (const recordId of ['agreement', 'revision', 'award']) {
    const edge = canonicalCase.edges.find((candidate) => candidate.id === canonicalRouteIds[recordId]);
    assert.equal(buttons[recordId].tagName, 'BUTTON');
    assert.equal(buttons[recordId].getAttribute('type'), 'button');
    buttons[recordId].dispatch('click');
    for (const [articleId, article] of Object.entries(articles)) {
      assert.equal(article.hidden, articleId !== recordId, recordId + ' selects its actual article.');
      assert.equal(buttons[articleId].getAttribute('aria-pressed'), String(articleId === recordId));
    }
    assert.deepEqual(activeIds(edges), [edge.id]);
    assert.deepEqual(activeIds(nodes).sort(), [edge.source, edge.target].sort());
    assert.ok(announcement.textContent.trim(), 'A user selection must announce its relation.');
    assertDiagramStillPresent({ edges, nodes });
  }
});
