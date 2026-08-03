import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";
import { AnnotationPanel } from "../analysis/annotation-panel";

// Mock fetch globally
const mockFetch = jest.fn();
beforeEach(() => {
  (global as any).fetch = mockFetch;
  (global as any).localStorage = {
    getItem: jest.fn(() => "test-token"),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  };
  // Initial load returns empty annotations
  mockFetch.mockResolvedValue({
    ok: true,
    json: async () => ({ annotations: [], count: 0 }),
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

describe("AnnotationPanel", () => {
  it("renders the panel with header", async () => {
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    expect(screen.getByText("教学批注")).toBeInTheDocument();
  });

  it("shows empty state when no annotations", async () => {
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    // Wait for fetch to resolve
    const emptyText = await screen.findByText(/暂无批注/);
    expect(emptyText).toBeInTheDocument();
  });

  it("renders input field and submit button", async () => {
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    expect(screen.getByPlaceholderText(/添加教学批注/)).toBeInTheDocument();
    expect(screen.getByText("发布")).toBeInTheDocument();
  });

  it("disables submit button when input is empty", async () => {
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    const btn = screen.getByText("发布");
    expect(btn).toBeDisabled();
  });

  it("enables submit button when text is entered", async () => {
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    const input = screen.getByPlaceholderText(/添加教学批注/);
    await userEvent.type(input, "这是一个测试批注");
    const btn = screen.getByText("发布");
    expect(btn).not.toBeDisabled();
  });

  it("displays existing annotations", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        annotations: [
          { id: 1, author: "张老师", text: "建议加强图形认知", created_at: "2026-06-01T10:00:00" },
          { id: 2, author: "李老师", text: "运算能力提升明显", created_at: "2026-06-15T14:30:00" },
        ],
        count: 2,
      }),
    });
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    const item1 = await screen.findByText("建议加强图形认知");
    expect(item1).toBeInTheDocument();
    expect(screen.getByText("运算能力提升明显")).toBeInTheDocument();
  });

  it("shows annotation count badge", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        annotations: [{ id: 1, author: "张老师", text: "测试", created_at: "2026-06-01T10:00:00" }],
        count: 1,
      }),
    });
    await act(async () => {
      render(<AnnotationPanel reportId={300} />);
    });
    const badge = await screen.findByText("1");
    expect(badge).toBeInTheDocument();
  });
});
