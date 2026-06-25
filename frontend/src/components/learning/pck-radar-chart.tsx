"use client";

/**
 * Pure SVG radar/spider chart for PCK 4-dimension visualization.
 * No external chart library — zero dependencies.
 */

interface SubDim {
  key: string;
  name: string;
}

interface Dimension {
  key: string;
  name: string;
  sub_dimensions: SubDim[];
}

interface PckRadarChartProps {
  dimensions: Dimension[];
  scores?: Record<string, number>; // dimension key → score 0-100
  size?: number;
}

export function PckRadarChart({ dimensions, scores, size = 320 }: PckRadarChartProps) {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.38;
  const levels = 4; // L1-L4

  // Calculate axis angles (4 dimensions → 4 axes)
  const n = dimensions.length;
  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2; // Start from top

  const getPoint = (index: number, value: number) => {
    const angle = startAngle + index * angleStep;
    const r = (value / 100) * radius;
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  };

  const getLevelPoint = (index: number, level: number) => {
    const angle = startAngle + index * angleStep;
    const lr = (level / levels) * radius;
    return {
      x: cx + lr * Math.cos(angle),
      y: cy + lr * Math.sin(angle),
    };
  };

  // Build score polygon
  const scorePoints = dimensions
    .map((d, i) => {
      const score = scores?.[d.key] ?? 0;
      return getPoint(i, score);
    });

  const scorePath = scorePoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ") + " Z";

  // Dimension colors
  const dimColors = ["#3b82f6", "#f59e0b", "#10b981", "#8b5cf6"];

  return (
    <div className="flex flex-col items-center">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="drop-shadow-sm"
      >
        {/* Level rings */}
        {Array.from({ length: levels }, (_, l) => {
          const levelRadius = ((l + 1) / levels) * radius;
          const ringPoints = Array.from({ length: n }, (_, i) => {
            const angle = startAngle + i * angleStep;
            return {
              x: cx + levelRadius * Math.cos(angle),
              y: cy + levelRadius * Math.sin(angle),
            };
          });
          const ringPath = ringPoints
            .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
            .join(" ") + " Z";
          return (
            <path
              key={l}
              d={ringPath}
              fill="none"
              stroke={l === levels - 1 ? "#cbd5e1" : "#e2e8f0"}
              strokeWidth={l === levels - 1 ? 1.5 : 0.5}
              strokeDasharray={l < levels - 1 ? "4 4" : undefined}
            />
          );
        })}

        {/* Axis lines */}
        {dimensions.map((_, i) => {
          const end = getPoint(i, 100);
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={end.x}
              y2={end.y}
              stroke="#e2e8f0"
              strokeWidth={1}
            />
          );
        })}

        {/* Score fill */}
        <path
          d={scorePath}
          fill="rgba(59, 130, 246, 0.15)"
          stroke="#3b82f6"
          strokeWidth={2}
        />

        {/* Score dots */}
        {scorePoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={4}
            fill={dimColors[i]}
            stroke="white"
            strokeWidth={1.5}
          />
        ))}

        {/* Dimension labels */}
        {dimensions.map((d, i) => {
          const angle = startAngle + i * angleStep;
          const labelR = radius + 36;
          const lx = cx + labelR * Math.cos(angle);
          const ly = cy + labelR * Math.sin(angle);
          return (
            <text
              key={i}
              x={lx}
              y={ly}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-slate-700 font-semibold"
              fontSize="13"
            >
              {d.name}
            </text>
          );
        })}

        {/* Sub-dimension labels along axes */}
        {dimensions.map((d, i) => {
          return d.sub_dimensions.slice(0, 2).map((sd, si) => {
            const angle = startAngle + i * angleStep;
            const frac = 0.55 + si * 0.25;
            const sr = frac * radius;
            const sx = cx + sr * Math.cos(angle);
            const sy = cy + sr * Math.sin(angle);
            return (
              <text
                key={`${i}-${si}`}
                x={sx}
                y={sy}
                textAnchor="middle"
                dominantBaseline="central"
                className="fill-slate-400"
                fontSize="9"
              >
                {sd.name}
              </text>
            );
          });
        })}
      </svg>

      {/* Dimension legend */}
      <div className="flex gap-3 mt-3 flex-wrap justify-center">
        {dimensions.map((d, i) => {
          const score = scores?.[d.key];
          return (
            <div key={d.key} className="flex items-center gap-1.5 text-xs">
              <span
                className="w-2.5 h-2.5 rounded-full inline-block"
                style={{ backgroundColor: dimColors[i] }}
              />
              <span className="text-slate-600">{d.name}</span>
              {score !== undefined && (
                <span className="font-semibold text-slate-800">{score}%</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
