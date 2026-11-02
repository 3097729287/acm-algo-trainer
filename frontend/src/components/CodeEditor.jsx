import {EXTRA_SHORTCUTS,matchesShortcut} from '@/lib/shortcuts.js';
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { drawSelection, EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine } from '@codemirror/view';
import { Annotation, Compartment, EditorState, Prec } from '@codemirror/state';
import { indentLess, indentMore, history, defaultKeymap, historyKeymap } from '@codemirror/commands';
import {highlightSelectionMatches,searchKeymap} from '@codemirror/search';
import {lintKeymap} from '@codemirror/lint';
import { cpp } from '@codemirror/lang-cpp';
import { python } from '@codemirror/lang-python';
import { HighlightStyle, indentUnit, syntaxHighlighting, indentOnInput, bracketMatching } from '@codemirror/language';
import { acceptCompletion, autocompletion, completionStatus, snippetCompletion, closeBrackets, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete';
import { tags } from '@lezer/highlight';
import './CodeEditor.css';
import './CodeEditorTheme.css';
import {editorTheme as findEditorTheme,editorThemeStyle} from '@/lib/editorThemes.js';

const externalChange = Annotation.define();
// Configure the editor explicitly so neither a folding gutter nor folding
// commands can hide code. Keep history, selection, search and completion.
const editorSetup=[lineNumbers(),highlightActiveLineGutter(),highlightSpecialChars(),history(),dropCursor(),EditorState.allowMultipleSelections.of(true),indentOnInput(),bracketMatching(),closeBrackets(),rectangularSelection(),crosshairCursor(),highlightActiveLine(),highlightSelectionMatches(),keymap.of([...closeBracketsKeymap,...defaultKeymap,...searchKeymap,...historyKeymap,...completionKeymap,...lintKeymap])];
const keywordOptions = 'alignas alignof auto bool break case catch char class const constexpr continue decltype default delete do double else enum explicit extern false float for friend if inline int long namespace new noexcept nullptr operator private protected public return short signed sizeof static struct switch template this throw true try typedef typename union unsigned using virtual void volatile while'.split(' ').map(label => ({ label, type: 'keyword' }));
const completions = [
  ...keywordOptions,
  ...'cin cout cerr endl string vector pair map set unordered_map unordered_set queue priority_queue deque stack sort lower_bound upper_bound min max swap reverse next_permutation accumulate iota gcd make_pair push_back emplace_back size begin end'.split(' ').map(label => ({ label, type: 'variable', detail: 'C++ 常用名称' })),
  snippetCompletion('for (int ${i} = 0; ${i} < ${n}; ++${i}) {\n    ${}\n}', { label: 'fori', type: 'snippet', detail: '计数循环' }),
  snippetCompletion('for (auto &${item} : ${container}) {\n    ${}\n}', { label: 'forr', type: 'snippet', detail: '范围循环' }),
  snippetCompletion('if (${condition}) {\n    ${}\n}', { label: 'ifblock', type: 'snippet', detail: '条件分支' }),
  snippetCompletion('while (${condition}) {\n    ${}\n}', { label: 'whileblock', type: 'snippet', detail: '循环' }),
  snippetCompletion('int main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    ${}\n    return 0;\n}', { label: 'main', type: 'snippet', detail: 'C++17 入口模板' }),
];
function completeCpp(context) {
  const word = context.matchBefore(/[A-Za-z_][A-Za-z_0-9]*/);
  if (!word && !context.explicit) return null;
  return { from: word ? word.from : context.pos, options: completions, validFor: /^[A-Za-z_0-9]*$/ };
}
const colors = HighlightStyle.define([
  { tag: tags.keyword, class: 'tok-keyword' },
  { tag: [tags.typeName, tags.className], class: 'tok-type' },
  { tag: [tags.string, tags.character], class: 'tok-string' },
  { tag: [tags.number, tags.bool, tags.null], class: 'tok-number' },
  { tag: tags.comment, class: 'tok-comment' },
  { tag: [tags.function(tags.variableName), tags.definition(tags.variableName)], class: 'tok-function' },
  { tag: [tags.meta, tags.processingInstruction], class: 'tok-meta' },
  { tag: [tags.operator, tags.punctuation], class: 'tok-operator' },
]);
const theme = EditorView.theme({
  '&': { height: '100%', color: 'var(--editor-foreground,var(--text))', backgroundColor: 'var(--editor-surface,var(--panel))' },
  '.cm-scroller': { overflow: 'auto', fontFamily: 'Consolas, "Cascadia Code", monospace', fontSize: '1rem', lineHeight: '1.7' },
  '.cm-content': { padding: '12px 0', caretColor: 'transparent' },
  '.cm-line': { padding: '0 13px' },
  '.cm-gutters': { backgroundColor: 'transparent', color: 'var(--editor-gutter,var(--muted))', borderRight: '1px solid var(--line)' },
  '.cm-activeLineGutter': { backgroundColor: 'var(--editor-active-line,var(--accent-soft))', color: 'var(--editor-accent,var(--accent))' },
  '.cm-activeLine': { backgroundColor: 'var(--editor-active-line,var(--accent-soft))' },
  '.cm-cursor, .cm-dropCursor': { borderLeftColor: 'var(--text)', borderLeftWidth: '2px' },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': { backgroundColor: 'color-mix(in srgb, var(--accent) 24%, transparent)' },
  '.cm-matchingBracket': { backgroundColor: 'color-mix(in srgb, var(--accent) 10%, transparent)', outline: 'none', borderBottom: '1px solid color-mix(in srgb, var(--accent) 45%, transparent)' },
  '.cm-tooltip': { backgroundColor: 'var(--panel-2)', border: '1px solid var(--line)', color: 'var(--text)' },
  '.cm-tooltip-autocomplete > ul > li[aria-selected]': { backgroundColor: 'var(--accent-soft)', color: 'var(--text)' },
  '.cm-panels': { backgroundColor: 'var(--panel-2)', color: 'var(--text)' },
  '.cm-searchMatch': { backgroundColor: 'color-mix(in srgb, var(--warning) 25%, transparent)' },
  '.cm-searchMatch-selected': { backgroundColor: 'color-mix(in srgb, var(--warning) 45%, transparent)' },
});

const CodeEditor = forwardRef(function CodeEditor({ shortcuts={}, value = '', onChange, onCursorChange, onCommand, onLeave, readOnly = false, disabled = false, docKey = '', language = 'cpp17', ariaLabel = 'C++ 代码',editorTheme }, ref) {
  const host = useRef(null), viewRef = useRef(null), readonlyCompartment = useRef(new Compartment());
  const callbacks = useRef({ onChange, onCursorChange, onCommand, onLeave, shortcuts });
  callbacks.current = { onChange, onCursorChange, onCommand, onLeave, shortcuts };
  useImperativeHandle(ref, () => ({
    focus: () => viewRef.current?.focus(),
    get value() { return viewRef.current?.state.doc.toString() || ''; },
    getSelection: () => ({ start: viewRef.current?.state.selection.main.from || 0, end: viewRef.current?.state.selection.main.to || 0 }),
    get selectionStart() { return viewRef.current?.state.selection.main.from || 0; },
    get selectionEnd() { return viewRef.current?.state.selection.main.to || 0; },
    setSelectionRange: (start, end = start) => { const view = viewRef.current; if (view) view.dispatch({ selection: { anchor: Math.min(start, view.state.doc.length), head: Math.min(end, view.state.doc.length) }, scrollIntoView: true }); },
    get scrollTop() { return viewRef.current?.scrollDOM.scrollTop || 0; },
    set scrollTop(value) { if (viewRef.current) viewRef.current.scrollDOM.scrollTop = value; },
    getDOM: () => viewRef.current?.contentDOM,
    getView: () => viewRef.current,
  }), []);
  useEffect(() => {
    const notifyCursor = view => { const position = view.state.selection.main.head, line = view.state.doc.lineAt(position); callbacks.current.onCursorChange?.({ line: line.number, column: position - line.from + 1 }); };
    const view = new EditorView({ parent: host.current, state: EditorState.create({ doc: value, extensions: [
      Prec.highest(EditorView.domEventHandlers({ keydown(event, editor) {
        if (event.isComposing || editor.composing || event.keyCode === 229) return false;
        if((event.ctrlKey||event.metaKey)&&event.key==='Tab'){event.preventDefault();event.stopPropagation();callbacks.current.onLeave?.();return true;}
        const command=['official','submit','run','save','pane-0','pane-1','pane-2',...EXTRA_SHORTCUTS.filter(item=>item[3]==='编辑器').map(item=>item[0])].find(id=>matchesShortcut(event,id,callbacks.current.shortcuts));
        if (!command) return false;
        event.preventDefault(); event.stopPropagation(); callbacks.current.onCommand?.(command); return true;
      } })),
      Prec.highest(keymap.of([{ key: 'Tab', run: editor => (completionStatus(editor.state) === 'active' && acceptCompletion(editor)) || indentMore(editor), shift: indentLess }])),
      editorSetup, drawSelection({cursorBlinkRate:0}), language==='python3' ? python() : cpp(), indentUnit.of('    '), theme, syntaxHighlighting(colors),
      autocompletion({ ...(language==='python3'?{}:{override:[completeCpp]}), activateOnTyping: true, maxRenderedOptions: 12 }),
      readonlyCompartment.current.of([EditorState.readOnly.of(readOnly || disabled), EditorView.editable.of(!disabled)]),
      EditorView.contentAttributes.of(editor => ({ 'aria-label': language==='python3'?'Python 代码':ariaLabel, 'aria-multiline': 'true', 'aria-readonly': editor.state.readOnly ? 'true' : 'false', role: 'textbox', spellcheck: 'false', autocapitalize: 'off' })),
      EditorView.updateListener.of(update => {
        if (update.docChanged && !update.transactions.some(transaction => transaction.annotation(externalChange))) callbacks.current.onChange?.(update.state.doc.toString());
        if (update.docChanged || update.selectionSet) notifyCursor(update.view);
      }),
    ] }) });
    viewRef.current = view;
    notifyCursor(view);
    return () => { viewRef.current = null; view.destroy(); };
    // Changing document identity creates a fresh undo history; mirrored value
    // updates below preserve the current caret and history during ordinary edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docKey, language]);
  useEffect(() => {
    const view = viewRef.current;
    if (view && view.state.doc.toString() !== value) view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value }, annotations: externalChange.of(true) });
  }, [value, docKey]);
  useEffect(() => { viewRef.current?.dispatch({ effects: readonlyCompartment.current.reconfigure([EditorState.readOnly.of(readOnly || disabled), EditorView.editable.of(!disabled)]) }); }, [readOnly, disabled, docKey]);
  const selected=editorTheme?findEditorTheme(editorTheme):null;
  return <div className="code-editor" style={selected?editorThemeStyle(selected.id):undefined} ref={host} data-editor-theme={selected?.id} data-editor-effect={selected?selected.effect||'none':undefined} data-readonly={readOnly || disabled} onKeyDown={event => { if (event.defaultPrevented) event.stopPropagation(); }}/>;
});
export default CodeEditor;
