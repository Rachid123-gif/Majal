import type { DataNeeds, DataRequestRow } from "@/lib/dataNeeds";

const L = { fr: "x", ar: "x" };

function request(code: string, holders: string[], extra: Partial<DataRequestRow>): DataRequestRow {
  return {
    code,
    priority: "essential",
    priority_label: L,
    holders,
    alternatives: [],
    complementary: [],
    data: L,
    detail: L,
    format: L,
    frequency: L,
    value: L,
    effects: { computed: [], reliable: [], finer: [] },
    finer_scale: null,
    themes: [],
    requires_also: [],
    context: false,
    boundaries: false,
    ...extra,
  };
}

/** Small territory for the simulator tests: two axes, four requests. */
export const DATA = {
  summary: { total: 4, available: 2, missing: 2 },
  axes: [
    {
      code: "education",
      label: L,
      total: 2,
      available: 1,
      counts: { official: 0, open: 0, estimated: 1, missing: 1 },
      indicators: ["EDU_ECOLES", "EDU_PROX"],
    },
    {
      code: "demographie",
      label: L,
      total: 2,
      available: 1,
      counts: { official: 1, open: 0, estimated: 0, missing: 1 },
      indicators: ["DEM_POP", "URB_DOC"],
    },
  ],
  requests: [
    request("population_6_14", ["hcp"], {
      effects: { computed: ["EDU_ECOLES"], reliable: [], finer: [] },
      requires_also: ["ecoles"],
    }),
    request("ecoles", ["aref"], {
      effects: { computed: ["EDU_ECOLES"], reliable: ["EDU_PROX"], finer: [] },
      requires_also: ["population_6_14"],
    }),
    request("rgph", ["hcp"], { effects: { computed: [], reliable: [], finer: ["DEM_POP"] } }),
    request("voirie", ["rabat", "sale"], { themes: ["voirie"] }),
  ],
} as unknown as DataNeeds;
