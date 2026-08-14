import { Toaster } from "sonner";

import Navigation from "@/app/_components/layouts/Navigation";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0A1628]">
      <Navigation />
      <div className="pt-16">{children}</div>
      {/* Without this, every toast.error() in the chat UI — including the
          rate-limit notice — is a silent no-op. */}
      <Toaster position="top-center" richColors />
    </div>
  );
}
