"use client";

import { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Nav from "../../components/Nav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [pendingApprovalRequest, setPendingApprovalRequest] = useState<string | null>(null);
  const [approveEmail, setApproveEmail] = useState(false);
  const [pendingDraft, setPendingDraft] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamBufferRef = useRef("");
  const emailIntentRef = useRef(false);
  const quickPrompts = [
    "Give me the top 10 at-risk customers",
    "Generate email for CUST-1003",
    "Summarize risk drivers for CUST-1011",
    "Show top 5 attrition risks in the last 90 days"
  ];

  function wantsEmail(text: string) {
    const lower = text.toLowerCase();
    return ["email", "draft", "send"].some((k) => lower.includes(k));
  }

  function extractEmailDraft(content: string) {
    const lines = content.split("\n");
    const idx = lines.findIndex((line) => {
      const cleaned = line.toLowerCase().replace(/\*/g, "");
      return cleaned.includes("email_draft") || cleaned.includes("email draft");
    });
    if (idx === -1) return { cleaned: content, draft: null as string | null };
    const headerLine = lines[idx];
    const inlineDraft = headerLine
      .replace(/\*+/g, "")
      .replace(/email[_ ]?draft\s*[:\-]?/i, "")
      .trim();
    const draftLines = [inlineDraft, ...lines.slice(idx + 1)].filter((l) => l !== "");
    const draft = draftLines.join("\n").trim();
    const cleaned = lines.slice(0, idx).join("\n").trim();
    return { cleaned: cleaned || content, draft: draft || null };
  }

  async function fetchNonStream(payload: Record<string, unknown>) {
    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Blocked by guardrails: ${JSON.stringify(data.detail)}` }
      ]);
      return;
    }
    const data = await res.json();
    if (!conversationId) setConversationId(data.conversation_id);
    const parsed = extractEmailDraft(data.response);
    if (emailIntentRef.current && parsed.draft) {
      setPendingDraft(parsed.draft);
    } else {
      setPendingDraft(null);
      setApproveEmail(false);
    }
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.role === "assistant") {
        last.content = parsed.cleaned || data.response;
      }
      return next;
    });
  }

  async function streamResponse(payload: Record<string, unknown>) {
    const res = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(payload)
    });

    if (!res.ok || !res.body) {
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Blocked by guardrails: ${JSON.stringify(data.detail)}` }
      ]);
      setIsSending(false);
      setIsStreaming(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    streamBufferRef.current = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";
      for (const part of parts) {
        const lines = part.split("\n").filter(Boolean);
        const eventLine = lines.find((l) => l.startsWith("event:")) || "";
        const dataLine = lines.find((l) => l.startsWith("data:")) || "";
        const event = eventLine.replace("event:", "").trim();
        const data = dataLine.replace("data:", "").trim().replace(/\\n/g, "\n");

        if (event === "meta") {
          if (data && !conversationId) setConversationId(data);
        } else if (event === "chunk") {
          streamBufferRef.current = streamBufferRef.current + data;
        } else if (event === "done") {
          const full = streamBufferRef.current;
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === "assistant") {
              last.content = full;
            }
            return next;
          });
          if (emailIntentRef.current) {
            const parsed = extractEmailDraft(full);
            if (parsed.draft) {
              setPendingDraft(parsed.draft);
            }
          }
        }
      }
    }

    if (streamBufferRef.current.length === 0) {
      await fetchNonStream(payload);
    }

    setIsSending(false);
    setIsStreaming(false);
  }

  async function sendMessage() {
    if (!input.trim()) return;
    const next = { role: "user" as const, content: input };
    setMessages((prev) => [...prev, next]);
    const emailIntent = wantsEmail(next.content);
    emailIntentRef.current = emailIntent;
    setPendingApprovalRequest(emailIntent ? next.content : null);
    setPendingDraft(null);
    setApproveEmail(false);
    setInput("");
    setIsSending(true);
    setIsStreaming(true);

    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    const payload = {
      message: next.content,
      conversation_id: conversationId,
      approve_email: false
    };
    await streamResponse(payload);
  }

  async function sendApprovedEmail() {
    if (!pendingApprovalRequest || !pendingDraft) return;
    emailIntentRef.current = true;
    setIsSending(true);
    setIsStreaming(true);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    const payload = {
      message: pendingApprovalRequest,
      conversation_id: conversationId,
      approve_email: true,
      approve_email_content: pendingDraft
    };
    await streamResponse(payload);
    setApproveEmail(false);
    setPendingApprovalRequest(null);
    setPendingDraft(null);
  }

  return (
    <div>
      <Nav />
      <div className="container wide">
        <div className="chat-layout">
          <div className="chat-window">
            <h2>Chat Studio</h2>
            <div className="chat-prompts">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  className="prompt-pill"
                  onClick={() => setInput(prompt)}
                  type="button"
                >
                  {prompt}
                </button>
              ))}
            </div>
            <div className="chat-messages">
              {messages.map((m, idx) => (
                <div key={idx} className={`message ${m.role}`}>
                  {m.role === "assistant" ? (
                    <>
                      {m.content ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                      ) : (
                        isStreaming && <div className="typing">Generating<span>.</span><span>.</span><span>.</span></div>
                      )}
                      {pendingApprovalRequest && pendingDraft && idx === messages.length - 1 && m.content && (
                        <div className="approval-row">
                          <textarea
                            className="draft-editor"
                            value={pendingDraft}
                            onChange={(e) => setPendingDraft(e.target.value)}
                            rows={8}
                          />
                          <label className="toggle">
                            <input
                              type="checkbox"
                              checked={approveEmail}
                              onChange={(e) => setApproveEmail(e.target.checked)}
                            />
                            <span>Approve Email</span>
                          </label>
                          <button
                            className="button secondary"
                            onClick={sendApprovedEmail}
                            disabled={!approveEmail || isSending}
                          >
                            {isSending ? "Approving" : "Approve Email"}
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    m.content
                  )}
                </div>
              ))}
              {messages.length === 0 && (
                <div className="message assistant">
                  Ask for the top 10 at-risk customers or request a retention email draft.
                </div>
              )}
            </div>
            <div className="chat-input sticky-input">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Try: Give me the top 10 at-risk customers"
                onKeyDown={(e) => {
                  if (e.key === "Enter") sendMessage();
                }}
              />
              <button className="button" onClick={sendMessage} disabled={isSending}>
                {isSending ? "Sending" : "Send"}
              </button>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
