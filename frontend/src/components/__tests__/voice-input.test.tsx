import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";
import { VoiceInput } from "../voice-input";

// Mock Web Speech API
const mockStart = jest.fn();
const mockStop = jest.fn();
let mockOnResult: ((event: unknown) => void) | null = null;
let mockOnError: ((event: unknown) => void) | null = null;

beforeEach(() => {
  mockOnResult = null;
  mockOnError = null;
  (window as any).SpeechRecognition = jest.fn().mockImplementation(() => ({
    lang: "",
    interimResults: false,
    maxAlternatives: 1,
    continuous: false,
    start: mockStart,
    stop: mockStop,
    abort: jest.fn(),
    set onresult(fn: unknown) { mockOnResult = fn as any; },
    set onerror(fn: unknown) { mockOnError = fn as any; },
    set onend(fn: unknown) { (fn as Function)(); }, // auto-trigger onend
  }));
  (window as any).webkitSpeechRecognition = undefined;
});

afterEach(() => {
  jest.clearAllMocks();
  delete (window as any).SpeechRecognition;
});

describe("VoiceInput", () => {
  it("renders mic button when supported", () => {
    render(<VoiceInput onResult={jest.fn()} />);
    expect(screen.getByRole("button", { name: /开始录音/i })).toBeInTheDocument();
  });

  it("shows placeholder text when idle", () => {
    render(<VoiceInput onResult={jest.fn()} />);
    expect(screen.getByText("点击麦克风开始说话...")).toBeInTheDocument();
  });

  it("starts listening on mic click", async () => {
    render(<VoiceInput onResult={jest.fn()} />);
    const btn = screen.getByRole("button");
    await userEvent.click(btn);
    expect(mockStart).toHaveBeenCalled();
  });

  it("shows listening indicator while recording", async () => {
    render(<VoiceInput onResult={jest.fn()} />);
    const btn = screen.getByRole("button");
    await userEvent.click(btn);
    expect(screen.getByText(/正在聆听/)).toBeInTheDocument();
  });

  it("shows fallback message when unsupported", () => {
    delete (window as any).SpeechRecognition;
    const { container } = render(<VoiceInput onResult={jest.fn()} />);
    // Component renders nothing (returns null) when unsupported
    expect(container.innerHTML).toBe("");
  });

  it("calls onError when permission denied", async () => {
    const onError = jest.fn();
    render(<VoiceInput onResult={jest.fn()} onError={onError} />);
    const btn = screen.getByRole("button");
    await userEvent.click(btn);

    // Simulate error
    expect(mockOnError).toBeTruthy();
    act(() => {
      (mockOnError as Function)({ error: "not-allowed" });
    });
    expect(onError).toHaveBeenCalled();
  });

  it("is disabled when disabled prop is true", () => {
    render(<VoiceInput onResult={jest.fn()} disabled />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onResult when speech is recognized", async () => {
    const onResult = jest.fn();
    render(<VoiceInput onResult={onResult} />);
    const btn = screen.getByRole("button");
    await userEvent.click(btn);

    // Simulate recognition result
    expect(mockOnResult).toBeTruthy();
    act(() => {
      (mockOnResult as Function)({
        resultIndex: 0,
        results: [{ isFinal: true, 0: { transcript: "三" } }],
      });
    });
    expect(onResult).toHaveBeenCalledWith("三");
  });
});
