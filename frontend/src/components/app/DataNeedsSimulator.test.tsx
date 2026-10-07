import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DataNeedsSimulator } from "@/components/app/DataNeedsSimulator";
import { LocaleProvider } from "@/i18n/LocaleProvider";
import type { DataNeeds } from "@/lib/dataNeeds";
import { DATA } from "@/lib/dataNeeds.fixture";

const L = (fr: string) => ({ fr, ar: fr });
const data = {
  ...DATA,
  statuses: {
    official: L("Officiel"),
    open: L("Ouvert"),
    estimated: L("Estimé"),
    missing: L("Manquant"),
  },
  effects: {
    computed: { verb: L("calculer"), label: L("Calculés") },
    reliable: { verb: L("fiabiliser"), label: L("Fiabilisés") },
    finer: { verb: L("affiner"), label: L("Affinés") },
  },
  institutions: [
    { code: "hcp", name: L("Direction régionale du HCP") },
    { code: "aref", name: L("AREF") },
  ],
} as unknown as DataNeeds;

afterEach(cleanup);

describe("DataNeedsSimulator", () => {
  it("updates the counter live and always says that nothing is added", () => {
    render(
      <LocaleProvider>
        <DataNeedsSimulator data={data} />
      </LocaleProvider>,
    );
    expect(
      screen.getByText("Simulation : aucune donnée n'est ajoutée", { exact: false }),
    ).toBeTruthy();
    expect(screen.getByText("2 indicateurs disponibles sur 4")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Direction régionale du HCP"));
    fireEvent.click(screen.getByLabelText("AREF"));
    expect(
      screen.getByText("3 indicateurs disponibles sur 4 — +1 grâce à la simulation"),
    ).toBeTruthy();
    expect(screen.getByText("Calculés : 1 · Fiabilisés : 1 · Affinés : 1")).toBeTruthy();
  });
});
