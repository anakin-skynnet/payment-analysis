"use client";

import { useCallback, useRef, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getGenieUrl, openInDatabricks } from "@/config/workspace";
import { postChat } from "@/lib/api";
import { Sparkles, X } from "lucide-react";

export interface GenieAssistantMessage {
  role: "user" | "assistant";
  content: string;
  genieUrl?: string | null;
}

const TITLE = "Genie Assistant";
const PLACEHOLDER = "Ask about your data: approval rates, declines, trends…";

/** Uses backend POST /api/agents/chat (Databricks Genie – lakehouse data and insights). */
async function sendToGenie(message: string) {
  const { data } = await postChat(
    { message: message.trim() },
    { credentials: "include" }
  );
  return {
    reply: data.reply ?? "",
    genie_url: data.genie_url ?? null,
  };
}

export interface GenieAssistantProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Position: "left" | "right" for floating panel placement */
  position?: "left" | "right";
}

export function GenieAssistant({
  open: controlledOpen,
  onOpenChange,
  position = "left",
}: GenieAssistantProps = {}) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isControlled = controlledOpen !== undefined && onOpenChange !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;
  const setOpen = isControlled ? onOpenChange! : setInternalOpen;
  const [messages, setMessages] = useState<GenieAssistantMessage[]>([]);
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
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const out = await sendToGenie(text);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: out.reply,
          genieUrl: out.genie_url ?? undefined,
        },
      ]);
      setTimeout(scrollToBottom, 50);
    } catch (e) {
      const err = e instanceof Error ? e.message : "Genie unavailable.";
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

  const openGenieInWorkspace = useCallback(() => {
    openInDatabricks(getGenieUrl());
  }, []);

  if (!open) return null;

  return (
    <div
      className={cn(
        "fixed bottom-6 z-[100] flex w-[min(420px,calc(100vw-2rem))] flex-col rounded-xl border border-border bg-card text-card-foreground shadow-xl",
        position === "right" && "right-6",
        position === "left" && "left-6"
      )}
      role="dialog"
      aria-label={TITLE}
    >
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary/20 text-primary">
            <Sparkles className="h-4 w-4" />
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
            Chat with Databricks Genie for relevant information from the lakehouse: approval rates,
            declines, trends, and dashboards.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}
          >
            {m.role === "assistant" && (
              <Avatar className="h-6 w-6 shrink-0">
                <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                  <Sparkles className="h-3 w-3" />
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
                  onClick={openGenieInWorkspace}
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
                <Sparkles className="h-3 w-3" />
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
        <Button type="button" onClick={submit} disabled={loading || !input.trim()}>
          Send
        </Button>
      </div>
    </div>
  );
}
