"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Activity, Users, Network } from "lucide-react";

interface SidebarItem {
  icon: React.ComponentType<any>;
  label: string;
  path: string;
}

const NAV_ITEMS: SidebarItem[] = [
  { icon: Shield, label: "SOC Dashboard", path: "/dashboard" },
  { icon: Activity, label: "Live Event Log", path: "/live-feed" },
  { icon: Network, label: "Global Trust Graph", path: "/graph-view" },
  { icon: Users, label: "Demo Control Panel", path: "/personas" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-16 flex-col items-center border-r border-soc-border bg-soc-surface py-6">
      {/* Setu Brand Logo */}
      <div className="mb-8 flex items-center justify-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-soc-cyan bg-soc-bg shadow-[0_0_8px_rgba(0,212,255,0.2)]">
          <span className="font-display text-sm font-bold text-soc-cyan">S</span>
        </div>
      </div>

      {/* Navigation Buttons */}
      <nav className="flex flex-1 flex-col items-center gap-6">
        {NAV_ITEMS.map((item) => {
          const IconComponent = item.icon;
          const isActive = pathname === item.path || (item.path !== "/dashboard" && pathname.startsWith(item.path));

          return (
            <div key={item.path} className="group relative">
              <Link
                href={item.path}
                className={`flex h-11 w-11 items-center justify-center rounded-lg border transition-all duration-300 ${
                  isActive
                    ? "border-soc-cyan bg-soc-cyan/10 text-soc-cyan shadow-[0_0_10px_rgba(0,212,255,0.15)]"
                    : "border-transparent text-soc-textSecondary hover:border-soc-border hover:bg-soc-bg hover:text-soc-textPrimary"
                }`}
              >
                <IconComponent className="h-5 w-5" />
              </Link>
              
              {/* Custom Tooltip */}
              <div className="pointer-events-none absolute left-16 top-1/2 z-50 -translate-y-1/2 translate-x-2 rounded border border-soc-border bg-soc-surface px-2.5 py-1 text-xs font-medium text-soc-textPrimary opacity-0 shadow-xl transition-all duration-200 group-hover:translate-x-0 group-hover:opacity-100 whitespace-nowrap">
                {item.label}
              </div>
            </div>
          );
        })}
      </nav>
      
      {/* Decorative Status Signal */}
      <div className="mt-auto flex flex-col items-center">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-soc-green opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-soc-green"></span>
        </span>
      </div>
    </aside>
  );
}
