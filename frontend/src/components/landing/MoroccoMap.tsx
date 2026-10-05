import outline from "@/content/morocco-outline.json";

type CityCode = keyof typeof outline.cities;

const [, , WIDTH, HEIGHT] = outline.viewBox;

/** Hero map: the outline draws itself, then Rabat and Tétouan light up. */
export function MoroccoMap({ label, cities }: { label: string; cities: Record<CityCode, string> }) {
  const rabat = outline.cities.rabat;
  const tetouan = outline.cities.tetouan;
  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={label}
      className="morocco-map h-full w-full overflow-visible"
    >
      <defs>
        <pattern id="map-dots" width="14" height="14" patternUnits="userSpaceOnUse">
          <circle cx="1.5" cy="1.5" r="1.1" fill="currentColor" />
        </pattern>
        <radialGradient id="city-glow">
          <stop offset="0%" stopColor="var(--color-terracotta-light)" stopOpacity="0.85" />
          <stop offset="100%" stopColor="var(--color-terracotta-light)" stopOpacity="0" />
        </radialGradient>
        <clipPath id="map-clip">
          <path d={outline.path} />
        </clipPath>
      </defs>

      <g className="map-fill">
        <path d={outline.path} className="fill-cream/[0.06]" />
        <rect
          width={WIDTH}
          height={HEIGHT}
          fill="url(#map-dots)"
          clipPath="url(#map-clip)"
          className="text-cream/20"
        />
      </g>
      <path
        d={outline.path}
        pathLength={1}
        className="map-outline stroke-cream/80"
        fill="none"
        strokeWidth={1.6}
        strokeLinejoin="round"
      />

      <path
        d={`M${rabat[0]},${rabat[1]} Q${(rabat[0] + tetouan[0]) / 2 - 30},${(rabat[1] + tetouan[1]) / 2 - 10} ${tetouan[0]},${tetouan[1]}`}
        className="map-link stroke-terracotta-light"
        fill="none"
        strokeWidth={1.4}
        strokeDasharray="4 5"
      />

      {(Object.keys(outline.cities) as CityCode[]).map((code, index) => {
        const [x, y] = outline.cities[code];
        return (
          <g key={code} className="map-city" style={{ animationDelay: `${1.6 + index * 0.35}s` }}>
            <circle cx={x} cy={y} r={28} fill="url(#city-glow)" className="map-city-glow" />
            <circle
              cx={x}
              cy={y}
              r={7}
              className="map-city-pulse stroke-terracotta-light"
              fill="none"
            />
            <circle cx={x} cy={y} r={4.5} className="fill-terracotta-light" />
            <text
              x={x - 14}
              y={y + 7}
              textAnchor="end"
              className="map-city-label fill-cream text-[22px] font-medium"
            >
              {cities[code]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/** Close-up of one demo territory, cut from the same outline. */
export function TerritoryCloseUp({ code, name }: { code: CityCode; name: string }) {
  const [x, y] = outline.cities[code];
  const size = 150;
  return (
    <svg
      viewBox={`${x - size / 2} ${y - size / 2} ${size} ${size}`}
      preserveAspectRatio="xMidYMid slice"
      role="img"
      aria-label={name}
      className="bg-sea h-full w-full"
    >
      <path d={outline.context} className="fill-land/55 stroke-petrol/15" strokeWidth={0.4} />
      <path d={outline.path} className="fill-land stroke-petrol/30" strokeWidth={0.5} />
      <circle cx={x} cy={y} r={10} className="map-city-glow fill-terracotta/20" />
      <circle cx={x} cy={y} r={3} className="fill-terracotta" />
    </svg>
  );
}
