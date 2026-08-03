"use client";

import { useEffect, useState, useCallback } from "react";

interface ConfettiExplosionProps {
  active: boolean;
  onComplete?: () => void;
  pieceCount?: number;
}

const COLORS = ["#FF8C42", "#FF6B6B", "#FFD93D", "#6BCB77", "#4ECDC4", "#4D96FF", "#9B59B6", "#FF85A2"];

interface Piece {
  id: number;
  x: number;
  color: string;
  delay: number;
  rotation: number;
  size: number;
}

export function ConfettiExplosion({ active, onComplete, pieceCount = 30 }: ConfettiExplosionProps) {
  const [pieces, setPieces] = useState<Piece[]>([]);

  useEffect(() => {
    if (active) {
      const newPieces: Piece[] = Array.from({ length: pieceCount }, (_, i) => ({
        id: i,
        x: (Math.random() - 0.5) * 200 + 50,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        delay: Math.random() * 0.3,
        rotation: Math.random() * 720 - 360,
        size: Math.random() * 8 + 6,
      }));
      setPieces(newPieces);

      const timer = setTimeout(() => {
        setPieces([]);
        onComplete?.();
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [active, pieceCount, onComplete]);

  if (!active || pieces.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden" aria-hidden="true">
      {pieces.map((piece) => (
        <div
          key={piece.id}
          className="kid-confetti-piece"
          style={{
            left: `${piece.x}%`,
            top: "-10px",
            width: `${piece.size}px`,
            height: `${piece.size * 1.4}px`,
            backgroundColor: piece.color,
            animationDelay: `${piece.delay}s`,
            transform: `rotate(${piece.rotation}deg)`,
          }}
        />
      ))}
    </div>
  );
}

/**
 * Hook: trigger confetti with a simple boolean toggle
 */
export function useConfetti() {
  const [show, setShow] = useState(false);

  const fire = useCallback(() => {
    setShow(false);
    // Use microtask to reset state so React re-triggers the effect
    setTimeout(() => setShow(true), 50);
  }, []);

  return { show, fire, Confetti: () => <ConfettiExplosion active={show} /> };
}
