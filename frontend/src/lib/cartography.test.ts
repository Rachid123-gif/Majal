import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import contour from "@/content/maroc-contour.json";
import outline from "@/content/morocco-outline.json";

/*
 * Territorial integrity of the Kingdom of Morocco (non-negotiable, see CLAUDE.md), for the
 * maps drawn by MAJAL itself: landing page, presentation, close-ups, login page, app contour.
 */

type Point = [number, number];

function polygonsFromPath(d: string): Point[][] {
  return d
    .split("M")
    .filter(Boolean)
    .map((part) =>
      part
        .replace(/Z$/, "")
        .split("L")
        .map((pair) => pair.split(",").map(Number) as Point),
    );
}

function inside([x, y]: Point, ring: Point[]): boolean {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

const checks = Object.entries(outline.checks) as [string, Point][];

describe("maps drawn by MAJAL — Kingdom of Morocco in its entirety", () => {
  it("draws the Kingdom as one unbroken outline, without any inner line", () => {
    expect(polygonsFromPath(outline.path)).toHaveLength(1);
  });

  it("includes the southern provinces in the Kingdom's outline", () => {
    const [kingdom] = polygonsFromPath(outline.path);
    for (const [name, point] of checks) {
      expect(inside(point, kingdom), name).toBe(true);
    }
  });

  it("never draws a neighbouring territory over the southern provinces", () => {
    for (const polygon of polygonsFromPath(outline.context)) {
      for (const [name, point] of checks) {
        expect(inside(point, polygon), name).toBe(false);
      }
    }
  });

  it("uses a contour covering the Kingdom from Tangier to Lagouira in the application map", () => {
    const ys = (contour.geometry.coordinates as number[][][][]).flat(2).map((p) => p[1]);
    expect(Math.min(...ys)).toBeLessThan(21.5);
    expect(Math.max(...ys)).toBeGreaterThan(35.5);
  });

  it("lets only the filtered style use the Protomaps base map", () => {
    const root = path.resolve(__dirname, "..");
    const offenders: string[] = [];
    const walk = (dir: string) => {
      for (const name of readdirSync(dir)) {
        const file = path.join(dir, name);
        if (statSync(file).isDirectory()) walk(file);
        else if (/\.(tsx?|jsx?)$/.test(name) && !/\.test\./.test(name)) {
          const text = readFileSync(file, "utf-8");
          if (
            text.includes("@protomaps/basemaps") &&
            !file.endsWith(path.join("lib", "basemapStyle.ts"))
          ) {
            offenders.push(path.relative(root, file));
          }
        }
      }
    };
    walk(root);
    expect(offenders).toEqual([]);
  });
});
