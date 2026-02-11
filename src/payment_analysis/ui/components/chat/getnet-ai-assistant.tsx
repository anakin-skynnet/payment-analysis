"use client";

import { useCallback, useRef, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getGenieUrl, openInDatabricks } from "@/config/workspace";
import { Bot, Mic, X } from "lucide-react";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  genieUrl?: string | null;
}

const TITLE = "Getnet AI Assistant";
const PLACEHOLDER = "Ask about approval rates, declines, trends…";

async function sendMessage(message: string): Promise<{ reply: string; genie_url?: string | null }> {
  const res = await fetch("/api/agents/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: message.trim() }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to get response");
  }
  return res.json();
}

export function GetnetAIAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, []);

  const submit = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError(null);
    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const { reply, genie_url } = await sendMessage(text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply, genieUrl: genie_url ?? undefined },
      ]);
      setTimeout(scrollToBottom, 50);
    } catch (e) {
      const err = e instanceof Error ? e.message : "Something went wrong.";
      setError(err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Sorry, I couldn't process that. ${err}`, genieUrl: null },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, scrollToBottom]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submit();
      }
    },
    [submit]
  );

  const openGenie = useCallback(() => {
    openInDatabricks(getGenieUrl());
  }, []);

  if (!open) {
    return (
      <Button
        type="button"
        variant="default"
        size="lg"
        className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg"
        aria-label={`Open ${TITLE}`}
        onClick={() => setOpen(true)}
      >
        <Bot className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50 flex w-[min(420px,calc(100vw-2rem))] flex-col rounded-xl border border-border bg-card text-card-foreground shadow-xl"
      )}
      role="dialog"
      aria-label={TITLE}
    >
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-muted text-muted-foreground">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
        <span className="flex-1 font-semibold text-sm">{TITLE}</span>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          aria-label="Close"
          onClick={() => setOpen(false)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div
        ref={scrollRef}
        className="flex max-h-[320px] min-h-[200px] flex-1 flex-col gap-3 overflow-y-auto p-4"
      >
        {messages.length === 0 && (
          <p className="text-muted-foreground text-sm">
            Ask about approval rates, decline reasons, trends, or open Genie for full
            natural-language analytics.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "flex gap-2",
              m.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {m.role === "assistant" && (
              <Avatar className="h-6 w-6 shrink-0">
                <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                  <Bot className="h-3 w-3" />
                </AvatarFallback>
              </Avatar>
            )}
            <div
              className={cn(
                "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.role === "assistant" && m.genieUrl && (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="mt-2 h-auto p-0 text-primary underline"
                  onClick={openGenie}
                >
                  Open in Genie
                </Button>
              )}
            </div>
            {m.role === "user" && <span className="h-6 w-6 shrink-0" />}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start gap-2">
            <Avatar className="h-6 w-6 shrink-0">
              <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                <Bot className="h-3 w-3" />
              </AvatarFallback>
            </Avatar>
            <div className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
              Thinking…
            </div>
          </div>
        )}
        {error && (
          <p className="text-destructive text-sm" role="alert">
            {error}
          </p>
        )}
      </div>

      <div className="flex gap-2 border-t border-border p-3">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDER}
          disabled={loading}
          className="min-w-0 flex-1"
          aria-label="Message"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="shrink-0"
          aria-label="Voice input (placeholder)"
          disabled
        >
          <Mic className="h-4 w-4" />
        </Button>
        <Button type="button" onClick={submit} disabled={loading || !input.trim()}>
          Send
        </Button>
      </div>
    </div>
  );
}
