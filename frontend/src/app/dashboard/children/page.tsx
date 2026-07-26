"use client";

import { useState, useEffect, useCallback } from "react";
import { api, type ChildRecord } from "@/lib/api-client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import Link from "next/link";

type AgeGroup = "small" | "middle" | "large";

const AGE_DISPLAY: Record<AgeGroup, string> = {
  small: "小班（3-4岁）",
  middle: "中班（4-5岁）",
  large: "大班（5-6岁）",
};

const AGE_COLORS: Record<AgeGroup, string> = {
  small: "bg-pink-100 text-pink-700",
  middle: "bg-blue-100 text-blue-700",
  large: "bg-purple-100 text-purple-700",
};

const PAGE_SIZE = 10;

export default function ChildrenPage() {
  const [children, setChildren] = useState<ChildRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add form
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");
  const [newAge, setNewAge] = useState<AgeGroup>("middle");
  const [newClass, setNewClass] = useState("");
  const [newBirth, setNewBirth] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [saving, setSaving] = useState(false);

  // Edit modal
  const [editChild, setEditChild] = useState<ChildRecord | null>(null);
  const [editName, setEditName] = useState("");
  const [editAge, setEditAge] = useState<AgeGroup>("middle");
  const [editClass, setEditClass] = useState("");
  const [editBirth, setEditBirth] = useState("");
  const [editNotes, setEditNotes] = useState("");

  // Import
  const [showImport, setShowImport] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{ total: number; imported: number; skipped: number; errors: Array<{ row: string; reason: string }> } | null>(null);

  // Delete confirm
  const [confirmDelete, setConfirmDelete] = useState<{ id: number; name: string } | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  // Filters & pagination
  const [searchQuery, setSearchQuery] = useState("");
  const [filterAge, setFilterAge] = useState<string>("");
  const [filterClass, setFilterClass] = useState("");
  const [page, setPage] = useState(1);

  // Fetch children (static import — no dynamic import overhead)
  const fetchChildren = useCallback(async () => {
    try {
      setError(null);
      const data = await api.children.list({
        age_group: filterAge || undefined,
        class_name: filterClass || undefined,
        search: searchQuery || undefined,
      });
      setChildren(data.children);
      setPage(1);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载幼儿列表失败";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [filterAge, filterClass, searchQuery]);

  useEffect(() => {
    fetchChildren();
  }, [fetchChildren]);

  // Collect unique class names for filter dropdown
  const classNames = [...new Set(children.map((c) => c.class_name).filter(Boolean))] as string[];

  // Pagination
  const totalPages = Math.max(1, Math.ceil(children.length / PAGE_SIZE));
  const paginatedChildren = children.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // ── Add child ──
  const addChild = async () => {
    if (!newName.trim()) {
      toast.error("请输入幼儿姓名");
      return;
    }
    setSaving(true);
    try {
      await api.children.create({
        name: newName.trim(),
        age_group: newAge,
        class_name: newClass.trim() || undefined,
        birth_date: newBirth || undefined,
        notes: newNotes.trim() || undefined,
      });
      setNewName("");
      setNewClass("");
      setNewBirth("");
      setNewNotes("");
      setShowAdd(false);
      toast.success(`已添加 ${newName.trim()}`);
      await fetchChildren();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "添加失败");
    } finally {
      setSaving(false);
    }
  };

  // ── Edit child ──
  const openEdit = (child: ChildRecord) => {
    setEditChild(child);
    setEditName(child.name);
    setEditAge(child.age_group as AgeGroup);
    setEditClass(child.class_name || "");
    setEditBirth(child.birth_date ? child.birth_date.slice(0, 10) : "");
    setEditNotes(child.notes || "");
  };
  const saveEdit = async () => {
    if (!editChild || !editName.trim()) return;
    setSaving(true);
    try {
      await api.children.update(editChild.id, {
        name: editName.trim(),
        age_group: editAge,
        class_name: editClass.trim() || undefined,
        birth_date: editBirth || undefined,
        notes: editNotes.trim() || undefined,
      });
      setEditChild(null);
      toast.success(`已更新 ${editName.trim()}`);
      await fetchChildren();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "更新失败");
    } finally {
      setSaving(false);
    }
  };

  // ── Delete child ──
  const deleteChild = async (id: number, name: string) => {
    setDeleting(id);
    try {
      await api.children.delete(id);
      toast.success(`已删除 ${name}`);
      setConfirmDelete(null);
      await fetchChildren();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeleting(null);
    }
  };

  // ── CSV Import ──
  const handleImport = async () => {
    if (!importFile) return;
    setImporting(true);
    setImportResult(null);
    try {
      const result = await api.children.importCSV(importFile);
      setImportResult(result);
      if (result.imported > 0) {
        toast.success(`成功导入 ${result.imported} 名幼儿`);
        await fetchChildren();
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "导入失败");
    } finally {
      setImporting(false);
    }
  };

  const downloadTemplate = () => {
    const csv = "name,age_group,class_name,birth_date,notes\n小明,middle,中一班,2020-03-15,活泼好动\n小红,large,大一班,2019-07-20,专注力好\n";
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "幼儿导入模板.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  // ── Loading ──
  if (loading) {
    return (
      <div className="flex-1 p-6 max-w-5xl mx-auto flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-500">正在加载幼儿列表...</p>
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error) {
    return (
      <div className="flex-1 p-6 max-w-5xl mx-auto">
        <Card className="p-12 text-center border-red-200 bg-red-50">
          <div className="text-4xl mb-3">⚠️</div>
          <h3 className="font-semibold text-red-700 mb-2">加载失败</h3>
          <p className="text-sm text-red-500 mb-4">{error}</p>
          <button
            onClick={() => { setLoading(true); setError(null); fetchChildren(); }}
            className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700 transition-colors"
          >
            重试
          </button>
        </Card>
      </div>
    );
  }

  // ── Main ──
  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">👶 幼儿管理</h1>
          <p className="text-sm text-slate-500 mt-1">
            管理班级幼儿档案，追踪每位幼儿的发展历程
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowImport(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white text-indigo-600 text-sm font-medium border border-indigo-300 hover:bg-indigo-50 transition-colors"
          >
            📥 批量导入
          </button>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            ➕ 添加幼儿
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="🔍 搜索姓名..."
          value={searchQuery}
          onChange={(e) => { setSearchQuery(e.target.value); setLoading(true); }}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm w-48 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select
          value={filterAge}
          onChange={(e) => { setFilterAge(e.target.value); setLoading(true); }}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">全部年龄段</option>
          <option value="small">小班（3-4岁）</option>
          <option value="middle">中班（4-5岁）</option>
          <option value="large">大班（5-6岁）</option>
        </select>
        <select
          value={filterClass}
          onChange={(e) => { setFilterClass(e.target.value); setLoading(true); }}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">全部班级</option>
          {classNames.map((cn) => (
            <option key={cn} value={cn}>{cn}</option>
          ))}
        </select>
        {(searchQuery || filterAge || filterClass) && (
          <button
            onClick={() => { setSearchQuery(""); setFilterAge(""); setFilterClass(""); setLoading(true); }}
            className="px-3 py-2 text-sm text-slate-500 hover:text-slate-700"
          >
            ✕ 清除筛选
          </button>
        )}
      </div>

      {/* Add form */}
      {showAdd && (
        <Card className="p-6 border-2 border-indigo-200 bg-indigo-50">
          <h3 className="font-semibold text-slate-700 mb-4">添加新幼儿</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-600 block mb-1">姓名 *</label>
              <input
                type="text" value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="幼儿姓名"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                onKeyDown={(e) => e.key === "Enter" && addChild()}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600 block mb-1">年龄段 *</label>
              <select value={newAge} onChange={(e) => setNewAge(e.target.value as AgeGroup)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="small">小班（3-4岁）</option>
                <option value="middle">中班（4-5岁）</option>
                <option value="large">大班（5-6岁）</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600 block mb-1">班级</label>
              <input
                type="text" value={newClass}
                onChange={(e) => setNewClass(e.target.value)}
                placeholder="如：中一班"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600 block mb-1">出生日期</label>
              <input
                type="date" value={newBirth}
                onChange={(e) => setNewBirth(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="mt-3">
            <label className="text-sm font-medium text-slate-600 block mb-1">备注</label>
            <input
              type="text" value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              placeholder="特殊需求、学习特点等"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={addChild} disabled={saving}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50">
              {saving ? "保存中..." : "确认添加"}
            </button>
            <button onClick={() => setShowAdd(false)}
              className="px-4 py-2 rounded-lg bg-white text-slate-600 text-sm border border-slate-300 hover:bg-slate-50">
              取消
            </button>
          </div>
        </Card>
      )}

      {/* Children list */}
      {children.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-4xl mb-3">📋</div>
          <h3 className="font-semibold text-slate-700 mb-2">暂无幼儿记录</h3>
          <p className="text-sm text-slate-500">点击"添加幼儿"开始建立班级档案</p>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {paginatedChildren.map((child) => (
              <Card key={child.id} className="p-5 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-lg">
                      👶
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800">{child.name}</h3>
                      <div className="flex items-center gap-3 mt-0.5">
                        <Badge className={AGE_COLORS[child.age_group as AgeGroup] || "bg-slate-100 text-slate-600"}>
                          {AGE_DISPLAY[child.age_group as AgeGroup] || child.age_group}
                        </Badge>
                        {child.class_name && (
                          <span className="text-xs text-slate-500">🏫 {child.class_name}</span>
                        )}
                        {child.parent_access_code && (
                          <span className="text-xs text-slate-400 font-mono">
                            🔑 {child.parent_access_code}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard/assessment?child=${encodeURIComponent(child.name)}&age=${child.age_group}`}
                      className="px-3 py-1.5 rounded-lg bg-indigo-100 text-indigo-700 text-xs font-medium hover:bg-indigo-200 transition-colors"
                    >
                      📸 分析操作单
                    </Link>
                    <Link
                      href={`/dashboard/children/${child.id}/reports`}
                      className="px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-700 text-xs font-medium hover:bg-emerald-200 transition-colors"
                    >
                      📊 查看报告
                    </Link>
                    <button
                      onClick={() => openEdit(child)}
                      className="px-3 py-1.5 rounded-lg bg-amber-100 text-amber-700 text-xs font-medium hover:bg-amber-200 transition-colors"
                    >
                      ✏️ 编辑
                    </button>
                    <button
                      onClick={() => setConfirmDelete({ id: child.id, name: child.name })}
                      disabled={deleting === child.id}
                      className="px-3 py-1.5 rounded-lg bg-red-100 text-red-600 text-xs font-medium hover:bg-red-200 transition-colors disabled:opacity-50"
                    >
                      {deleting === child.id ? "删除中..." : "🗑️ 删除"}
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm disabled:opacity-40 hover:bg-slate-50"
              >
                ← 上一页
              </button>
              <span className="text-sm text-slate-500">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm disabled:opacity-40 hover:bg-slate-50"
              >
                下一页 →
              </button>
            </div>
          )}
        </>
      )}

      <Separator />

      {/* Footer */}
      <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
        <p className="text-sm text-slate-500">
          💡 <span className="font-medium">提示：</span>
          共 {children.length} 名幼儿。数据已持久化到数据库，支持按班级筛选和导入。
        </p>
      </div>

      {/* ── Edit Modal ── */}
      {editChild && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setEditChild(null)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-lg text-slate-800 mb-4">✏️ 编辑 {editChild.name}</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-slate-600 block mb-1">姓名</label>
                <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-600 block mb-1">年龄段</label>
                <select value={editAge} onChange={(e) => setEditAge(e.target.value as AgeGroup)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="small">小班（3-4岁）</option>
                  <option value="middle">中班（4-5岁）</option>
                  <option value="large">大班（5-6岁）</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-600 block mb-1">班级</label>
                <input type="text" value={editClass} onChange={(e) => setEditClass(e.target.value)}
                  placeholder="如：中一班"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-600 block mb-1">出生日期</label>
                <input type="date" value={editBirth} onChange={(e) => setEditBirth(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-600 block mb-1">备注</label>
                <textarea value={editNotes} onChange={(e) => setEditNotes(e.target.value)} rows={2}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
            </div>
            <div className="flex gap-2 mt-4 justify-end">
              <button onClick={saveEdit} disabled={saving}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50">
                {saving ? "保存中..." : "保存修改"}
              </button>
              <button onClick={() => setEditChild(null)}
                className="px-4 py-2 rounded-lg bg-white text-slate-600 text-sm border border-slate-300 hover:bg-slate-50">
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Confirm Modal ── */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setConfirmDelete(null)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm mx-4 text-center" onClick={(e) => e.stopPropagation()}>
            <div className="text-4xl mb-3">⚠️</div>
            <h3 className="font-semibold text-slate-800 mb-2">确认删除</h3>
            <p className="text-sm text-slate-500 mb-4">
              确定要删除 <span className="font-semibold text-red-600">{confirmDelete.name}</span> 的记录吗？此操作不可撤销。
            </p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => deleteChild(confirmDelete.id, confirmDelete.name)}
                disabled={deleting === confirmDelete.id}
                className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700 disabled:opacity-50"
              >
                {deleting === confirmDelete.id ? "删除中..." : "确认删除"}
              </button>
              <button onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 rounded-lg bg-white text-slate-600 text-sm border border-slate-300 hover:bg-slate-50">
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Import Modal ── */}
      {showImport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => { setShowImport(false); setImportResult(null); setImportFile(null); }}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-lg text-slate-800 mb-4">📥 批量导入幼儿</h3>

            {!importResult ? (
              <>
                <p className="text-sm text-slate-500 mb-4">
                  上传 CSV 文件批量导入幼儿名单。文件需包含表头行，支持 UTF-8 / GBK 编码。
                </p>
                <div className="p-6 border-2 border-dashed border-slate-300 rounded-xl text-center mb-4">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="text-sm"
                  />
                  {importFile && (
                    <p className="text-sm text-green-600 mt-2">已选择：{importFile.name}</p>
                  )}
                </div>
                <div className="text-xs text-slate-400 mb-4">
                  列格式：<code>name</code>(必填) <code>age_group</code>(必填: small/middle/large) <code>class_name</code>(可选) <code>birth_date</code>(可选) <code>notes</code>(可选)
                </div>
                <div className="flex gap-2">
                  <button onClick={handleImport} disabled={!importFile || importing}
                    className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50">
                    {importing ? "导入中..." : "开始导入"}
                  </button>
                  <button onClick={downloadTemplate}
                    className="px-4 py-2 rounded-lg bg-white text-slate-600 text-sm border border-slate-300 hover:bg-slate-50">
                    📄 下载模板
                  </button>
                  <button onClick={() => { setShowImport(false); setImportFile(null); }}
                    className="px-4 py-2 rounded-lg bg-white text-slate-600 text-sm border border-slate-300 hover:bg-slate-50">
                    取消
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="space-y-3 mb-4">
                  <div className="flex gap-4 text-center">
                    <div className="flex-1 p-3 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-slate-700">{importResult.total}</div>
                      <div className="text-xs text-slate-500">总计</div>
                    </div>
                    <div className="flex-1 p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-700">{importResult.imported}</div>
                      <div className="text-xs text-green-600">成功导入</div>
                    </div>
                    <div className="flex-1 p-3 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-700">{importResult.skipped}</div>
                      <div className="text-xs text-red-600">跳过</div>
                    </div>
                  </div>
                  {importResult.errors.length > 0 && (
                    <div className="max-h-40 overflow-y-auto border border-red-200 rounded-lg p-3 bg-red-50">
                      <p className="text-xs font-medium text-red-700 mb-2">错误详情：</p>
                      {importResult.errors.map((e, i) => (
                        <p key={i} className="text-xs text-red-600">
                          第 {e.row} 行：{e.reason}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                <button onClick={() => { setShowImport(false); setImportResult(null); setImportFile(null); }}
                  className="w-full px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700">
                  完成
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
