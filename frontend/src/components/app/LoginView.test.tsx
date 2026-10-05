import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LoginView } from "@/components/app/LoginView";
import { LocaleProvider } from "@/i18n/LocaleProvider";

const replace = vi.fn();
let search = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  useSearchParams: () => search,
}));

function mockLogin(status: number) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      status === 200
        ? new Response(JSON.stringify({ username: "professeur", display_name: {}, roles: [] }), {
            status: 200,
          })
        : new Response(JSON.stringify({ detail: "x" }), { status }),
    ),
  );
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Identifiant"), { target: { value: "professeur" } });
  fireEvent.change(screen.getByLabelText("Mot de passe"), { target: { value: "secret" } });
  fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));
}

beforeEach(() => {
  search = new URLSearchParams();
  replace.mockReset();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("LoginView", () => {
  it("opens the dashboard after a successful login", async () => {
    mockLogin(200);
    render(
      <LocaleProvider>
        <LoginView />
      </LocaleProvider>,
    );
    fillAndSubmit();
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/tableau-de-bord"));
  });

  it("returns to the requested page, but never to another site", async () => {
    mockLogin(200);
    search = new URLSearchParams({ suite: "//evil.example" });
    render(
      <LocaleProvider>
        <LoginView />
      </LocaleProvider>,
    );
    fillAndSubmit();
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/tableau-de-bord"));
  });

  it("explains a wrong password in plain French", async () => {
    mockLogin(401);
    render(
      <LocaleProvider>
        <LoginView />
      </LocaleProvider>,
    );
    fillAndSubmit();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Identifiant ou mot de passe incorrect.",
    );
    expect(replace).not.toHaveBeenCalled();
  });
});
