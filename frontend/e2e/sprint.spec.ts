import { expect, test } from "@playwright/test";

test("el wizard recorre tres pasos sencillos sin mutar datos", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Fuentes de datos" })).toBeVisible();
  await page.getByRole("button", { name: "Agregar fuente" }).click();
  await expect(page.getByText("01 / 03")).toBeVisible();

  await page.getByLabel("Nombre de la fuente").fill("Prueba E2E visual");
  await page.getByRole("button", { name: "Elegir tipo de archivo" }).click();
  await expect(page.getByText("02 / 03")).toBeVisible();
  await page.getByLabel("Elige el archivo").setInputFiles("../outputs/transacciones-prueba.csv");
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(page.getByText("03 / 03")).toBeVisible();

  await expect(page.getByRole("heading", { name: "Confirma y activa" })).toBeVisible();
  await expect(page.getByText("Prueba E2E visual")).toBeVisible();
  await expect(page.getByRole("button", { name: /Crear y revisar fuente|Guardando…/ })).toBeVisible();
});

test("las vistas operativas principales son navegables", async ({ page }) => {
  await page.goto("/");
  for (const item of ["Conectar una base de datos", "Actividad", "Datos por revisar", "Automatizaciones", "Preferencias"]) {
    await page.getByRole("button", { name: item, exact: true }).click();
  }
  await expect(page.getByRole("heading", { name: "Preferencias", exact: true })).toBeVisible();
});
