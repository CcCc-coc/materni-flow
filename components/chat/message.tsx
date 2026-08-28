"use client";

import type { UIMessage } from "ai";
import { motion } from "framer-motion";
import { User } from "lucide-react";
import { useState } from "react";

import { AssistantAvatar } from "./AssistantAvatar";
import { Markdown } from "./markdown";
import { cn } from "@/lib/utils";

/**
 * Collapsible component for displaying reasoning/thinking content.
 * Shows a summary by default, expands to show full content on click.
 */
const ReasoningBlock = ({ text }: { text: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Truncate text for preview (first 100 chars)
  const previewText = text.length > 100 ? text.slice(0, 100) + "..." : text;

  return (
    <div className="border border-amber-200 rounded-lg bg-amber-50 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center gap-2 text-left hover:bg-amber-100 transition-colors"
      >
        <svg
          className={cn(
            "w-4 h-4 text-amber-600 transition-transform",
            isExpanded && "rotate-90"
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-xs font-medium text-amber-700">
          Thinking
        </span>
        {!isExpanded && (
          <span className="text-xs text-amber-600 truncate flex-1">
            {previewText}
          </span>
        )}
      </button>
      {isExpanded && (
        <div className="px-3 py-2 border-t border-amber-200">
          <div className="text-xs text-amber-800 whitespace-pre-wrap">
            {text}
          </div>
        </div>
      )}
    </div>
  );
};

export const PreviewMessage = ({
  message,
  append,
}: {
  message: UIMessage;
  append?: (message: any) => Promise<string | null | undefined>;
}) => {
  return (
    <motion.div
      className="w-full mx-auto max-w-3xl group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      <div
        className={cn(
          "flex gap-3 w-full",
          message.role === "user" ? "justify-end" : "justify-start"
        )}
      >
        {message.role === "assistant" && <AssistantAvatar />}

        <div
          className={cn(
            "flex flex-col gap-2 max-w-[85%] sm:max-w-[75%] p-4 rounded-xl",
            message.role === "user"
              ? "bg-primary text-white"
              : "bg-white border border-slate-200"
          )}
        >
          {/* AI SDK v5: Use parts instead of content */}
          {message.parts && message.parts.length > 0 && (
            <div className="flex flex-col gap-4">
              {message.parts.map((part: any, index: number) => {
                // Render reasoning/thinking content
                if (part.type === 'reasoning' && part.text) {
                  return (
                    <ReasoningBlock key={index} text={part.text} />
                  );
                }
                // Render text content
                if (part.type === 'text' && part.text) {
                  return (
                    <div
                      key={index}
                      className={cn(
                        message.role === "assistant"
                          ? "text-primary"
                          : "text-white"
                      )}
                    >
                      <Markdown
                        onQuestionClick={(question) => {
                          append?.({
                            role: 'user',
                            content: question,
                          });
                        }}
                      >
                        {part.text}
                      </Markdown>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          )}
        </div>

        {/* User Avatar - Right side */}
        {message.role === "user" && (
          <div className="w-8 h-8 flex items-center justify-center border border-slate-200 shrink-0 rounded-lg bg-slate-100">
            <User className="w-4 h-4 text-slate-500" aria-label="You" />
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const ThinkingMessage = () => {
  const role = "assistant";

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div className="flex gap-3 w-full justify-start">
        <AssistantAvatar />

        <div className="p-4 bg-white border border-slate-200 rounded-xl">
          <div className="flex items-center gap-2 text-slate-600">
            <span className="inline-block w-2 h-2 bg-brand rounded-full animate-pulse" />
            <span className="font-display text-sm">Thinking...</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
