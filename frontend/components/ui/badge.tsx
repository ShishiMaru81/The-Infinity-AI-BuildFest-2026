import { cn } from "@/lib/utils";

const priorityColors: Record<string, string> = {
  CRITICAL: "bg-red-600/20 text-red-400 border-red-600",
  HIGH: "bg-orange-600/20 text-orange-400 border-orange-600",
  MEDIUM: "bg-yellow-600/20 text-yellow-400 border-yellow-600",
  LOW: "bg-green-600/20 text-green-400 border-green-600",
  SAFE: "bg-green-600/20 text-green-400 border-green-600",
};

export function Badge({
  children,
  priority = "LOW",
  className,
}: {
  children: React.ReactNode;
  priority?: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        priorityColors[priority] || priorityColors.LOW,
        className
      )}
    >
      {children}
    </span>
  );
}
