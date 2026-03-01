import type { FlashMessage } from "@/types";

interface FlashProps {
  msg: FlashMessage | null;
  onClear: () => void;
}

export default function Flash({ msg, onClear }: FlashProps) {
  if (!msg) return null;
  return (
    <div
      className={`px-4 py-3 rounded-lg text-sm flex items-center justify-between ${
        msg.type === "error"
          ? "bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300"
          : "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300"
      }`}
    >
      <span>{msg.text}</span>
      <button onClick={onClear} className="ml-2 opacity-50 hover:opacity-100">
        ✕
      </button>
    </div>
  );
}
