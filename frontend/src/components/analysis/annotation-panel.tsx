"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

interface Annotation {
  id: number;
  report_id: number;
  author: string;
  text: string;
  created_at: string;
}

interface Props {
  reportId: number;
}

export function AnnotationPanel({ reportId }: Props) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchAnnotations = useCallback(async () => {
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/reports/${reportId}/annotations`,
        { headers: { Authorization: `Bearer ${localStorage.getItem("auth_token") || ""}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setAnnotations(data.annotations || []);
      }
    } catch {
      // Silent fail for annotations
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    fetchAnnotations();
  }, [fetchAnnotations]);

  const handleSubmit = async () => {
    if (!text.trim() || submitting) return;
    setSubmitting(true);
    try {
      const { api } = await import("@/lib/api-client");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/reports/${reportId}/annotations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("auth_token") || ""}`,
          },
          body: JSON.stringify({ text: text.trim() }),
        }
      );
      if (res.ok) {
        const newAnnotation = await res.json();
        setAnnotations((prev) => [newAnnotation, ...prev]);
        setText("");
        toast.success("批注已添加");
      } else {
        const err = await res.json().catch(() => ({ detail: "添加失败" }));
        toast.error(err.detail || "添加批注失败");
      }
    } catch {
      toast.error("网络错误");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (annotationId: number) => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/reports/${reportId}/annotations/${annotationId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token") || ""}`,
          },
        }
      );
      if (res.ok) {
        setAnnotations((prev) => prev.filter((a) => a.id !== annotationId));
        toast.success("批注已删除");
      }
    } catch {
      toast.error("删除失败");
    }
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
    } catch {
      return iso.slice(0, 10);
    }
  };

  return (
    <Card className="p-5" id="report-annotations">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">💬</span>
        <h3 className="font-semibold text-slate-700 text-sm">教学批注</h3>
        <Badge className="bg-slate-100 text-slate-500 text-xs">
          {annotations.length}
        </Badge>
      </div>
      <Separator className="mb-3" />

      {/* Input */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="添加教学批注，与同事分享..."
          maxLength={500}
          className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-300"
        />
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || submitting}
          className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-40 transition-colors shrink-0"
        >
          {submitting ? "..." : "发布"}
        </button>
      </div>

      {/* List */}
      {loading ? (
        <p className="text-xs text-slate-400 text-center py-4">加载中...</p>
      ) : annotations.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-4">
          暂无批注。添加第一条教学批注与同事分享。
        </p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {annotations.map((a) => (
            <div
              key={a.id}
              className="p-3 bg-amber-50 rounded-lg border border-amber-100 group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700">{a.text}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {a.author} · {formatDate(a.created_at)}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="text-xs text-slate-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0"
                  title="删除"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
