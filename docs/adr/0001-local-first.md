# ADR 0001 — Local-first

## Decisión

Procesar datos junto a sus fuentes y usar PostgreSQL local. El bind por defecto es loopback y no existe telemetría externa.

## Motivo

Los datasets pueden alcanzar cientos de GB o TB; subirlos a cloud administrado por Kiriox aumenta coste, exposición y latencia. La arquitectura local preserva control operativo y permite procesar por streaming.

## Consecuencias

El operador gestiona PostgreSQL, backups, claves y capacidad local. La API requiere contratos claros para que la evolución de conectores no rompa el pipeline.
