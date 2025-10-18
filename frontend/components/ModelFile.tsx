import React from 'react';
import { Card } from './Card';

interface ModelFileProps {
  code: string;
}

export default function ModelFile({ code }: ModelFileProps) {
  const handleDownload = () => {
    try {
      const blob = new Blob([code || ''], { type: 'text/x-python' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'model.py';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      // ignore
    }
  };

  if (!code || code.trim().length === 0) {
    return (
      <Card title="Model File (model.py)">
        <p className="text-sm text-neutral-600">No model.py code was generated.</p>
      </Card>
    );
  }

  return (
    <Card title="Model File (model.py)">
      <div className="mb-3 flex justify-end">
        <button
          onClick={handleDownload}
          className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded hover:bg-primary-700"
        >
          Download model.py
        </button>
      </div>
      <div className="rounded-md bg-neutral-900 overflow-hidden">
        <pre className="p-4 overflow-x-auto">
{code}
        </pre>
      </div>
    </Card>
  );
}


