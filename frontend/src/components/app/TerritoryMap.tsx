"use client";

import * as maplibregl from "maplibre-gl";
import type {
  ExpressionSpecification,
  GeoJSONSource,
  MapLayerMouseEvent,
  StyleSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Locale } from "@/content/types";
import kingdom from "@/content/maroc-contour.json";
import { basemapLayers } from "@/lib/basemapStyle";
import type { FacilityCollection, UnitCollection, UnitProperties } from "@/lib/maps";

// The worker is served by src/app/maplibre/[file]/route.ts (bundlers cannot resolve it).
maplibregl.setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const PETROL = "#12343b";
const TERRACOTTA = "#a8461f";

export type HoverInfo = { unit: UnitProperties; x: number; y: number } | null;

export function baseStyle(code: string, locale: Locale): StyleSpecification {
  const origin = window.location.origin;
  return {
    version: 8,
    glyphs: `${origin}/basemap/fonts/{fontstack}/{range}.pbf`,
    sprite: `${origin}/basemap/sprites/light`,
    sources: {
      protomaps: {
        type: "vector",
        tiles: [`${origin}/api/tiles/${code}/{z}/{x}/{y}.mvt`],
        maxzoom: 15,
        attribution: "© OpenStreetMap · Protomaps",
      },
    },
    // Filtered layers: the Kingdom of Morocco in its entirety (cartography rules).
    layers: basemapLayers(locale),
  };
}

