"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CameraCapture } from "@/components/camera-capture";

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const ALLOWED_TYPES = [
  "image/jpeg", "image/png", "image/webp", "application/pdf",
];
const ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".pdf"];

interface UploadPanelProps {
  preview: string | null;
  previews?: string[] | null;
  onFileChange: (file: File, previewUrl: string) => void;
  onFilesChange?: (files: File[], previewUrls: string[]) => void;
  onCameraCapture: (file: File, previewUrl: string) => void;
}

export function UploadPanel({
  preview,
  previews,
  onFileChange,
  onFilesChange,
  onCameraCapture,
}: UploadPanelProps) {
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
      return `文件"${file.name}"过大（${(file.size / 1024 / 1024).toFixed(1)}MB），最大支持20MB`;
    }
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `不支持的文件格式"${ext}"，支持：JPG, PNG, WEBP, PDF`;
    }
    return null;
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;
    setError(null);

    const errors: string[] = [];
    const validFiles: File[] = [];
    const validUrls: string[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const f = fileList[i];
      const err = validateFile(f);
      if (err) {
        errors.push(err);
      } else {
        validFiles.push(f);
        validUrls.push(URL.createObjectURL(f));
      }
    }

    if (errors.length > 0) {
      setError(errors.join("；"));
    }

    if (validFiles.length === 0) return;

    if (validFiles.length === 1) {
      onFileChange(validFiles[0], validUrls[0]);
    } else if (onFilesChange) {
      onFilesChange(validFiles, validUrls);
    }
  };

  const previewList = previews && previews.length > 0 ? previews : (preview ? [preview] : []);

  return (
    <Card className="p-6 lg:col-span-2">
      <Tabs defaultValue="file">
        <TabsList className="mb-4">
          <TabsTrigger value="file">📁 上传图片</TabsTrigger>
          <TabsTrigger value="camera">📷 摄像头</TabsTrigger>
          <TabsTrigger value="scan">📄 扫描件</TabsTrigger>
        </TabsList>

        {/* Error display */}
        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
            <span className="text-red-500 flex-shrink-0 mt-0.5">⚠️</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="text-xs text-red-500 underline mt-1 hover:text-red-700"
              >
                关闭
              </button>
            </div>
          </div>
        )}

        <TabsContent value="file">
          <div
            className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-indigo-400 transition-colors cursor-pointer"
            onClick={() => document.getElementById("file-input")?.click()}
          >
            {previewList.length > 0 ? (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2 justify-center">
                  {previewList.slice(0, 4).map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      alt={`Preview ${i + 1}`}
                      className="max-h-32 rounded-lg shadow-sm object-cover"
                    />
                  ))}
                  {previewList.length > 4 && (
                    <div className="flex items-center justify-center w-24 h-32 rounded-lg bg-slate-100 text-sm text-slate-500">
                      +{previewList.length - 4}
                    </div>
                  )}
                </div>
                <p className="text-xs text-slate-400">
                  已选 {previewList.length} 张，点击更换
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-4xl">📁</div>
                <p className="text-slate-600 font-medium">
                  点击或拖拽上传操作单
                </p>
                <p className="text-xs text-slate-400">
                  支持多选，最多10张 · JPG, PNG, WEBP, PDF（最大20MB）
                </p>
              </div>
            )}
            <input
              id="file-input"
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              className="hidden"
              multiple
              onChange={handleFileInput}
            />
          </div>
        </TabsContent>

        <TabsContent value="camera">
          <CameraCapture onCapture={onCameraCapture} />
        </TabsContent>

        <TabsContent value="scan">
          <div
            className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-indigo-400 transition-colors cursor-pointer"
            onClick={() => document.getElementById("scan-input")?.click()}
          >
            <div className="space-y-3">
              <div className="text-4xl">📄</div>
              <p className="text-slate-600 font-medium">扫描件 / PDF 上传</p>
              <p className="text-xs text-slate-400">
                支持 PDF 和图片扫描件，系统会自动进行图像增强处理和文字识别
              </p>
            </div>
            <input
              id="scan-input"
              type="file"
              accept="application/pdf,image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleFileInput}
            />
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
