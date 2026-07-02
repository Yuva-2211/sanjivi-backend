"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Send,
  Mic,
  Star,
  ChevronLeft,
  ShieldAlert,
  ShieldCheck,
  ChevronDown,
  Leaf,
  Sun,
  Beaker,
  Shield,
  Activity,
  MessageSquare,
  BookOpen,
  Menu,
  Search,
  Pencil,
  Trash2,
  Check,
  X,
  Copy,
} from "lucide-react";
import SanjiviLogo from "@/components/SanjiviLogo";
import { useRouter } from "next/navigation";

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

type SpeechRecognitionConstructor = new () => SpeechRecognition;

interface SpeechRecognition {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  start: () => void;
}

interface SpeechRecognitionEvent {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  systems?: string[];
  emergency?: boolean;
  ayurveda?: any;
  siddha?: any;
  unani?: any;
  homeopathy?: any;
  yoga?: any;
  sources?: any;
  hospital_referral?: any;
}

interface Chat {
  id: string;
  title: string;
  preview: string;
  timestamp: Date;
  starred: boolean;
  systems: string[];
}

type ChatMessages = Record<string, Message[]>;

// ─── Constants ───────────────────────────────────────────────
const SYSTEM_COLORS: Record<string, { bg: string; dot: string; text: string; icon: React.ReactNode }> = {
  Ayurveda: { bg: "bg-emerald-50", dot: "bg-emerald-500", text: "text-emerald-700", icon: <Leaf className="w-3 h-3" /> },
  Siddha:   { bg: "bg-amber-50",   dot: "bg-amber-500",   text: "text-amber-700",   icon: <Shield className="w-3 h-3" /> },
  Unani:    { bg: "bg-teal-50",    dot: "bg-teal-500",    text: "text-teal-700",    icon: <Beaker className="w-3 h-3" /> },
  Homeopathy:{ bg: "bg-purple-50", dot: "bg-purple-500",  text: "text-purple-700",  icon: <Activity className="w-3 h-3" /> },
  Yoga:     { bg: "bg-orange-50",  dot: "bg-orange-500",  text: "text-orange-700",  icon: <Sun className="w-3 h-3" /> },
};

const CHAT_MODES = [
  { value: "Multisystem", label: "Multisystem" },
  { value: "Ayurveda", label: "Ayurvedic" },
  { value: "Yoga", label: "Yoga" },
  { value: "Unani", label: "Unani" },
  { value: "Siddha", label: "Siddha" },
  { value: "Homeopathy", label: "Homeopathy" },
];

