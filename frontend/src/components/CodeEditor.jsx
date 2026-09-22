import Editor from '@monaco-editor/react'

const languageMap = {
  python: 'python',
  javascript: 'javascript',
  java: 'java',
  cpp: 'cpp',
}

export default function CodeEditor({ language, code, onChange }) {
  return (
    <div className="editor-wrap">
      <Editor
        height="420px"
        language={languageMap[language] || 'python'}
        value={code}
        theme="vs-dark"
        onChange={(value) => onChange(value || '')}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          wordWrap: 'on',
          automaticLayout: true,
        }}
      />
    </div>
  )
}
