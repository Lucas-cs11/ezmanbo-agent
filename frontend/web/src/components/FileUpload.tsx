"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X, Loader2 } from "lucide-react";

const ALLOWED_TYPES = ".pdf,.csv,.txt,.md,.json,.xlsx,.xls";
const ALLOWED_LABELS = "PDF (数据手册), CSV (BOM表), TXT/MD, JSON, Excel";

export function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [parsing, setParsing] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (f: File | null) => {
    if (!f) return;
    setFile(f);
    setPreview(null);

    // For text-based files, read preview
    if (f.name.endsWith(".txt") || f.name.endsWith(".md") || f.name.endsWith(".json") || f.name.endsWith(".csv")) {
      const text = await f.text();
      setPreview(text.slice(0, 500));
    } else if (f.name.endsWith(".pdf")) {
      setPreview("[PDF 文件] — 将通过后端解析提取文本内容");
    } else {
      setPreview("[二进制文件] — 将发送至后端解析");
    }
  };

  const handleParse = async () => {
    if (!file) return;
    setParsing(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch(`${API_BASE}/upload/parse`, {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      setPreview(data.content || data.detail || JSON.stringify(data));
    } catch (e: unknown) {
      setPreview(`解析失败: ${e instanceof Error ? e.message : "未知错误"}`);
    }
    setParsing(false);
  };

  const remove = () => {
    setFile(null);
    setPreview(null);
  };

  return (
    <div className="px-4 pb-3">
      {/* Drop zone */}
      <div
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-3 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-colors"
      >
        {file ? (
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-500 shrink-0" />
            <span className="text-xs text-gray-700 truncate flex-1">{file.name}</span>
            <button onClick={(e) => { e.stopPropagation(); remove(); }} className="p-0.5 hover:bg-red-100 rounded">
              <X className="w-3.5 h-3.5 text-gray-400" />
            </button>
          </div>
        ) : (
          <div>
            <Upload className="w-5 h-5 text-gray-400 mx-auto mb-1" />
            <p className="text-[10px] text-gray-500">点击上传文件</p>
            <p className="text-[9px] text-gray-400 mt-0.5">{ALLOWED_LABELS}</p>
          </div>
        )}
        <input
          ref={fileRef}
          type="file"
          accept={ALLOWED_TYPES}
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0] || null)}
        />
      </div>

      {/* Parse button */}
      {file && (
        <button
          onClick={handleParse}
          disabled={parsing}
          className="w-full mt-2 flex items-center justify-center gap-1 py-1.5 rounded-lg bg-blue-600 text-white text-xs hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {parsing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
          {parsing ? "解析中..." : "提交解析"}
        </button>
      )}

      {/* Preview */}
      {preview && (
        <div className="mt-2 p-2 rounded-lg bg-gray-50 border border-gray-200 max-h-[120px] overflow-y-auto">
          <pre className="text-[10px] text-gray-600 whitespace-pre-wrap font-mono">{preview}</pre>
        </div>
      )}
    </div>
  );
}