// ─── Sub-components ───────────────────────────────────────────
function SystemBadge({ system }: { system: string }) {
  const cfg = SYSTEM_COLORS[system];
  if (!cfg) return null;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold ${cfg.bg} ${cfg.text} border border-current/20`}>
      {cfg.icon}
      {system}
    </span>
  );
}

function MessageBubble({ msg, isSaved, onSave }: {
  msg: Message;
  isSaved?: boolean;
  onSave?: () => void;
}) {
  const [showSources, setShowSources] = useState(false);
  const [expandedSystems, setExpandedSystems] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (msg.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="flex justify-end w-full"
      >
        <div className="max-w-[85%] sm:max-w-[75%] bg-primary text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-sm">
          {msg.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="flex justify-start w-full"
    >
      <div className="max-w-[92%] sm:max-w-[85%] flex flex-col gap-3">
        {/* Emergency Banner */}
        {msg.emergency && (
          <div className="flex flex-col gap-3 px-4 py-3 bg-rose-600 text-white rounded-2xl text-xs font-bold shadow-lg">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 shrink-0" />
              <span>{msg.content || "This may require immediate medical attention. Please contact a hospital or call 102 / 112. No home remedies are shown."}</span>
            </div>
            {msg.hospital_referral?.nearest_hospital && (
              <div className="flex flex-col gap-2 mt-2 bg-rose-700/60 p-3 rounded-xl font-sans">
                <span className="text-[10px] uppercase tracking-wider text-rose-200 block mb-1">Nearest Hospital Details</span>
                <div className="flex flex-col gap-0.5">
                  <span className="font-extrabold text-[11px]">{msg.hospital_referral.nearest_hospital.name}</span>
                  <span className="text-[10px] text-rose-100 font-normal">{msg.hospital_referral.nearest_hospital.address}</span>
                  {msg.hospital_referral.nearest_hospital.phone && <span className="text-[9px] text-rose-100 font-normal">Phone: {msg.hospital_referral.nearest_hospital.phone}</span>}
                  {msg.hospital_referral.nearest_hospital.distance_km != null && <span className="text-[9px] text-rose-200 font-normal">Distance: {msg.hospital_referral.nearest_hospital.distance_km} km</span>}
                  {msg.hospital_referral.nearest_hospital.maps_url && (
                    <a href={msg.hospital_referral.nearest_hospital.maps_url} target="_blank" rel="noopener noreferrer" className="text-[9px] text-white underline mt-0.5 hover:text-rose-100">
                      View on Google Maps
                    </a>
                  )}
                </div>
              </div>
            )}
            {msg.hospital_referral?.hospitals && msg.hospital_referral.hospitals.length > 0 && (
              <div className="flex flex-col gap-2 mt-2 bg-rose-700/50 p-3 rounded-xl font-sans">
                <span className="text-[10px] uppercase tracking-wider text-rose-200 block mb-1">Other Nearby Hospitals:</span>
                <div className="flex flex-col gap-2">
                  {msg.hospital_referral.hospitals.map((h: any, idx: number) => (
                    <div key={idx} className="border-b border-rose-500/20 last:border-b-0 pb-1.5 last:pb-0 flex flex-col gap-0.5">
                      <span className="font-extrabold text-[11px]">{h.name}</span>
                      <span className="text-[10px] text-rose-100 font-normal">{h.address}</span>
                      {h.phone && <span className="text-[9px] text-rose-100 font-normal">Phone: {h.phone}</span>}
                      {h.distance_km && <span className="text-[9px] text-rose-200 font-normal">Distance: {h.distance_km} km</span>}
                      {h.maps_url && (
                        <a href={h.maps_url} target="_blank" rel="noopener noreferrer" className="text-[9px] text-white underline mt-0.5 hover:text-rose-100">
                          View on Google Maps
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!msg.emergency && (
          <div className="bg-white border border-neutral-200/60 rounded-2xl rounded-tl-sm shadow-sm overflow-hidden transition-shadow duration-300 hover:shadow-md">
            {/* Response header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-100 bg-neutral-50/50">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
                  <ShieldCheck className="w-3 h-3 text-emerald-600" />
                </div>
                <span className="text-[10px] font-extrabold text-emerald-700 uppercase tracking-wider">Safety Validated</span>
              </div>
              {msg.systems && msg.systems.length > 0 && (
                <div className="flex gap-1 flex-wrap justify-end">
                  {msg.systems.map(s => <SystemBadge key={s} system={s} />)}
                </div>
              )}
            </div>

            {/* Content */}
            <div className="px-4 py-4 text-sm text-brand-text leading-relaxed prose prose-sm max-w-none">
              {msg.content.split("\n").map((line, idx) => {
                if (line.startsWith("**") && line.endsWith("**")) {
                  return <p key={idx} className="font-bold text-brand-text mt-3 mb-1">{line.replace(/\*\*/g, "")}</p>;
                }
                if (line.startsWith("---")) {
                  return <hr key={idx} className="my-3 border-neutral-100" />;
                }
                if (line.startsWith("*") && line.endsWith("*")) {
                  return <p key={idx} className="text-xs text-brand-muted italic mt-3">{line.replace(/\*/g, "")}</p>;
                }
                return <p key={idx} className="mb-1">{line}</p>;
              })}
            </div>

            {msg.yoga?.images && msg.yoga.images.length > 0 && (
              <div className="px-4 pb-4">
                <p className="text-[10px] font-extrabold uppercase tracking-wider text-brand-muted mb-2">Suggested yoga poses</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {msg.yoga.images.map((img: any, idx: number) => (
                    <a
                      key={`${img.pose_name}-${idx}`}
                      href={img.source_url || img.image_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-xl border border-neutral-200 overflow-hidden bg-neutral-50 hover:border-primary transition-colors"
                    >
                      <img src={img.image_url} alt={img.pose_name} className="h-28 w-full object-cover" />
                      <span className="block px-2 py-2 text-[10px] font-bold text-brand-text truncate">{img.pose_name}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {showSources && msg.sources && msg.sources.length > 0 && (
              <div className="px-4 pb-4">
                <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-3">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-brand-muted mb-2">Sources</p>
                  <div className="flex flex-col gap-3">
                    {msg.sources.map((source: any, idx: number) => (
                      <div key={idx} className="text-xs text-brand-text leading-relaxed">
                        <p className="font-bold">
                          {source.title || "Source document"}
                          {source.page ? `, p. ${source.page}` : ""}
                        </p>
                        {source.domain && <p className="text-[10px] text-primary font-bold uppercase tracking-wider">{source.domain}</p>}
                        {source.excerpt && <p className="text-[11px] text-brand-muted mt-1">{source.excerpt}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Footer actions */}
            <div className="px-4 py-3 border-t border-neutral-100 flex items-center gap-3 flex-wrap">
              <button
                onClick={onSave}
                className={`text-[10px] font-bold transition-colors flex items-center gap-1 ${
                  isSaved ? "text-gold" : "text-brand-muted hover:text-primary"
                }`}
              >
                <Star className={`w-3 h-3 ${isSaved ? "fill-gold" : ""}`} /> {isSaved ? "Saved" : "Save"}
              </button>
              <button
                onClick={() => setShowSources(prev => !prev)}
                disabled={!msg.sources || msg.sources.length === 0}
                className="text-[10px] font-bold text-brand-muted hover:text-primary transition-colors flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <BookOpen className="w-3 h-3" /> Sources
              </button>
              <button
                onClick={handleCopy}
                className="text-[10px] font-bold text-brand-muted hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-600" />
                    <span className="text-emerald-600">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy</span>
                  </>
                )}
              </button>
              <button
                onClick={() => setExpandedSystems(prev => !prev)}
                className="text-[10px] font-bold text-primary hover:underline flex items-center gap-1 ml-auto"
              >
                {expandedSystems ? "Hide" : "See"} per-system breakdown
                <ChevronDown className={`w-3 h-3 transition-transform ${expandedSystems ? "rotate-180" : ""}`} />
              </button>
            </div>

            {/* Expanded system breakdown */}
            <AnimatePresence>
              {expandedSystems && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  className="overflow-hidden border-t border-neutral-100"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 bg-neutral-50/30">
                    {Object.entries(SYSTEM_COLORS).map(([sys, cfg]) => (
                      <div key={sys} className={`px-5 py-4 rounded-xl border border-neutral-200/40 shadow-sm transition-all duration-300 hover:shadow-md ${cfg.bg}`}>
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className={`w-2.5 h-2.5 rounded-full ${cfg.dot}`} />
                          <span className={`text-xs md:text-sm font-extrabold uppercase tracking-wider ${cfg.text}`}>{sys}</span>
                        </div>
                        <div className="text-xs md:text-sm text-brand-text font-medium leading-relaxed">
                          {sys === "Ayurveda" && (msg.ayurveda ? (
                            <div className="flex flex-col gap-1 text-[11px]">
                              {msg.ayurveda.diagnosis && <p><span className="font-bold text-[9px] uppercase text-emerald-800 tracking-wider">Assessment:</span> {msg.ayurveda.diagnosis}</p>}
                              {msg.ayurveda.recommendations && <p><span className="font-bold text-[9px] uppercase text-emerald-800 tracking-wider">Therapy:</span> {msg.ayurveda.recommendations}</p>}
                              {msg.ayurveda.herbs_or_remedies && msg.ayurveda.herbs_or_remedies.length > 0 && (
                                <p><span className="font-bold text-[9px] uppercase text-emerald-800 tracking-wider">Herbs:</span> {msg.ayurveda.herbs_or_remedies.join(", ")}</p>
                              )}
                              {msg.ayurveda.diet && <p><span className="font-bold text-[9px] uppercase text-emerald-800 tracking-wider">Diet:</span> {msg.ayurveda.diet}</p>}
                              {msg.ayurveda.lifestyle && <p><span className="font-bold text-[9px] uppercase text-emerald-800 tracking-wider">Lifestyle:</span> {msg.ayurveda.lifestyle}</p>}
                            </div>
                          ) : "Yashtimadhu decoction, warm Abhyanga massage, avoid cold foods.")}
                          
                          {sys === "Siddha" && (msg.siddha ? (
                            <div className="flex flex-col gap-1 text-[11px]">
                              {msg.siddha.diagnosis && <p><span className="font-bold text-[9px] uppercase text-amber-800 tracking-wider">Assessment:</span> {msg.siddha.diagnosis}</p>}
                              {msg.siddha.recommendations && <p><span className="font-bold text-[9px] uppercase text-amber-800 tracking-wider">Therapy:</span> {msg.siddha.recommendations}</p>}
                              {msg.siddha.herbs_or_remedies && msg.siddha.herbs_or_remedies.length > 0 && (
                                <p><span className="font-bold text-[9px] uppercase text-amber-800 tracking-wider">Formulations:</span> {msg.siddha.herbs_or_remedies.join(", ")}</p>
                              )}
                              {msg.siddha.diet && <p><span className="font-bold text-[9px] uppercase text-amber-800 tracking-wider">Diet:</span> {msg.siddha.diet}</p>}
                              {msg.siddha.lifestyle && <p><span className="font-bold text-[9px] uppercase text-amber-800 tracking-wider">Lifestyle:</span> {msg.siddha.lifestyle}</p>}
                            </div>
                          ) : "Nilavembu Kudineer for cooling, kanji diet, morning sun.")}

                          {sys === "Unani" && (msg.unani ? (
                            <div className="flex flex-col gap-1 text-[11px]">
                              {msg.unani.diagnosis && <p><span className="font-bold text-[9px] uppercase text-teal-800 tracking-wider">Mizaj & Assessment:</span> {msg.unani.diagnosis}</p>}
                              {msg.unani.recommendations && <p><span className="font-bold text-[9px] uppercase text-teal-800 tracking-wider">Therapy:</span> {msg.unani.recommendations}</p>}
                              {msg.unani.herbs_or_remedies && msg.unani.herbs_or_remedies.length > 0 && (
                                <p><span className="font-bold text-[9px] uppercase text-teal-800 tracking-wider">Drugs:</span> {msg.unani.herbs_or_remedies.join(", ")}</p>
                              )}
                              {msg.unani.diet && <p><span className="font-bold text-[9px] uppercase text-teal-800 tracking-wider">Diet:</span> {msg.unani.diet}</p>}
                              {msg.unani.lifestyle && <p><span className="font-bold text-[9px] uppercase text-teal-800 tracking-wider">Regimen:</span> {msg.unani.lifestyle}</p>}
                            </div>
                          ) : "Roghan Baiza Murgh topical, warm hydrotherapy, honey-ginger.")}

                          {sys === "Homeopathy" && (msg.homeopathy ? (
                            <div className="flex flex-col gap-1 text-[11px]">
                              {msg.homeopathy.diagnosis && <p><span className="font-bold text-[9px] uppercase text-purple-800 tracking-wider">Totality Analysis:</span> {msg.homeopathy.diagnosis}</p>}
                              {msg.homeopathy.recommendations && <p><span className="font-bold text-[9px] uppercase text-purple-800 tracking-wider">Prescription:</span> {msg.homeopathy.recommendations}</p>}
                              {msg.homeopathy.herbs_or_remedies && msg.homeopathy.herbs_or_remedies.length > 0 && (
                                <p><span className="font-bold text-[9px] uppercase text-purple-800 tracking-wider">Remedies:</span> {msg.homeopathy.herbs_or_remedies.join(", ")}</p>
                              )}
                              {msg.homeopathy.diet && <p><span className="font-bold text-[9px] uppercase text-purple-800 tracking-wider">Dietary:</span> {msg.homeopathy.diet}</p>}
                              {msg.homeopathy.lifestyle && <p><span className="font-bold text-[9px] uppercase text-purple-800 tracking-wider">Lifestyle:</span> {msg.homeopathy.lifestyle}</p>}
                            </div>
                          ) : "Nux Vomica 30C once nightly for stress-digestive overlap.")}

                          {sys === "Yoga" && msg.yoga && (
                            <div className="flex flex-col gap-1.5 text-[11px]">
                              {msg.yoga.poses && msg.yoga.poses.length > 0 && (
                                <div>
                                  <span className="font-bold text-[9px] uppercase text-orange-850 tracking-wider block">Asanas:</span>
                                  <ul className="list-disc list-inside pl-1 text-orange-900">
                                    {msg.yoga.poses.map((p: string, i: number) => <li key={i}>{p}</li>)}
                                  </ul>
                                </div>
                              )}
                              {msg.yoga.breathing_exercises && msg.yoga.breathing_exercises.length > 0 && (
                                <p><span className="font-bold text-[9px] uppercase text-orange-850 tracking-wider">Pranayama:</span> {msg.yoga.breathing_exercises.join(", ")}</p>
                              )}
                              {msg.yoga.lifestyle && <p><span className="font-bold text-[9px] uppercase text-orange-850 tracking-wider">Lifestyle:</span> {msg.yoga.lifestyle}</p>}
                              {msg.yoga.images && msg.yoga.images.length > 0 && (
                                <div className="flex gap-2 overflow-x-auto mt-2 pb-1 no-scrollbar">
                                  {msg.yoga.images.map((img: any, i: number) => (
                                    <div key={i} className="flex-shrink-0 w-24 bg-white border border-neutral-100 rounded-lg p-1">
                                      <img src={img.image_url} alt={img.pose_name} className="w-full h-16 object-cover rounded" />
                                      <span className="text-[8px] font-bold block mt-1 truncate text-neutral-600">{img.pose_name}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ─── Main Chat Page ───────────────────────────────────────────
export default function ChatPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessages>({});
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [systemFilter, setSystemFilter] = useState<string>("All");
  const [selectedMode, setSelectedMode] = useState<string>("Multisystem");
  const [activeView, setActiveView] = useState<"chat" | "starred">("chat");
  const [isListening, setIsListening] = useState(false);

  // States for ChatGPT-like features (Edit, Delete, Search)
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messages = activeChat ? chatMessages[activeChat] ?? [] : [];

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }, []);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Handler functions for editing and deleting chats
  const deleteChat = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    setChats(prev => prev.filter(c => c.id !== chatId));
    setChatMessages(prev => {
      const next = { ...prev };
      delete next[chatId];
      return next;
    });

    if (activeChat === chatId) {
      const remainingChats = chats.filter(c => c.id !== chatId);
      if (remainingChats.length > 0) {
        setActiveChat(remainingChats[0].id);
      } else {
        setActiveChat(null);
      }
    }
  };

  const startEditing = (chatId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingChatId(chatId);
    setEditingTitle(currentTitle);
  };

  const saveTitle = (chatId: string, e?: React.MouseEvent | React.KeyboardEvent) => {
    if (e) e.stopPropagation();
    if (!editingTitle.trim()) return;

    setChats(prev => prev.map(c => {
      if (c.id === chatId) {
        return { ...c, title: editingTitle.trim() };
      }
      return c;
    }));
    setEditingChatId(null);
    setEditingTitle("");
  };

  const cancelEditing = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    setEditingChatId(null);
    setEditingTitle("");
  };

  const createChat = (firstMessage?: string) => {
    const id = `chat-${Date.now()}`;
    const title = firstMessage ? firstMessage.slice(0, 48) : "New conversation";
    const newChat: Chat = {
      id,
      title,
      preview: firstMessage || "Start asking...",
      timestamp: new Date(),
      starred: false,
      systems: getSelectedSystems(),
    };
    setChats(prev => [newChat, ...prev]);
    setChatMessages(prev => ({ ...prev, [id]: [] }));
    setActiveChat(id);
    return id;
  };

  const appendMessage = (chatId: string, message: Message) => {
    setChatMessages(prev => ({
      ...prev,
      [chatId]: [...(prev[chatId] ?? []), message],
    }));
  };

  const updateChatSummary = (chatId: string, message: Message) => {
    setChats(prev => prev.map(chat => (
      chat.id === chatId
        ? {
            ...chat,
            preview: message.content,
            timestamp: message.timestamp,
            systems: message.systems?.length ? message.systems : chat.systems,
          }
        : chat
    )));
  };

  const getSelectedSystems = () => (
    selectedMode === "Multisystem" ? Object.keys(SYSTEM_COLORS) : [selectedMode]
  );

  const getCurrentPosition = () => new Promise<{ lat: number; lng: number } | null>((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => resolve({
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 2500, maximumAge: 300000 },
    );
  });

  const toggleStarredChat = (chatId: string) => {
    setChats(prev => prev.map(chat => (
      chat.id === chatId ? { ...chat, starred: !chat.starred } : chat
    )));
  };

  const handleVoiceInput = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setInputValue(prev => `${prev}${prev ? " " : ""}Voice input is not supported in this browser.`);
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) {
        setInputValue(prev => `${prev}${prev ? " " : ""}${transcript}`);
      }
    };
    recognition.start();
  };

  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text) return;
    const chatId = activeChat ?? createChat(text);
    const currentMessages = chatMessages[chatId] ?? [];

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    appendMessage(chatId, userMsg);
    setChats(prev => prev.map(chat => (
      chat.id === chatId
        ? {
            ...chat,
            title: chat.title === "New conversation" ? text.slice(0, 48) : chat.title,
            preview: text,
            timestamp: userMsg.timestamp,
            systems: getSelectedSystems(),
          }
        : chat
    )));
    setInputValue("");
    setIsTyping(true);

    try {
      const location = await getCurrentPosition();
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://sanjivi-backend.onrender.com";
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          selected_system: selectedMode,
          history: currentMessages.map(m => ({ role: m.role, content: m.content })),
          lat: location?.lat,
          lng: location?.lng,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server status: ${response.status}`);
      }

      const data = await response.json();
      setIsTyping(false);
      const responseSystems = data.emergency
        ? []
        : Object.entries({
            Ayurveda: data.ayurveda,
            Siddha: data.siddha,
            Unani: data.unani,
            Homeopathy: data.homeopathy,
            Yoga: data.yoga,
          }).filter(([, value]) => Boolean(value)).map(([system]) => system);

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: data.emergency
          ? (data.hospital_referral?.message || "Medical emergency detected. Please consult a doctor immediately.")
          : (data.reviewer?.final_answer || data.consensus?.unified_recommendation || "Synthesis completed."),
        timestamp: new Date(),
        systems: responseSystems.length > 0 ? responseSystems : getSelectedSystems(),
        emergency: data.emergency,
        ayurveda: data.ayurveda,
        siddha: data.siddha,
        unani: data.unani,
        homeopathy: data.homeopathy,
        yoga: data.yoga,
        sources: data.sources,
        hospital_referral: data.hospital_referral,
      };

      appendMessage(chatId, aiMsg);
      updateChatSummary(chatId, aiMsg);
    } catch (err) {
      console.warn("Backend API not reachable:", err);
      setIsTyping(false);
      const errorMsg: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: "I could not reach the Sanjivi AI backend. Please make sure the backend is running, then try again.",
        timestamp: new Date(),
        systems: [],
        emergency: false,
      };
      appendMessage(chatId, errorMsg);
      updateChatSummary(chatId, errorMsg);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    createChat();
    if (isMobile) setSidebarOpen(false);
  };

  const filteredChats = chats.filter(c => {
    if (activeView === "starred" && !c.starred) return false;
    if (systemFilter === "Multisystem" && c.systems.length <= 1) return false;
    if (systemFilter !== "All" && systemFilter !== "Multisystem" && !c.systems.includes(systemFilter)) return false;
    
    if (searchQuery.trim() !== "") {
      const query = searchQuery.toLowerCase();
      const matchTitle = c.title.toLowerCase().includes(query);
      const matchMessages = (chatMessages[c.id] ?? []).some(m => 
        m.content.toLowerCase().includes(query)
      );
      return matchTitle || matchMessages;
    }
    return true;
  });

  const [timeCutoffs] = useState(() => {
    const now = Date.now();
    return {
      today: new Date(now - 86400000),
      week: new Date(now - 604800000),
    };
  });
  const groupedChats = {
    Today: filteredChats.filter(c => c.timestamp > timeCutoffs.today),
    "This Week": filteredChats.filter(c => c.timestamp <= timeCutoffs.today && c.timestamp > timeCutoffs.week),
    Older: filteredChats.filter(c => c.timestamp <= timeCutoffs.week),
  };

  return (
    <div className="h-screen w-screen flex bg-brand-bg overflow-hidden relative">
      {/* Backdrop overlay for mobile drawer */}
      <AnimatePresence>
        {isMobile && sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-brand-text/30 backdrop-blur-xs z-35"
          />
        )}
      </AnimatePresence>

      {/* ── LEFT SIDEBAR ── */}
      <AnimatePresence initial={false}>
        {(!isMobile || sidebarOpen) && (
          <motion.aside
            key="sidebar"
            initial={isMobile ? { x: "-100%" } : { width: 0, opacity: 0 }}
            animate={
              isMobile
                ? { x: 0 }
                : { width: sidebarOpen ? 280 : 0, opacity: sidebarOpen ? 1 : 0 }
            }
            exit={isMobile ? { x: "-100%" } : { width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className={`h-full flex flex-col bg-white border-r border-neutral-200/60 overflow-hidden shrink-0 z-40 ${
              isMobile ? "fixed inset-y-0 left-0 w-[280px] shadow-2xl" : "relative"
            }`}
          >
            {/* Logo + collapse */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-neutral-100">
              <a onClick={() => {
                router.push("/");
                if (isMobile) setSidebarOpen(false);
              }} className="cursor-pointer">
                <SanjiviLogo />
              </a>
              <button
                onClick={() => setSidebarOpen(false)}
                className="w-7 h-7 rounded-lg hover:bg-neutral-100 flex items-center justify-center transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4 text-brand-muted" />
              </button>
            </div>

            <div className="px-3 py-3">
              <button
                onClick={() => {
                  router.push("/");
                  if (isMobile) setSidebarOpen(false);
                }}
                className="w-full text-[10px] font-bold uppercase tracking-wide text-emerald-900 bg-emerald-50 hover:bg-emerald-100 transition-all rounded-xl px-4 py-2.5 shadow-sm cursor-pointer"
              >
                Back to landing page
              </button>
            </div>

            {/* New Chat */}
            <div className="px-3 py-3">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-[#1b5e20] text-white text-xs font-bold rounded-xl transition-all shadow-sm cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>New Chat</span>
              </button>
            </div>

            {/* Search chats */}
            <div className="px-3 mb-2 relative">
              <Search className="w-3.5 h-3.5 absolute left-6 top-3.5 text-neutral-400" />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-8 py-2 rounded-xl bg-neutral-50 border border-neutral-200 text-xs font-medium text-brand-text placeholder-neutral-400 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-6 top-2.5 p-0.5 rounded-full hover:bg-neutral-200 text-neutral-400 hover:text-brand-text transition-colors cursor-pointer"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* View tabs: All / Starred */}
            <div className="flex px-3 gap-1 mb-2">
              {(["chat", "starred"] as const).map(v => (
                <button
                  key={v}
                  onClick={() => setActiveView(v)}
                  className={`flex-1 py-1.5 text-[10px] font-extrabold rounded-lg uppercase tracking-wide transition-colors cursor-pointer ${
                    activeView === v ? "bg-emerald-50 text-primary" : "text-brand-muted hover:text-brand-text"
                  }`}
                >
                  {v === "starred" ? "Starred" : "All Chats"}
                </button>
              ))}
            </div>

            {/* System Filter */}
            <div className="px-3 mb-3">
              <select
                value={systemFilter}
                onChange={e => setSystemFilter(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-neutral-50 border border-neutral-200 text-[10px] font-bold text-brand-muted focus:outline-none focus:border-primary transition-all cursor-pointer"
              >
                <option value="All">All Systems</option>
                {CHAT_MODES.map(mode => (
                  <option key={mode.value} value={mode.value}>{mode.label}</option>
                ))}
              </select>
            </div>

            {/* Chat History List */}
            <div data-lenis-prevent className="flex-1 overflow-y-auto px-2 pb-3 custom-scrollbar">
              {filteredChats.length === 0 && (
                <div className="px-3 py-8 text-center">
                  <p className="text-xs font-bold text-brand-text">No chats found</p>
                  <p className="text-[10px] text-brand-muted mt-1 leading-relaxed">
                    Try another search term or start a new conversation.
                  </p>
                </div>
              )}
              {Object.entries(groupedChats).map(([group, items]) =>
                items.length > 0 ? (
                  <div key={group} className="mb-4">
                    <p className="px-3 pb-1.5 text-[9px] font-extrabold uppercase tracking-widest text-neutral-400">{group}</p>
                    {items.map(chat => (
                      <div key={chat.id} className="relative group/item w-full mb-0.5">
                        {editingChatId === chat.id ? (
                          <div className="flex items-center gap-1.5 px-3 py-2 bg-emerald-50 border border-emerald-100 rounded-xl">
                            <input
                              type="text"
                              value={editingTitle}
                              onChange={e => setEditingTitle(e.target.value)}
                              onKeyDown={e => {
                                if (e.key === "Enter") saveTitle(chat.id);
                                else if (e.key === "Escape") cancelEditing(e);
                              }}
                              autoFocus
                              className="flex-1 min-w-0 bg-transparent text-xs font-semibold text-brand-text border-b border-primary focus:outline-none py-0.5"
                            />
                            <button
                              onClick={(e) => saveTitle(chat.id, e)}
                              className="p-1 rounded hover:bg-emerald-100 text-emerald-700 transition-colors cursor-pointer"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={cancelEditing}
                              className="p-1 rounded hover:bg-emerald-100 text-neutral-500 transition-colors cursor-pointer"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <div
                            onClick={() => {
                              setActiveChat(chat.id);
                              if (isMobile) setSidebarOpen(false);
                            }}
                            className={`w-full text-left px-3 py-2.5 rounded-xl transition-all relative flex flex-col gap-1 cursor-pointer ${
                              activeChat === chat.id
                                ? "bg-emerald-50 border border-emerald-100"
                                : "hover:bg-neutral-50 border border-transparent"
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2 pr-12">
                              <div className="flex-1 min-w-0">
                                <p className={`text-xs font-semibold truncate ${activeChat === chat.id ? "text-primary" : "text-brand-text"}`}>
                                  {chat.title}
                                </p>
                                <p className="text-[10px] text-brand-muted truncate mt-0.5">{chat.preview}</p>
                              </div>
                              {chat.starred && <Star className="w-3 h-3 text-gold fill-gold shrink-0 mt-0.5" />}
                            </div>
                            {chat.systems.length > 0 && (
                              <div className="flex gap-1 mt-0.5 flex-wrap">
                                {chat.systems.slice(0, 2).map(s => (
                                  <span key={s} className={`text-[8px] font-bold px-1.5 py-0.5 rounded-full ${SYSTEM_COLORS[s]?.bg} ${SYSTEM_COLORS[s]?.text}`}>
                                    {s}
                                  </span>
                                ))}
                                {chat.systems.length > 2 && (
                                  <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full bg-neutral-100 text-neutral-500">
                                    +{chat.systems.length - 2}
                                  </span>
                                )}
                              </div>
                            )}

                            {/* Hover actions group (Rename, Delete) */}
                            <div className={`absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 transition-opacity pl-4 pr-1 h-8 rounded-r-xl ${
                              isMobile ? "opacity-100" : "opacity-0 group-hover/item:opacity-100"
                            } ${
                              activeChat === chat.id
                                ? "bg-gradient-to-l from-emerald-50 via-emerald-50 to-transparent"
                                : "bg-gradient-to-l from-neutral-50 via-neutral-50 to-transparent"
                            }`}>
                              <button
                                onClick={(e) => startEditing(chat.id, chat.title, e)}
                                className="p-1 rounded hover:bg-neutral-200/50 text-brand-muted hover:text-primary transition-colors cursor-pointer"
                                title="Rename conversation"
                              >
                                <Pencil className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={(e) => deleteChat(chat.id, e)}
                                className="p-1 rounded hover:bg-neutral-200/50 text-brand-muted hover:text-rose-600 transition-colors cursor-pointer"
                                title="Delete conversation"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : null
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── MAIN CHAT AREA ── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">

        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200/60 bg-white/80 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-3">
            {(!sidebarOpen || isMobile) && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="w-8 h-8 rounded-xl hover:bg-neutral-100 flex items-center justify-center transition-colors cursor-pointer"
              >
                <Menu className="w-4 h-4 text-brand-muted" />
              </button>
            )}
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-brand-muted" />
              <span className="text-sm font-bold text-brand-text truncate max-w-[200px]">
                {chats.find(c => c.id === activeChat)?.title ?? "New conversation"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedMode}
              onChange={(e) => setSelectedMode(e.target.value)}
              className="hidden sm:block px-3 py-2 rounded-xl bg-neutral-50 border border-neutral-200 text-[10px] font-bold text-brand-muted focus:outline-none focus:border-primary transition-all cursor-pointer"
              title="Choose response model"
            >
              {CHAT_MODES.map(mode => (
                <option key={mode.value} value={mode.value}>{mode.label}</option>
              ))}
            </select>
            {/* System indicators */}
            <div className="hidden sm:flex items-center gap-1">
              {Object.entries(SYSTEM_COLORS).map(([sys, cfg]) => (
                <div key={sys} title={sys} className={`w-2 h-2 rounded-full ${cfg.dot}`} />
              ))}
            </div>
            <button
              onClick={handleNewChat}
              className="w-8 h-8 rounded-xl bg-primary text-white flex items-center justify-center shadow-sm transition-all hover:bg-[#1b5e20] cursor-pointer"
              title="New chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages area */}
        <div data-lenis-prevent className="flex-1 overflow-y-auto scroll-smooth px-4 md:px-12 lg:px-24 py-6 flex flex-col gap-5 custom-scrollbar">
          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center gap-6 text-center py-24">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center">
                <Leaf className="w-7 h-7 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-black text-brand-text font-serif">Ask Sanjivi AI anything</h2>
                <p className="text-sm text-brand-muted mt-1.5 max-w-sm">
                  Describe your symptoms, ask about herbs, or explore a traditional protocol. Five systems respond in concert.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {[
                  "I have morning joint stiffness for 2 weeks",
                  "Natural remedies for digestive issues",
                  "Pranayama for work stress",
                  "Ayurvedic skin care routine",
                ].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => setInputValue(suggestion)}
                    className="px-3 py-2 text-xs font-medium bg-white border border-neutral-200 rounded-xl hover:border-primary hover:text-primary transition-all cursor-pointer"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              isSaved={!!activeChat && !!chats.find(chat => chat.id === activeChat)?.starred}
              onSave={activeChat ? () => toggleStarredChat(activeChat) : undefined}
            />
          ))}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-neutral-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center gap-2">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <span className="text-[10px] font-semibold text-brand-muted">Five systems analyzing…</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-4 md:px-12 lg:px-24 pb-6 pt-3 shrink-0 bg-brand-bg">
          <div className="sm:hidden mb-2">
            <select
              value={selectedMode}
              onChange={(e) => setSelectedMode(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white border border-neutral-200 text-xs font-bold text-brand-muted focus:outline-none focus:border-primary transition-all cursor-pointer"
            >
              {CHAT_MODES.map(mode => (
                <option key={mode.value} value={mode.value}>{mode.label}</option>
              ))}
            </select>
          </div>
          <div className="relative flex items-end gap-3 bg-white border border-neutral-200 rounded-2xl shadow-sm focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/10 transition-all px-4 py-3">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your symptoms or ask about a traditional remedy…"
              rows={1}
              className="flex-1 resize-none text-sm text-brand-text placeholder-neutral-400 bg-transparent focus:outline-none leading-relaxed max-h-36 no-scrollbar"
              style={{ overflowY: inputValue.split("\n").length > 3 ? "auto" : "hidden" }}
            />
            <div className="flex items-center gap-2 shrink-0 pb-0.5">
              <button
                onClick={handleVoiceInput}
                className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors cursor-pointer ${
                  isListening ? "bg-emerald-50 text-primary" : "hover:bg-neutral-100 text-brand-muted hover:text-primary"
                }`}
                title="Voice input"
              >
                <Mic className="w-4 h-4" />
              </button>
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
                className="w-9 h-9 rounded-xl bg-primary hover:bg-[#1b5e20] text-white flex items-center justify-center transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-sm"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
          <p className="text-center text-[9px] text-neutral-400 font-medium mt-2.5">
            Sanjivi AI provides educational information only. Not a substitute for professional medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}
