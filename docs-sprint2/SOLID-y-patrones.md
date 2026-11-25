# Principios SOLID y patrones de diseño aplicados en el SGA

Este documento responde a la actividad 6 del Sprint 2 ("Aplicar principios SOLID y patrones de
diseño cuando corresponda"). Muestra **dónde** está cada principio y cada patrón en el código, con
un fragmento corto y el **motivo**, y lo relaciona con el diseño del Sprint 1:

- [Principios de diseño (SOLID)](../docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md)
- [Diseño interno de módulos](../docs/03-diseno-de-software/diseno-interno/diseno-interno-de-modulos.md)
- [C4 nivel 4, sección 4: patrones y principios](../docs/04-modelo-c4/Nivel4-DiagramadeCodigo.md)

> **Nota sobre `docs/`.** El archivo
> [`patrones-de-diseno.md`](../docs/03-diseno-de-software/diseno-interno/patrones-de-diseno.md)
> tiene hoy el mismo contenido que `principios-de-diseno.md`. Como `docs/` no se modifica en el
> Sprint 2, los patrones se toman de la tabla del C4 nivel 4 (Repository, Adapter, State, Unit of
> Work e inyección de dependencias) y del plan de 001
> ([SOLID y patrones](../specs/001-flujo-solicitud/plan.md)), que agrega Strategy.

Rutas: `B/` = `tecnologia/backend/app/`. Los fragmentos están recortados; cada enlace lleva a la
línea real.

---

## 1. Principios SOLID

### S · Responsabilidad única

**Qué dice `docs/`:** "La ruta recibe la petición, el caso de uso coordina la firma, la entidad
aplica las reglas del conducto regular y el repositorio guarda en PostgreSQL."

**Dónde:** firmar un requerimiento pasa por cuatro clases, cada una con un solo motivo para cambiar.

| Responsabilidad | Archivo |
|---|---|
| HTTP: validar la entrada, abrir la transacción y armar la respuesta | [`B/modules/requests/presentacion/router.py#L209`](../tecnologia/backend/app/modules/requests/presentacion/router.py#L209) |
| Coordinar el caso de uso: visibilidad, bloqueo, firma, historial y auditoría | [`B/modules/requests/aplicacion/firmar_requerimiento.py#L90`](../tecnologia/backend/app/modules/requests/aplicacion/firmar_requerimiento.py#L90) |
| Reglas del conducto regular | [`B/modules/requests/dominio/requerimiento.py#L147`](../tecnologia/backend/app/modules/requests/dominio/requerimiento.py#L147) |
| Guardar en PostgreSQL | [`B/modules/requests/infraestructura/repositorio_postgres.py#L66`](../tecnologia/backend/app/modules/requests/infraestructura/repositorio_postgres.py#L66) |

```python
# presentacion/router.py: la ruta solo traduce HTTP al caso de uso.
def firmar(id: uuid.UUID, entrada: DecisionFirmaEntrada, usuario=Depends(solo_firmantes), ...):
    actor = _actor(usuario)
    with fabrica_uow() as uow:
        construir_firmar(uow.sesion).ejecutar(actor, id, entrada.decision, entrada.motivo)
        vista = construir_consultar(uow.sesion).detalle(actor, id)
    return RequerimientoSalida.desde_vista(vista)
```

**Por qué:** un cambio en HTTP (por ejemplo, el campo `documento_revisado` de 002) se hizo solo en
el esquema de la presentación, sin tocar el dominio ni el repositorio.

### O · Abierto/cerrado

**Qué dice `docs/`:** "Para guardar los PDF en otro lugar se crea un nuevo adaptador de
`AlmacenDocumentos`; el caso de uso no se modifica."

**Dónde:** el puerto
[`B/modules/signing/dominio/puertos.py#L88`](../tecnologia/backend/app/modules/signing/dominio/puertos.py#L88)
y su adaptador de disco
[`B/modules/signing/infraestructura/almacen_documentos_disco.py#L16`](../tecnologia/backend/app/modules/signing/infraestructura/almacen_documentos_disco.py#L16).

```python
class AlmacenDocumentos(Protocol):
    """Dónde se guardan los PDF firmados. Cambiar el disco por otro almacenamiento es otro
    adaptador de este puerto; los casos de uso no cambian (ADR-010, abierto/cerrado)."""

    def guardar(self, clave: str, contenido: bytes) -> None: ...  # nunca sobrescribe
    def leer(self, clave: str) -> bytes: ...                      # no hay método para borrar
```

**Por qué:** `EmitirDocumento` guarda el PDF sin saber si va a un disco, a un bucket o a otra
base. Pasar a otro almacenamiento es agregar una clase, sin modificar casos de uso ya probados.
Lo mismo pasa con las reglas: una regla de aprobación nueva es otra implementación de
`ReglaAprobacion` (ver Strategy).

### L · Sustitución de Liskov

**Qué dice `docs/`:** "Cualquier adaptador que cumpla el puerto `FirmadorDocumentos` puede
reemplazar a `FirmadorEd25519` sin errores; en las pruebas se usa uno falso."

**Dónde:** el puerto
[`B/modules/signing/dominio/puertos.py#L56`](../tecnologia/backend/app/modules/signing/dominio/puertos.py#L56),
el adaptador real
[`B/modules/signing/infraestructura/firmador_ed25519.py#L25`](../tecnologia/backend/app/modules/signing/infraestructura/firmador_ed25519.py#L25)
y el doble de prueba
[`tests/firmador_falso.py`](../tecnologia/backend/tests/firmador_falso.py). En 002 se sumaron los
dobles de los puertos de documentos
([`tests/dobles_documentos.py`](../tecnologia/backend/tests/dobles_documentos.py)).

```python
class FirmadorFalso:                      # tests/firmador_falso.py
    metodo = "falso-sha256-v1"

    def firmar(self, contenido: bytes) -> str:
        return self._firma(contenido)

    def verificar(self, contenido: bytes, firma: str, clave_id: str) -> bool:
        return clave_id == self.clave_id and firma == self._firma(contenido)
```

**Por qué:** las pruebas unitarias de `EmitirDocumento` y del conducto regular usan el doble y se
comportan igual que con Ed25519. Si un adaptador no cumpliera el contrato (por ejemplo, devolver
`True` siempre en `verificar`), las pruebas de EQ-02 lo detectarían.

### I · Segregación de interfaces

**Qué dice `docs/`:** "Cada puerto es pequeño y tiene un solo propósito: repositorio, firmador,
almacén de documentos y auditoría, en lugar de una interfaz gigante."

**Dónde:** [`B/modules/signing/dominio/puertos.py`](../tecnologia/backend/app/modules/signing/dominio/puertos.py)
define cinco puertos pequeños: `FirmadorDocumentos`, `RepositorioFirmas`, `AlmacenDocumentos`,
`GeneradorPdf` y `RepositorioDocumentos`.

```python
class GeneradorPdf(Protocol):
    def generar(self, documento: DocumentoPdf, codigo: str, huella_contenido: str) -> bytes: ...
```

**Por qué:** `GeneradorPdfReportLab` implementa un solo método. El almacén de disco no sabe nada
de firmas, y el firmador no sabe nada de archivos. En 002 se agregaron tres puertos nuevos sin
cambiar los de 001.

### D · Inversión de dependencias

**Qué dice `docs/`:** "El caso de uso depende de los puertos del dominio, no de PostgreSQL ni de
`cryptography`; la raíz de composición inyecta los adaptadores."

**Dónde:** el caso de uso recibe puertos en su constructor
([`firmar_requerimiento.py#L90`](../tecnologia/backend/app/modules/requests/aplicacion/firmar_requerimiento.py#L90)),
y la raíz de composición elige los adaptadores
([`B/modules/requests/infraestructura/dependencias.py#L110`](../tecnologia/backend/app/modules/requests/infraestructura/dependencias.py#L110)).

```python
class FirmarRequerimiento:
    def __init__(self, repositorio: Repositorio, firmas: FirmasRequerimiento,
                 auditoria: RegistroAuditoria) -> None: ...

def construir_firmar(sesion: Session) -> FirmarRequerimiento:     # raíz de composición
    return FirmarRequerimiento(
        repositorio=RepositorioRequerimientosPostgres(sesion),
        firmas=construir_servicio_firma(sesion),
        auditoria=construir_registro_auditoria(sesion),
    )
```

**Por qué:** las reglas del conducto regular se prueban sin base de datos. La regla se hace cumplir
con una prueba:
[`tests/unitarias/test_reglas_dependencia.py`](../tecnologia/backend/tests/unitarias/test_reglas_dependencia.py)
falla si un dominio importa `fastapi`, `sqlalchemy`, `cryptography`, `jwt` o `bcrypt`, o si el
dominio o la aplicación de `signing` importan `reportlab`, `os` o `pathlib`.

---

## 2. Patrones de diseño

| Patrón | Dónde (`docs/`) | Archivo |
|---|---|---|
| State | C4 nivel 4; ADR-007 | `requests/dominio/requerimiento.py`, `estado.py` |
| Repository | C4 nivel 4 | `requests/dominio/puertos.py` → `infraestructura/repositorio_postgres.py` |
| Unit of Work | C4 nivel 4; ADR-003 | `core/unidad_trabajo.py` |
| Adapter | C4 nivel 4 | `FirmadorEd25519`, `GeneradorPdfReportLab`, `AlmacenDocumentosDisco` |
| Strategy | Plan de 001 (principio V) | `rules/dominio/regla_aprobacion.py`; el `metodo` de cada firma |
| Inyección de dependencias | C4 nivel 4 | `main.py`, `*/infraestructura/dependencias.py`, `Depends` de FastAPI |

### State (ADR-007)

**Dónde:** [`B/modules/requests/dominio/requerimiento.py#L96`](../tecnologia/backend/app/modules/requests/dominio/requerimiento.py#L96).
Cada estado del conducto regular es una clase. El estado base rechaza todas las acciones, y cada
estado concreto habilita solo las suyas.

```python
class _Estado:
    def firmar(self, req, nivel):
        raise self._no_permitida("firmar")          # por defecto, nada está permitido

class _PendienteFirma(_Estado):
    def firmar(self, req, nivel):
        self._validar_nivel(nivel)                  # solo el nivel que espera este estado
        req.niveles_firmados.add(nivel)
        req._avanzar(self.siguiente)
```

**Por qué:** ningún nivel puede omitirse ni firmar dos veces (RN01, RN02). Una transición no
listada lanza `TransicionNoPermitida`, que la API responde con 409. EQ-01 lo prueba con cada
usuario, cada acción y cada estado.

### Repository

**Dónde:** el puerto
[`B/modules/requests/dominio/puertos.py#L134`](../tecnologia/backend/app/modules/requests/dominio/puertos.py#L134)
y su implementación con SQLAlchemy
[`repositorio_postgres.py#L109`](../tecnologia/backend/app/modules/requests/infraestructura/repositorio_postgres.py#L109).

```python
def obtener_para_actualizar(self, requerimiento_id):
    return self._cargar(
        select(RequerimientoModelo)
        .where(RequerimientoModelo.id == requerimiento_id)
        .with_for_update()                          # bloqueo de fila (ADR-003, EQ-03)
        .execution_options(populate_existing=True)
    )
```

**Por qué:** los casos de uso trabajan con la entidad `Requerimiento`, no con filas. El bloqueo
`FOR UPDATE` queda en la infraestructura, y aun así el caso de uso lo pide de forma explícita:
`obtener_para_actualizar`.

### Unit of Work (ADR-003)

**Dónde:** [`B/core/unidad_trabajo.py#L19`](../tecnologia/backend/app/core/unidad_trabajo.py#L19).

```python
def __exit__(self, tipo, error, traza):
    try:
        if tipo is None:
            sesion.commit()                         # estado, firma, historial y auditoría juntos
        else:
            sesion.rollback()                       # o no se guarda nada
    finally:
        sesion.close()
```

**Por qué:** el estado, la firma, los movimientos de stock, el historial y la auditoría se guardan
en una sola transacción (RN07). En 002, la fila de `documento_emitido` entra en la misma Unidad de
Trabajo que la descarga.

### Adapter

**Dónde:** tres adaptadores que traducen una librería al puerto del dominio:

- [`firmador_ed25519.py#L25`](../tecnologia/backend/app/modules/signing/infraestructura/firmador_ed25519.py#L25): `cryptography` → `FirmadorDocumentos`.
- [`generador_pdf_reportlab.py#L68`](../tecnologia/backend/app/modules/signing/infraestructura/generador_pdf_reportlab.py#L68): ReportLab → `GeneradorPdf`.
- [`almacen_documentos_disco.py#L34`](../tecnologia/backend/app/modules/signing/infraestructura/almacen_documentos_disco.py#L34): sistema de archivos → `AlmacenDocumentos`.

```python
def guardar(self, clave: str, contenido: bytes) -> None:      # AlmacenDocumentosDisco
    ...
    with open(temporal, "xb") as archivo:                     # escritura exclusiva
        archivo.write(contenido)
        os.fsync(archivo.fileno())
    os.link(temporal, ruta)     # falla si el nombre ya existe: nunca se sobrescribe un PDF emitido
```

**Por qué:** RC01 prevé cambiar a certificados acreditados. Eso es un adaptador nuevo de
`FirmadorDocumentos`, sin cambios en `requests`. Además, el dominio queda libre de librerías,
como pide la regla 1 de `principios-de-diseno.md`.

### Strategy

**Dónde:** [`B/modules/rules/dominio/regla_aprobacion.py#L13`](../tecnologia/backend/app/modules/rules/dominio/regla_aprobacion.py#L13).

```python
class ReglaAprobacion(Protocol):
    def requiere_cologe(self, categoria: Categoria, monto_total: Decimal) -> bool: ...

class ReglaCologePorCategoriaOMonto:                # RN03
    def requiere_cologe(self, categoria, monto_total) -> bool:
        return categoria == Categoria.MATERIAL_GUERRA or monto_total >= self._umbral
```

**Por qué:** la regla del COLOGE se inyecta en el envío del requerimiento. Cambiar el umbral o
agregar la aprobación automática (RN04) es otra estrategia, sin tocar `requests`, y eso es lo que
mide EQ-07 (mantenibilidad). La firma aplica la misma idea: cada firma guarda su `metodo`
(`ed25519-sha256-v1`) para elegir cómo se verifica.

### Inyección de dependencias

**Dónde:** [`B/main.py`](../tecnologia/backend/app/main.py) registra los routers; cada módulo tiene su
`infraestructura/dependencias.py` con funciones `construir_*`, y las rutas reciben la sesión y la
Unidad de Trabajo con `Depends`.

```python
@router.get("/{id}/documento.pdf", ...)
def documento_pdf(id, usuario=Depends(usuario_actual), fabrica_uow=Depends(obtener_fabrica_uow)):
    with fabrica_uow() as uow:
        pdf = construir_descargar_pdf(uow.sesion).ejecutar(_actor(usuario), id)
    return _respuesta_pdf(pdf)
```

**Por qué:** la raíz de composición es el único lugar que conoce las clases concretas. Las pruebas
de integración sustituyen la clave de firma por un par Ed25519 generado en memoria sin cambiar el
código de producción.

### Factory: no se usa

El plan de 001 lo decidió así: cada puerto tiene un solo adaptador en producción y no hay familias
de objetos que crear. Las funciones `construir_*` arman los objetos (es inyección de dependencias,
no Factory). Si aparece una familia, por ejemplo varios métodos de firma activos a la vez, se
justificará entonces.

---

## 3. Reglas de `docs/` y cómo se comprueban

Las cuatro "Reglas para programar" de
[`principios-de-diseno.md`](../docs/03-diseno-de-software/diseno-interno/principios-de-diseno.md):

| Regla | Cómo se comprueba |
|---|---|
| 1. El dominio no importa FastAPI, SQLAlchemy ni `cryptography` | `test_el_dominio_es_python_puro` en [`test_reglas_dependencia.py`](../tecnologia/backend/tests/unitarias/test_reglas_dependencia.py), en CI |
| 2. Un módulo no usa el repositorio ni las tablas de otro | `test_un_modulo_no_usa_la_infraestructura_de_otro`, en el mismo archivo |
| 3. Firmar o modificar el stock ocurre en una sola transacción | Unit of Work; EQ-03 ([evidencia](../evidencias/EQ-03/)) y las pruebas de concurrencia de firmas |
| 4. No programar criptografía propia | Solo `cryptography` (Ed25519) y `hashlib` (SHA-256) en `firmador_ed25519.py` y `contenido_canonico.py` |
