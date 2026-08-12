"use client";

import { PreviewMessage, ThinkingMessage } from "./message";
import { MultimodalInput } from "./multimodal-input";
import { Overview } from "./overview";
import { useScrollToBottom } from "@/hooks/use-scroll-to-bottom";
import { useChat } from "@ai-sdk/react";
import { toast } from "sonner";
import { useState, useEffect, useRef } from "react";
import FingerprintJS from '@fingerprintjs/fingerprintjs';
import { METADATA } from "@/lib/constants";

export function Chat() {
  const chatId = "001";

  const [input, setInput] = useState("");
  const [isContextBannerVisible, setIsContextBannerVisible] = useState(true);

  const browserFingerprintRef = useRef<string>("");

  useEffect(() => {
    const generateFingerprint = async () => {
      try {
        const fp = await FingerprintJS.load();
        const result = await fp.get();
        browserFingerprintRef.current = result.visitorId;
        console.log('Browser Fingerprint Generated:', result.visitorId);
      } catch (error) {
        console.error('Failed to generate browser fingerprint:', error);
      }
    };

    generateFingerprint();

    const originalFetch = window.fetch;
    window.fetch = async (input, init?) => {
      if (typeof input === 'string' && input.includes('/api/chat')) {
        const fingerprint = browserFingerprintRef.current;
        init = init || {};
        init.headers = {
          ...init.headers,
          'X-Client-Fingerprint': fingerprint,
        };
      }
      return originalFetch(input, init);
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  const {
    messages,
    setMessages,
    sendMessage,
    status,
    stop,
  } = useChat({
    onError: (error) => {
      if (error.message.includes("Too many requests") || error.message.includes("Rate limit") || error.message.includes("429")) {
        toast.error(
          "You have reached the usage limit, please try again in 60 minutes",
          { duration: 8000 }
        );
      } else {
        toast.error(error.message);
      }
    },
  });

  const isLoading = status === "streaming" || status === "submitted";

  const handleSubmit = (e?: { preventDefault?: () => void }, options?: any) => {
    e?.preventDefault?.();
    if (input.trim()) {
      sendMessage({ text: input });
      setInput("");
    }
  };

  const append = async (message: any): Promise<string | null | undefined> => {
    if (message.content) {
      await sendMessage({ text: message.content });
      return null;
    } else if (message.text) {
      await sendMessage({ text: message.text });
      return null;
    }
    return null;
  };

  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  useEffect(() => {
    if (messagesEndRef.current && messages.length > 0) {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "end"
        });
      });
    }
  }, [messages.length]);

  return (
    <div className="flex flex-col min-w-0 h-[calc(100dvh-64px)] bg-slate-50 dark:bg-[#0A1628]">
      <div
        ref={messagesContainerRef}
        className="flex flex-col min-w-0 gap-4 flex-1 overflow-y-scroll pt-4 px-4"
      >
        {/* Initial AI Assistant Welcome Display */}
        {messages.length === 0 && <Overview />}

        {/* Context Banner */}
        {messages.length > 0 && isContextBannerVisible && (
          <div className="max-w-3xl mx-auto w-full">
            <div className="border border-slate-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-900 rounded-xl">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1">
                  <div className="w-10 h-10 bg-blue-600 flex items-center justify-center shrink-0 rounded-lg">
                    <span className="font-display text-sm text-white">AI</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-display text-sm text-[#0A1628] dark:text-white">{METADATA.AI_ASSISTANT_NAME}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      I'm here to help you with <span className="font-semibold text-blue-600 dark:text-blue-400">SMB lending analytics</span> and portfolio insights.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsContextBannerVisible(false)}
                  className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors shrink-0 cursor-pointer"
                  aria-label="Close"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((message, index) => (
          <PreviewMessage
            key={message.id}
            chatId={chatId}
            message={message}
            isLoading={isLoading && messages.length - 1 === index}
            append={append}
          />
        ))}

        {isLoading &&
          messages.length > 0 &&
          messages[messages.length - 1].role === "user" && <ThinkingMessage />}

        {/* Auto-scroll anchor */}
        <div
          ref={messagesEndRef}
          className="shrink-0 min-w-[24px] min-h-[24px]"
        />
      </div>

      <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700">
        <form className="flex mx-auto gap-2 w-full md:max-w-3xl">
          <MultimodalInput
            chatId={chatId}
            input={input}
            setInput={setInput}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            stop={stop}
            messages={messages}
            setMessages={setMessages}
            append={append}
          />
        </form>
      </div>
    </div>
  );
}
