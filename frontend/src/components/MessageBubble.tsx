"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Highlight, themes } from "prism-react-renderer";
import type { Message } from "@/store/useStore";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
  streamingContent?: string;
}

const EZPLMLogo = () => (
  <div className="w-7 h-7 rounded-lg bg-brand flex items-center justify-center shrink-0">
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  </div>
);

function CodeBlock({ language, code }: { language: string; code: string }) {
  return (
    <Highlight
      theme={themes.nightOwl}
      code={code.trim()}
      language={language || "text"}
    >
      {({ tokens, getLineProps, getTokenProps }) => (
        <pre className="rounded-lg overflow-x-auto my-2 text-[12px] leading-relaxed p-3 bg-[#011627]">
          <code>
            {tokens.map((line, i) => {
              const lineProps = getLineProps({ line });
              return (
                <div key={i} {...lineProps}>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token })} />
                  ))}
                </div>
              );
            })}
          </code>
        </pre>
      )}
    </Highlight>
  );
}

export function MessageBubble({
  message,
  isStreaming = false,
  streamingContent,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const displayContent =
    isStreaming && streamingContent !== undefined
      ? streamingContent
      : message.content;

  const markdownComponents = {
    code({
      node,
      className,
      children,
      ...props
    }: {
      node?: unknown;
      className?: string;
      children?: React.ReactNode;
    }) {
      const match = /language-(\w+)/.exec(className || "");
      const codeString = String(children).replace(/\n$/, "");

      if (match) {
        return <CodeBlock language={match[1]} code={codeString} />;
      }

      return (
        <code
          className="bg-[var(--color-background)] px-1.5 py-0.5 rounded text-[12px] font-mono"
          {...props}
        >
          {children}
        </code>
      );
    },
    pre({ children }: { children?: React.ReactNode }) {
      return <>{children}</>;
    },
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-brand text-white rounded-2xl rounded-br-md px-4 py-3">
          <div className="text-[13px] leading-relaxed whitespace-pre-wrap">
            {displayContent}
          </div>
          {message.timestamp && (
            <p className="text-[10px] mt-1.5 opacity-60 text-right">
              {message.timestamp}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 mb-4">
      <div className="pt-0.5">
        {isSystem ? (
          <div className="w-7 h-7 rounded-lg bg-risk-high/20 flex items-center justify-center shrink-0">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--color-risk-high)"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
        ) : (
          <EZPLMLogo />
        )}
      </div>
      <div className="flex-1 min-w-0">
        {!isUser && !isSystem && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-semibold text-brand">EZPLM</span>
          </div>
        )}
        <div
          className={`rounded-2xl rounded-bl-md px-4 py-3 text-[13px] leading-relaxed ${
            isSystem
              ? "bg-risk-high/5 border border-risk-high/20 text-[var(--color-text-primary)]"
              : "bg-[var(--color-card)] border border-[var(--color-border)] text-[var(--color-text-primary)]"
          }`}
        >
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {displayContent ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {displayContent}
              </ReactMarkdown>
            ) : isStreaming ? null : (
              <span className="text-[var(--color-text-secondary)] italic">
                暂无内容
              </span>
            )}
          </div>
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-brand ml-0.5 animate-pulse rounded-sm" />
          )}
        </div>
        {message.timestamp && (
          <p className="text-[10px] mt-1 opacity-40">{message.timestamp}</p>
        )}
      </div>
    </div>
  );
}