export function TerritoryMap({
  code,
  locale,
  units,
  facilities,
  visibleCategories,
  colors,
  selectedId,
  onHover,
  onSelect,
  onMap,
  unitColors,
}: {
  code: string;
  locale: Locale;
  units: UnitCollection;
  facilities: FacilityCollection;
  visibleCategories: string[];
  colors: Record<string, string>;
  selectedId: number | null;
  onHover: (info: HoverInfo) => void;
  onSelect: (id: number | null) => void;
  onMap?: (map: maplibregl.Map | null) => void;
  /** Choropleth: fill colour per unit id (null when the map shows boundaries only). */
  unitColors?: Record<number, string> | null;
}) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [ready, setReady] = useState(false);
  const callbacks = useRef({ onHover, onSelect, onMap });
  useEffect(() => {
    callbacks.current = { onHover, onSelect, onMap };
  }, [onHover, onSelect, onMap]);

  const labels = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: units.features.map((f) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: f.properties.label },
        properties: { name: (locale === "ar" && f.properties.name_ar) || f.properties.name_fr },
      })),
    }),
    [units, locale],
  );

  // Create the map once per territory and language (the base map labels change with it).
  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: baseStyle(code, locale),
      bounds: (units.meta.bbox as [number, number, number, number]) ?? undefined,
      fitBoundsOptions: { padding: 40 },
      attributionControl: { compact: true },
      minZoom: 3, // the national view stays reachable by zooming out
      dragRotate: false,
      pitchWithRotate: false,
      canvasContextAttributes: { preserveDrawingBuffer: true }, // lets the map be exported as an image
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "metric", maxWidth: 140 }), "bottom-right");
    let hovered: number | null = null;

    map.on("load", () => {
      // Outer border of the Kingdom of Morocco, southern provinces included (Natural Earth,
      // Morocco point of view), drawn by MAJAL independently of the base map.
      map.addSource("kingdom", { type: "geojson", data: kingdom as GeoJSON.Feature });
      map.addLayer({
        id: "kingdom-outline",
        type: "line",
        source: "kingdom",
        maxzoom: 10,
        paint: { "line-color": PETROL, "line-width": 1.3, "line-opacity": 0.55 },
      });
      map.addSource("units", { type: "geojson", data: units, promoteId: "id" });
      map.addSource("unit-labels", { type: "geojson", data: labels });
      map.addSource("facilities", { type: "geojson", data: facilities });

      map.addLayer({
        id: "units-fill",
        type: "fill",
        source: "units",
        paint: {
          "fill-color": ["coalesce", ["feature-state", "color"], PETROL],
          "fill-opacity": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            0.22,
            ["boolean", ["feature-state", "hover"], false],
            0.16,
            0.05,
          ],
        },
      });
      map.addLayer({
        id: "units-line",
        type: "line",
        source: "units",
        paint: {
          "line-color": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            TERRACOTTA,
            PETROL,
          ],
          "line-width": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            3,
            ["boolean", ["feature-state", "hover"], false],
            2.2,
            1.2,
          ],
          "line-opacity": 0.85,
        },
      });
      map.addLayer({
        id: "facilities",
        type: "circle",
        source: "facilities",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 1.6, 12, 3, 15, 5.5],
          "circle-color": PETROL,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 9, 0, 13, 1],
          "circle-opacity": 0.9,
        },
      });
      map.addLayer({
        id: "unit-labels",
        type: "symbol",
        source: "unit-labels",
        layout: {
          "text-field": ["get", "name"],
          "text-font": ["Noto Sans Medium"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 9, 11, 13, 15],
          "text-max-width": 8,
          "text-allow-overlap": false,
        },
        paint: {
          "text-color": PETROL,
          "text-halo-color": "rgba(246,243,236,0.95)",
          "text-halo-width": 1.6,
        },
      });

      map.on("mousemove", "units-fill", (event: MapLayerMouseEvent) => {
        const feature = event.features?.[0];
        if (!feature) return;
        const id = Number(feature.id);
        if (hovered !== null && hovered !== id) {
          map.setFeatureState({ source: "units", id: hovered }, { hover: false });
        }
        hovered = id;
        map.setFeatureState({ source: "units", id }, { hover: true });
        map.getCanvas().style.cursor = "pointer";
        const unit = units.features.find((f) => f.properties.id === id)?.properties;
        if (unit) callbacks.current.onHover({ unit, x: event.point.x, y: event.point.y });
      });
      map.on("mouseleave", "units-fill", () => {
        if (hovered !== null)
          map.setFeatureState({ source: "units", id: hovered }, { hover: false });
        hovered = null;
        map.getCanvas().style.cursor = "";
        callbacks.current.onHover(null);
      });
      map.on("click", (event: maplibregl.MapMouseEvent) => {
        const feature = map.queryRenderedFeatures(event.point, { layers: ["units-fill"] })[0];
        callbacks.current.onSelect(feature ? Number(feature.id) : null);
      });
      // Opening view: framed on the studied territory (agglomeration or province).
      if (units.meta.bbox) {
        map.fitBounds(units.meta.bbox as [number, number, number, number], {
          padding: 40,
          duration: 0,
        });
      }
      setReady(true);
      callbacks.current.onMap?.(map);
    });

    mapRef.current = map;
    return () => {
      setReady(false);
      callbacks.current.onMap?.(null);
      map.remove();
      mapRef.current = null;
    };
    // Units and facilities are refreshed by the effects below without recreating the map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, locale]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    (map.getSource("units") as GeoJSONSource | undefined)?.setData(units);
    (map.getSource("unit-labels") as GeoJSONSource | undefined)?.setData(labels);
    (map.getSource("facilities") as GeoJSONSource | undefined)?.setData(facilities);
    if (units.meta.bbox) {
      map.fitBounds(units.meta.bbox as [number, number, number, number], {
        padding: 40,
        duration: 600,
      });
    }
  }, [ready, units, labels, facilities]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    map.setFilter("facilities", ["in", ["get", "category"], ["literal", visibleCategories]]);
    const entries = Object.entries(colors);
    if (entries.length === 0) {
      // No facility category (e.g. the citizen dashboard map): a plain colour, not a « match ».
      map.setPaintProperty("facilities", "circle-color", PETROL);
      return;
    }
    const match: unknown[] = ["match", ["get", "category"]];
    for (const [category, color] of entries) match.push(category, color);
    match.push(PETROL);
    map.setPaintProperty("facilities", "circle-color", match as ExpressionSpecification);
  }, [ready, visibleCategories, colors]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    for (const feature of units.features) {
      map.setFeatureState(
        { source: "units", id: feature.properties.id },
        { selected: feature.properties.id === selectedId },
      );
    }
  }, [ready, selectedId, units]);

  // Choropleth colours: stronger fill, selection shown by the outline only.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    for (const feature of units.features) {
      const id = feature.properties.id;
      map.setFeatureState({ source: "units", id }, { color: unitColors?.[id] ?? null });
    }
    map.setPaintProperty(
      "units-fill",
      "fill-opacity",
      unitColors
        ? ["case", ["boolean", ["feature-state", "hover"], false], 0.92, 0.78]
        : [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            0.22,
            ["boolean", ["feature-state", "hover"], false],
            0.16,
            0.05,
          ],
    );
    map.setPaintProperty(
      "units-fill",
      "fill-color",
      unitColors
        ? ["coalesce", ["feature-state", "color"], "#e8e4da"]
        : ["case", ["boolean", ["feature-state", "selected"], false], TERRACOTTA, PETROL],
    );
  }, [ready, unitColors, units]);

  return <div ref={container} className="h-full w-full" />;
}
