import {EditorState} from '@codemirror/state';
import {EditorView} from '@codemirror/view';

window.mountLuoguEditor = () => {
  window.fixtureView = new EditorView({
    state: EditorState.create({doc: '// original draft'}),
    parent: document.querySelector('#native-editor'),
  });
};
