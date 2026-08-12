'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface MarkdownProps {
  children: string;
  variant?: 'chat' | 'card';
  onQuestionClick?: (question: string) => void;
}

export const Markdown = ({ children, variant = 'chat', onQuestionClick }: MarkdownProps) => {
  // Preprocess markdown to handle #ask: links with spaces
  const preprocessedChildren = children.replace(
    /\[([^\]]+)\]\(#ask:([^)]+)\)/g,
    '[$1](<#ask:$2>)'
  );

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
          a: ({ href, children }) => {
            // Handle clickable question links
            if (href?.startsWith('#ask:')) {
              const question = decodeURIComponent(href.replace('#ask:', ''));
              return (
                <button
                  onClick={() => onQuestionClick?.(question)}
                  className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline font-medium cursor-pointer transition-colors"
                >
                  {children}
                </button>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline"
              >
                {children}
              </a>
            );
          },
          code: ({ className, children, ...props }) => {
            // Inline code doesn't have a className (language-*), code blocks do
            const isInline = !className;
            if (isInline) {
              return (
                <code className="bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 px-1.5 py-0.5 rounded text-sm font-mono text-[#0A1628] dark:text-slate-100">
                  {children}
                </code>
              );
            }
            return (
              <code className={cn("block bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-3 rounded-lg my-3 overflow-x-auto text-sm font-mono text-[#0A1628] dark:text-slate-100", className)}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-lg my-3 overflow-x-auto">
              {children}
            </pre>
          ),
          ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-blue-600 dark:text-blue-400">{children}</strong>,
          em: ({ children }) => <em className="italic text-slate-600 dark:text-slate-300">{children}</em>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 pl-4 my-3 text-slate-600 dark:text-slate-300 italic bg-slate-50 dark:bg-slate-800/50 py-2 rounded-r">
              {children}
            </blockquote>
          ),
          h1: ({ children }) => <h1 className="text-2xl font-bold mb-3 mt-4">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xl font-bold mb-3 mt-4">{children}</h2>,
          h3: ({ children }) => <h3 className="text-lg font-semibold mb-2 mt-3">{children}</h3>,
          h4: ({ children }) => <h4 className="text-base font-semibold mb-2 mt-3">{children}</h4>,
          table: ({ children }) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border border-slate-200 dark:border-slate-700 rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-slate-100 dark:bg-slate-800">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left text-sm font-semibold border-b border-slate-200 dark:border-slate-700">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2 text-sm border-b border-slate-200 dark:border-slate-700">
              {children}
            </td>
          ),
        }}
      >
        {preprocessedChildren}
      </ReactMarkdown>
    </div>
  );
};
