import { useCallback, useEffect, useRef, useState } from "react";

type CameraRecorderModalProps = {
  open: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
  title: string;
};

type RecorderStatus = "idle" | "ready" | "recording" | "recorded";

function pickMimeType(): string {
  const candidates = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm", "video/mp4"];
  for (const type of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

/**
 * In-app webcam recorder. Opens the camera, records a clip with MediaRecorder,
 * and hands the result back as a File (same shape the file-upload flow uses).
 * Requires a secure context (https or localhost) for camera access.
 */
export function CameraRecorderModal({ open, onClose, onCapture, title }: CameraRecorderModalProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null);
  const [recordedFile, setRecordedFile] = useState<File | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const attachLivePreview = useCallback(() => {
    if (videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      void videoRef.current.play().catch(() => {});
    }
  }, []);

  // Acquire the camera while the modal is open; release it on close/unmount.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setStatus("idle");
    setError(null);
    setElapsed(0);

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser cannot access a camera here. Camera capture needs HTTPS (or localhost).");
      return;
    }

    navigator.mediaDevices
      .getUserMedia({ video: true, audio: false })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        attachLivePreview();
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof DOMException && err.name === "NotAllowedError"
            ? "Camera permission was denied. Allow camera access in your browser, then reopen this."
            : "Unable to start a camera. Check that one is connected and not in use by another app."
        );
      });

    return () => {
      cancelled = true;
      stopStream();
    };
  }, [open, attachLivePreview, stopStream]);

  // Recording elapsed-time ticker.
  useEffect(() => {
    if (status !== "recording") return;
    const id = window.setInterval(() => setElapsed((value) => value + 1), 1000);
    return () => window.clearInterval(id);
  }, [status]);

  // Revoke the recorded-clip object URL when it changes or on unmount.
  useEffect(() => {
    return () => {
      if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    };
  }, [recordedUrl]);

  function startRecording() {
    if (!streamRef.current) return;
    try {
      chunksRef.current = [];
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(streamRef.current, mimeType ? { mimeType } : undefined);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || "video/webm";
        const blob = new Blob(chunksRef.current, { type });
        const extension = type.includes("mp4") ? "mp4" : "webm";
        const file = new File([blob], `recording-${Date.now()}.${extension}`, { type });
        setRecordedFile(file);
        setRecordedUrl(URL.createObjectURL(blob));
        setStatus("recorded");
      };
      recorderRef.current = recorder;
      setElapsed(0);
      recorder.start();
      setStatus("recording");
    } catch {
      setError("Recording is not supported in this browser.");
    }
  }

  function stopRecording() {
    recorderRef.current?.stop();
    recorderRef.current = null;
  }

  function retake() {
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedUrl(null);
    setRecordedFile(null);
    setElapsed(0);
    setStatus("ready");
    attachLivePreview();
  }

  function close() {
    if (status === "recording") stopRecording();
    stopStream();
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedUrl(null);
    setRecordedFile(null);
    setStatus("idle");
    onClose();
  }

  function useVideo() {
    if (recordedFile) onCapture(recordedFile);
    close();
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="presentation">
      <div aria-label={title} aria-modal="true" className="card relative w-full max-w-xl" role="dialog">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            aria-label="Close"
            className="rounded-full border border-rim px-3 py-1 text-sm text-ink/70 transition hover:border-accent hover:text-accent"
            onClick={close}
            type="button"
          >
            ✕
          </button>
        </div>

        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-300/60 bg-rose-500/10 px-4 py-4 text-sm text-rose-700">
            {error}
          </div>
        ) : (
          <div className="mt-4">
            <div className="relative overflow-hidden rounded-2xl bg-slate-900">
              <video
                className={`aspect-video w-full object-cover ${status === "recorded" ? "hidden" : ""}`}
                muted
                playsInline
                ref={videoRef}
              />
              {status === "recorded" && recordedUrl ? (
                <video className="aspect-video w-full object-cover" controls playsInline src={recordedUrl} />
              ) : null}
              {status === "recording" ? (
                <span className="absolute left-3 top-3 inline-flex items-center gap-2 rounded-full bg-black/60 px-3 py-1 text-xs font-semibold text-white">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-rose-500" />
                  {formatTime(elapsed)}
                </span>
              ) : null}
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-3">
              {status === "idle" ? <p className="text-sm text-ink/60">Starting camera…</p> : null}
              {status === "ready" ? (
                <button className="button-primary" onClick={startRecording} type="button">
                  Start Recording
                </button>
              ) : null}
              {status === "recording" ? (
                <button className="button-primary" onClick={stopRecording} type="button">
                  Stop Recording
                </button>
              ) : null}
              {status === "recorded" ? (
                <>
                  <button className="button-primary" onClick={useVideo} type="button">
                    Use Video
                  </button>
                  <button className="button-secondary" onClick={retake} type="button">
                    Retake
                  </button>
                </>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
