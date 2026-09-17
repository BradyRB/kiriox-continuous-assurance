import { expect, test } from "@playwright/test";

test("el wizard recorre las ocho etapas sin mutar datos", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Fuentes de datos" })).toBeVisible();
  await page.getByRole("button", { name: "Nueva fuente" }).click();
  await expect(page.getByText("01 / 08")).toBeVisible();

  await page.getByLabel("Nombre de la fuente").fill("Prueba E2E visual");
  for (let step = 1; step < 8; step += 1) {
    await page.getByRole("button", { name: "Continuar" }).click();
    await expect(page.getByText(`${String(step + 1).padStart(2, "0")} / 08`)).toBeVisible();
  }

  await expect(page.getByRole("heading", { name: "Revisión" })).toBeVisible();
  await expect(page.getByText("Prueba E2E visual")).toBeVisible();
  await expect(page.getByRole("button", { name: /Crear fuente|Guardando…/ })).toBeVisible();
});

test("las vistas operativas principales son navegables", async ({ page }) => {
  await page.goto("/");
  for (const item of ["Explorador PostgreSQL", "Historial de ejecuciones", "Excepciones", "Schedules", "Configuración"]) {
    await page.getByRole("button", { name: item, exact: true }).click();
    await expect(page.getByRole("heading", { name: item, exact: true })).toBeVisible();
  }
});
