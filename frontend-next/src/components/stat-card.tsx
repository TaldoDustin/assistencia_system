"use client";

import type { ReactNode } from "react";
import { motion } from "motion/react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  icon?: ReactNode;
  hint?: string;
  tone?: "default" | "positive" | "negative";
}

const TONE_CLASSES: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "text-foreground",
  positive: "text-emerald-600 dark:text-emerald-400",
  negative: "text-red-600 dark:text-red-400",
};

export function StatCard({ label, value, icon, hint, tone = "default" }: StatCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
    >
      <Card className="border-border/60 shadow-none transition-shadow duration-200 hover:shadow-sm">
        <CardContent className="flex flex-col gap-2 px-5 py-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{label}</span>
            {icon && <span className="text-muted-foreground">{icon}</span>}
          </div>
          <span className={cn("text-2xl font-semibold tracking-tight", TONE_CLASSES[tone])}>
            {value}
          </span>
          {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
        </CardContent>
      </Card>
    </motion.div>
  );
}
