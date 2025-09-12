import { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: string;
  children?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ title, description, badge, children, actions }: PageHeaderProps) {
  return (
    <div className="border-b border-border bg-gradient-to-r from-background to-muted/30 backdrop-blur-sm">
      <div className="px-6 py-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                {title}
              </h1>
              {badge && (
                <Badge variant="secondary" className="text-xs">
                  {badge}
                </Badge>
              )}
            </div>
            {description && (
              <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
                {description}
              </p>
            )}
            {children}
          </div>
          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}