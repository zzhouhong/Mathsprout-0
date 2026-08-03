"use client";

import { type ReactNode } from "react";

interface MascotBubbleProps {
  message: string;
  emotion?: "happy" | "think" | "cheer" | "encourage";
  children?: ReactNode;
  className?: string;
}

const emotionEmoji: Record<string, string> = {
  happy: "😊",
  think: "🤔",
  cheer: "🎉",
  encourage: "💪",
};

const mascotFaces: Record<string, string> = {
  happy: "🌱",
  think: "🌿",
  cheer: "⭐",
  encourage: "🌳",
};

export function MascotBubble({ message, emotion = "happy", children, className = "" }: MascotBubbleProps) {
  return (
    <div className={`flex items-start gap-3 ${className} animate-kid-slide-up`}>
      {/* Mascot character */}
      <div className="flex-shrink-0 w-14 h-14 rounded-full bg-gradient-to-br from-kid-green to-kid-teal flex items-center justify-center text-3xl shadow-lg animate-kid-float">
        {mascotFaces[emotion]}
      </div>

      {/* Speech bubble */}
      <div className="kid-bubble flex-1 max-w-md">
        <p className="text-gray-700 leading-relaxed">{message}</p>
        {children}
        <span className="absolute -top-2 -right-2 text-xl animate-kid-bounce">
          {emotionEmoji[emotion]}
        </span>
      </div>
    </div>
  );
}

export function MascotCharacter({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "w-12 h-12 text-2xl",
    md: "w-20 h-20 text-4xl",
    lg: "w-32 h-32 text-6xl",
  };

  return (
    <div
      className={`${sizeClasses[size]} rounded-full bg-gradient-to-br from-kid-green to-kid-teal flex items-center justify-center shadow-xl animate-kid-float`}
    >
      🌱
    </div>
  );
}
