import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ConfidenceBadge } from "@/components/app/ConfidenceBadge";
import { LocaleProvider } from "@/i18n/LocaleProvider";

afterEach(cleanup);

describe("ConfidenceBadge", () => {
  it.each([
    ["official", "Officiel"],
    ["open", "Ouvert"],
    ["estimated", "Estimé"],
    ["fictitious", "Fictif"],
  ] as const)("names the %s level in words, with an explanation on hover", (kind, label) => {
    render(
      <LocaleProvider>
        <ConfidenceBadge kind={kind} />
      </LocaleProvider>,
    );
    const badge = screen.getByText(label);
    expect(badge).toHaveAttribute("title");
    expect(badge.getAttribute("title")).not.toBe("");
  });
});
