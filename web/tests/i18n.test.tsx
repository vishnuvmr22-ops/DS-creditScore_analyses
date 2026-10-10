import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { Shell } from "@/components/shell";
import { THEME_KEY } from "@/components/theme";
import { ApiContext } from "@/lib/config";
import { LOCALE_KEY } from "@/lib/dictionary";
import { LocaleProvider } from "@/lib/i18n";
import { translate } from "@/lib/dictionary";
import { validateField, ALL_FIELDS } from "@/lib/field-spec";
import { makeApi } from "./helpers";

function renderShell() {
  return render(
    <ApiContext.Provider value={{ api: makeApi(), baseUrl: "http://svc:8080" }}>
      <LocaleProvider>
        <Shell>
          <p>child</p>
        </Shell>
      </LocaleProvider>
    </ApiContext.Provider>,
  );
}

afterEach(() => {
  localStorage.clear();
});

describe("interface language", () => {
  it("defaults to English and switches the whole chrome to Spanish on toggle", async () => {
    const user = userEvent.setup();
    renderShell();

    const nav = screen.getByRole("navigation");
    // English by default.
    expect(within(nav).getByText("Decisioning")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "es" }));

    // The navigation and the provenance banner both follow the choice.
    expect(within(nav).getByText("Decisiones")).toBeInTheDocument();
    expect(screen.getAllByText(/Datos sintéticos/).length).toBeGreaterThan(0);
    expect(localStorage.getItem(LOCALE_KEY)).toBe("es");
  });

  it("restores the stored language on a fresh mount", async () => {
    localStorage.setItem(LOCALE_KEY, "es");
    renderShell();
    const nav = screen.getByRole("navigation");
    await waitFor(() => expect(within(nav).getByText("Auditoría")).toBeInTheDocument());
  });
});

describe("appearance", () => {
  it("defaults to dark when nothing is stored", async () => {
    renderShell();
    await waitFor(() => {
      const dark = screen.getByRole("button", { name: "dark" });
      expect(dark.getAttribute("aria-pressed")).toBe("true");
    });
    expect(localStorage.getItem(THEME_KEY)).toBeNull();
  });
});

describe("translate — the resolver", () => {
  it("interpolates named vars", () => {
    expect(translate("en", "shell.model", { v: "7" })).toBe("model 7");
    expect(translate("es", "shell.model", { v: "7" })).toBe("modelo 7");
  });

  it("falls back to English, then to the key itself", () => {
    // A symbol that is not a key passes through unchanged (used for "$"/"%").
    expect(translate("es", "%")).toBe("%");
    expect(translate("en", "no.such.key")).toBe("no.such.key");
  });
});

describe("validation follows the active locale", () => {
  const age = ALL_FIELDS.find((f) => f.name === "age")!;

  it("returns English by default and Spanish when asked", () => {
    expect(validateField(age, "17")).toBe("Must be 18 or more.");
    expect(validateField(age, "17", "es")).toBe("Debe ser 18 o más.");
  });
});
