"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MobilityTrendPoint } from "@/lib/api/analytics";

interface Props {
  data: MobilityTrendPoint[];
}

const SERIES = [
  { key: "outgoing", label: "Sortants", color: "#3b82f6" },
  { key: "incoming", label: "Entrants", color: "#22c55e" },
  { key: "internships", label: "Stages", color: "#f97316" },
  { key: "complementary", label: "Complémentaires", color: "#a855f7" },
] as const;

export function MobilityTrendsChart({ data }: Readonly<Props>) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.1} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            borderRadius: "8px",
            border: "1px solid hsl(var(--border))",
            background: "hsl(var(--popover))",
            color: "hsl(var(--popover-foreground))",
            fontSize: 13,
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 13, paddingTop: 12 }}
        />
        {SERIES.map(({ key, label, color }) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            name={label}
            stroke={color}
            strokeWidth={2.5}
            dot={{ r: 4, fill: color }}
            activeDot={{ r: 6 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
