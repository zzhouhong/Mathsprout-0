"use client";

import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface AnalysisProgressProps {
  progressStep: string;
  progress: number;
}

export function AnalysisProgress({ progressStep, progress }: AnalysisProgressProps) {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-4 mb-2">
        <div className="animate-spin text-xl">⏳</div>
        <span className="text-sm font-medium text-slate-600">
          {progressStep}
        </span>
      </div>
      <Progress value={progress} className="h-2" />
    </Card>
  );
}
