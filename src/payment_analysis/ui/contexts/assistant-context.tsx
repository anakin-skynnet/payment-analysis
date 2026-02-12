import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface AssistantContextValue {
  /** AI Chatbot (Orchestrator) panel open state */
  openAIChatbot: boolean;
  setOpenAIChatbot: (open: boolean) => void;
  openAIChatbotPanel: () => void;
  /** Genie Assistant panel open state */
  openGenieAssistant: boolean;
  setOpenGenieAssistant: (open: boolean) => void;
  openGenieAssistantPanel: () => void;
  /** Legacy: opens AI Chatbot (Orchestrator) for backward compatibility */
  open: boolean;
  setOpen: (open: boolean) => void;
  openAssistant: () => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [openAIChatbot, setOpenAIChatbot] = useState(false);
  const [openGenieAssistant, setOpenGenieAssistant] = useState(false);
  const openAIChatbotPanel = useCallback(() => setOpenAIChatbot(true), []);
  const openGenieAssistantPanel = useCallback(() => setOpenGenieAssistant(true), []);
  const value = useMemo<AssistantContextValue>(
    () => ({
      openAIChatbot,
      setOpenAIChatbot,
      openAIChatbotPanel,
      openGenieAssistant,
      setOpenGenieAssistant,
      openGenieAssistantPanel,
      open: openAIChatbot,
      setOpen: setOpenAIChatbot,
      openAssistant: openAIChatbotPanel,
    }),
    [
      openAIChatbot,
      openGenieAssistant,
      openAIChatbotPanel,
      openGenieAssistantPanel,
    ]
  );
  return (
    <AssistantContext.Provider value={value}>
      {children}
    </AssistantContext.Provider>
  );
}

export function useAssistant() {
  const ctx = useContext(AssistantContext);
  if (!ctx) {
    throw new Error("useAssistant must be used within AssistantProvider");
  }
  return ctx;
}

/** Safe hook: returns null if outside provider (e.g. on non-sidebar routes). */
export function useAssistantOptional() {
  return useContext(AssistantContext);
}
