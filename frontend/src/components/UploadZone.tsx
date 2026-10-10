import { useRef, useState } from "react";

type Props = {
  file: File | null;
  onFile: (f: File | null) => void;
};

export function UploadZone({ file, onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  function take(f: File | null) {
    if (!f) return onFile(null);
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      alert("Only PDF resumes are supported.");
      return;
    }
    onFile(f);
  }

  return (
    <div
      className={`upload-zone ${drag ? "drag" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        take(e.dataTransfer.files?.[0] ?? null);
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(e) => take(e.target.files?.[0] ?? null)}
      />
      <strong>{file ? file.name : "Drop your resume PDF here"}</strong>
      <span>{file ? `${(file.size / 1024).toFixed(0)} KB — click to replace` : "or click to browse · PDF only · not stored"}</span>
    </div>
  );
}
