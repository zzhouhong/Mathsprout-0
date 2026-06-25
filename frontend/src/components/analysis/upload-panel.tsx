"use client";

import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CameraCapture } from "@/components/camera-capture";

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
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    if (fileList.length === 1) {
      const f = fileList[0];
      onFileChange(f, URL.createObjectURL(f));
    } else if (onFilesChange) {
      const files: File[] = [];
      const urls: string[] = [];
      for (let i = 0; i < fileList.length; i++) {
        files.push(fileList[i]);
        urls.push(URL.createObjectURL(fileList[i]));
      }
      onFilesChange(files, urls);
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
          <div className="text-center py-8 space-y-3">
            <div className="text-4xl">📄</div>
            <p className="text-slate-600">扫描件上传</p>
            <p className="text-xs text-slate-400">
              支持 PDF 和图片格式的扫描件，系统会自动进行图像增强处理
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
