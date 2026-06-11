"use client";

import { useEffect, useRef, useState } from "react";
import { useStore } from "@/store/useStore";

export function PdfViewer() {
  const pdfUrl = useStore((s) => s.pdfUrl);
  const showPdfViewer = useStore((s) => s.showPdfViewer);
  const setShowPdfViewer = useStore((s) => s.setShowPdfViewer);
  const pdfLoading = useStore((s) => s.pdfLoading);

  const [scale, setScale] = useState(100);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowPdfViewer(false);
    };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [setShowPdfViewer]);

  if (!showPdfViewer) return null;

  const handleDownload = () => {
    if (pdfUrl) {
      const a = document.createElement("a");
      a.href = pdfUrl;
      a.download = "report.pdf";
      a.click();
    }
  };

  const handleFullscreen = () => {
    iframeRef.current?.requestFullscreen?.();
  };

  const zoomIn = () => setScale((s) => Math.min(s + 20, 200));
  const zoomOut = () => setScale((s) => Math.max(s - 20, 40));

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/60 backdrop-blur-sm">
      {/* Toolbar */}
      <div className="flex items-center justify-between h-12 px-4 bg-[#1e1e1e] text-white shrink-0">
        <h3 className="text-sm font-medium">PDF 报告</h3>
        <div className="flex items-center gap-1">
          <button
            onClick={zoomOut}
            className="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
            title="缩小"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <span className="text-[12px] w-12 text-center select-none">
            {scale}%
          </span>
          <button
            onClick={zoomIn}
            className="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
            title="放大"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button
            onClick={handleFullscreen}
            className="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
            title="全屏"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="15 3 21 3 21 9" />
              <polyline points="9 21 3 21 3 15" />
              <line x1="21" y1="3" x2="14" y2="10" />
              <line x1="3" y1="21" x2="10" y2="14" />
            </svg>
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
            title="下载"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>
          <button
            onClick={() => setShowPdfViewer(false)}
            className="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer ml-2"
            title="关闭"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto flex justify-center bg-[#525659]">
        {pdfLoading ? (
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-2 text-white">
              <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              <span className="text-sm">加载 PDF...</span>
            </div>
          </div>
        ) : pdfUrl ? (
          <iframe
            ref={iframeRef}
            src={`${pdfUrl}#toolbar=0&navpanes=0`}
            className="w-full h-full border-0"
            style={{ maxWidth: `${scale}%` }}
            title="PDF Report"
          />
        ) : (
          <div className="flex items-center justify-center text-white/60">
            <p className="text-sm">PDF 暂不可用</p>
          </div>
        )}
      </div>
    </div>
  );
}