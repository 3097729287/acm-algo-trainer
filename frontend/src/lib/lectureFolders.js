const paths = item => [...new Set([item.category, ...(item.categories || [])].filter(Boolean))]
  .map(value => String(value).split(/\s*\/\s*/).map(part => part.trim()).filter(Boolean));

export function lectureMatchesFolder(item, path) {
  return !path.length || paths(item).some(parts => path.every((part, index) => parts[index] === part));
}

export function lectureFolderOptions(entries) {
  const roots = [];
  for (const item of entries) for (const path of paths(item)) {
    let nodes = roots;
    for (let index = 0; index < path.length; index++) {
      const prefix = path.slice(0, index + 1), value = JSON.stringify(prefix);
      let folder = nodes.find(node => node.value === value);
      if (!folder) { folder = { label: path[index], selectionLabel: prefix.join(' / '), value, children: [] }; nodes.push(folder); }
      nodes = folder.children;
    }
  }
  const finish = nodes => nodes.sort((a,b) => a.label.localeCompare(b.label, 'zh-CN', {numeric:true}))
    .map(node => ({ ...node, children: node.children.length ? finish(node.children) : undefined }));
  return finish(roots);
}
