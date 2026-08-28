'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { getBlockRenderer } from './blocks';

interface MarkdownProps {
  children: string;
  onQuestionClick?: (question: string) => void;
}

export const Markdown = ({ children, onQuestionClick }: MarkdownProps) => {
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
          // The one dispatch point for fenced blocks. Inline code has no
          // className; a fenced block carries `language-*`, and that language
          // selects a renderer from blocks/ (this is where Mermaid enters).
          code: ({ className, children }) => {
            if (!className) {
              return (
                <code className="bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 px-1.5 py-0.5 rounded text-sm font-mono text-primary dark:text-slate-100">
                  {children}
                </code>
              );
            }
            const language = /language-(\w+)/.exec(className)?.[1] ?? '';
            const source = String(children).replace(/\n$/, '');
            const Block = getBlockRenderer(language);
            return <Block source={source} language={language} />;
          },
          // Fenced blocks render their own outer container (see
          // blocks/CodeBlock.tsx), so pre only passes through. Wrapping again
          // would nest <pre> inside <pre>, or a <div> inside a <pre>.
          pre: ({ children }) => <>{children}</>,
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
