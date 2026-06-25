"use client";

import { useState, useRef, useCallback, useEffect } from "react";

// Web Speech API type stubs (not in TypeScript's default DOM lib)
interface SpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  continuous: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

interface VoiceInputProps {
  onResult: (text: string) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  language?: string; // default "zh-CN"
  placeholder?: string;
}

/**
 * Voice input button using the browser Web Speech API.
 *
 * Requires HTTPS or localhost (browser security policy).
 * Supported in Chrome, Edge, Safari. Not in Firefox.
 */
export function VoiceInput({
  onResult,
  onError,
  disabled = false,
  language = "zh-CN",
  placeholder = "点击麦克风开始说话...",
}: VoiceInputProps) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check browser support
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }
  }, []);

  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onError?.("您的浏览器不支持语音输入，请使用 Chrome 或 Edge 浏览器");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = language;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let final = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interimText += result[0].transcript;
        }
      }
      if (final) {
        setInterim("");
        setListening(false);
        onResult(final.trim());
      } else {
        setInterim(interimText);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setListening(false);
      setInterim("");
      if (event.error === "no-speech") {
        // User didn't say anything — silent ignore
        return;
      }
      const messages: Record<string, string> = {
        "audio-capture": "未检测到麦克风，请检查设备连接",
        "not-allowed": "麦克风权限被拒绝，请在浏览器设置中允许",
        "network": "网络连接失败，请检查网络",
        "aborted": "语音识别已取消",
      };
      const msg = messages[event.error] || `语音识别出错: ${event.error}`;
      onError?.(msg);
    };

    recognition.onend = () => {
      setListening(false);
      if (interim && !recognitionRef.current) {
        // If recognition ended with interim text, submit it
        onResult(interim.trim());
        setInterim("");
      }
    };

    recognitionRef.current = recognition;
    setListening(true);
    setInterim("");
    recognition.start();

    // Auto-stop after 8 seconds of silence
    setTimeout(() => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    }, 8000);
  }, [language, onResult, onError, interim]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setListening(false);
    setInterim("");
  }, []);

  if (!supported) return null;

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={listening ? stopListening : startListening}
        disabled={disabled}
        className={`relative w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all duration-300 ${
          listening
            ? "bg-red-500 text-white scale-110 shadow-lg shadow-red-200 animate-pulse"
            : "bg-indigo-100 text-indigo-600 hover:bg-indigo-200 hover:scale-105"
        } disabled:opacity-40 disabled:cursor-not-allowed`}
        title={listening ? "点击停止" : "点击说话"}
        aria-label={listening ? "停止录音" : "开始录音"}
      >
        {listening ? "⏹" : "🎤"}
        {listening && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-white" />
        )}
      </button>

      {listening && (
        <div className="text-center">
          <p className="text-xs text-red-500 font-medium animate-pulse">
            🔴 正在聆听...
          </p>
          {interim && (
            <p className="text-sm text-slate-600 mt-1 italic max-w-[200px] truncate">
              &ldquo;{interim}&rdquo;
            </p>
          )}
        </div>
      )}

      {!listening && !interim && (
        <p className="text-xs text-slate-400">{placeholder}</p>
      )}
    </div>
  );
}
