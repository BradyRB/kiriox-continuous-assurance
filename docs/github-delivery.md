# Guía de entrega del módulo en GitHub

Esta guía publica el proyecto local en un repositorio nuevo y permite que otra persona lo clone, lo levante y valide el flujo completo.

## 1. Revisión antes de publicar

Desde PowerShell, abre el proyecto:

```powershell
cd "C:\Users\zen01\Documents\Codex\2026-09-14\files-pasted-by-the-user-act"
git --version
git status
```

El proyecto ya incluye un `.gitignore` para no subir el entorno virtual de Python, `node_modules`, builds, almacenamiento local, caches, logs ni `.env`.

Antes del primer commit revisa siempre la lista exacta de archivos:

```powershell
git add .
git status --short
git diff --cached --name-only
```

No continúes si aparecen `.env`, contraseñas reales, tokens, `backend/.venv`, `frontend/node_modules`, `backend/storage` o archivos de `work/`. Si detectas algo, ejecuta `git restore --staged <archivo>` y corrígelo antes del commit.

## 2. Crear el repositorio en GitHub

1. Entra en https://github.com e inicia sesión.
2. Pulsa `+` y selecciona `New repository`.
3. Usa un nombre como `kiriox-continuous-assurance`.
4. Selecciona `Private` si el código aún no debe ser público.
5. No marques `Add a README`, `.gitignore` ni licencia: este proyecto ya tiene esos archivos localmente.
6. Pulsa `Create repository`.

## 3. Inicializar y subir el código desde PowerShell

Sustituye `TU_USUARIO` por tu usuario u organización de GitHub:

```powershell
cd "C:\Users\zen01\Documents\Codex\2026-09-14\files-pasted-by-the-user-act"
git init
git branch -M main
git add .
git status --short
git diff --cached --name-only
git commit -m "feat: complete Kiriox Continuous Assurance MVP"
git remote add origin https://github.com/TU_USUARIO/kiriox-continuous-assurance.git
git push -u origin main
```

Cuando GitHub solicite autenticación, usa la ventana del navegador o un token de GitHub; no pegues contraseñas en el código ni en archivos del proyecto. Si ya existe un remoto llamado `origin`, usa:

```powershell
git remote set-url origin https://github.com/TU_USUARIO/kiriox-continuous-assurance.git
git push -u origin main
```

Comprueba la publicación:

```powershell
git remote -v
git log -1 --oneline
```

## 4. Alternativa con GitHub Desktop

También puedes abrir GitHub Desktop, elegir `File > Add local repository`, seleccionar esta carpeta, pulsar `Publish repository`, elegir nombre/visibilidad y confirmar `Publish repository`.

## 5. Cómo debe probarlo tu jefe después de clonar

Requisitos: Docker Desktop iniciado, Python 3.11+, Node.js 20+ y Git.

```powershell
git clone https://github.com/TU_USUARIO/kiriox-continuous-assurance.git
cd kiriox-continuous-assurance
docker compose up -d postgres
```

En una terminal PowerShell:

```powershell
.\scripts\start-backend.ps1
```

En otra terminal PowerShell:

```powershell
.\scripts\start-frontend.ps1
```

Después debe abrir:

- Aplicación: http://127.0.0.1:3000/
- API: http://127.0.0.1:8000/
- Documentación interactiva: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

El procedimiento funcional completo, los datos esperados y los resultados validados están en [SPRINT-REPORT-FOR-MANAGER.md](../outputs/SPRINT-REPORT-FOR-MANAGER.md).

## 6. Entrega recomendada

Comparte a tu jefe:

1. La URL del repositorio.
2. El [reporte del sprint](../outputs/SPRINT-REPORT-FOR-MANAGER.md).
3. Esta guía de publicación y arranque.
4. La advertencia de que las credenciales `kiriox/kiriox` son únicamente de desarrollo local y no deben reutilizarse en producción.

El repositorio no contiene los archivos temporales de `work/`; para la prueba principal se pueden usar los CSV versionados en `outputs/transacciones-prueba.csv` y `outputs/transacciones-invalidas.csv`.
