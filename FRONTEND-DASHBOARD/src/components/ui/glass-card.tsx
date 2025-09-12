import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  intensity?: "light" | "medium" | "strong";
}

export function GlassCard({ 
  className, 
  intensity = "medium", 
  children, 
  ...props 
}: GlassCardProps) {
  const intensityClasses = {
    light: "bg-white/5 backdrop-blur-xs border-white/10",
    medium: "bg-white/10 backdrop-blur-sm border-white/20",
    strong: "bg-white/20 backdrop-blur-md border-white/30"
  };

  return (
    <Card 
      className={cn(
        "shadow-glass transition-all duration-300 hover:shadow-elevated",
        intensityClasses[intensity],
        className
      )}
      {...props}
    >
      {children}
    </Card>
  );
}