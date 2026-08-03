"use client";

import { type ButtonHTMLAttributes, type ReactNode } from "react";

interface BigTapButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "success" | "fun" | "play";
  size?: "md" | "lg" | "xl";
  icon?: ReactNode;
  isLoading?: boolean;
}

const sizeClasses = {
  md: "min-h-[48px] min-w-[48px] px-6 text-lg",
  lg: "min-h-[64px] min-w-[64px] px-8 text-xl",
  xl: "min-h-[80px] min-w-[80px] px-10 text-2xl",
};

const variantClasses = {
  primary: "kid-btn-primary",
  success: "kid-btn-success",
  fun: "kid-btn-fun",
  play: "kid-btn-play",
};

export function BigTapButton({
  children,
  variant = "primary",
  size = "lg",
  icon,
  isLoading,
  className = "",
  disabled,
  ...props
}: BigTapButtonProps) {
  return (
    <button
      className={`kid-btn ${variantClasses[variant]} ${sizeClasses[size]} ${
        disabled || isLoading ? "opacity-50 cursor-not-allowed" : ""
      } ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="inline-flex items-center gap-2">
          <span className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
          加载中...
        </span>
      ) : (
        <>
          {icon && <span className="text-2xl">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
}
