"""Datos de prueba ficticios del incremento 001 (data-model.md §9, RC13).

Uso (desde tecnologia/backend)::

    python -m seeds.cargar

Es idempotente: los identificadores son fijos (UUID v5 a partir del código) y cada inserción usa
``ON CONFLICT DO NOTHING``, así que ejecutarlo dos veces no duplica nada. La contraseña común de
demostración sale de ``CONTRASENA_DEMO`` y nunca se versiona. Todos los nombres son ficticios.
"""

import sys
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.base_datos import obtener_fabrica_sesiones
from app.core.config import obtener_configuracion
from app.modules.catalog.dominio.tipos import Categoria, TipoOrgano
from app.modules.catalog.infraestructura.modelos import AlmacenModelo, ItemModelo, OrganoModelo
from app.modules.identity.dominio.rol import Rol
from app.modules.identity.infraestructura.hash_bcrypt import HasherBcrypt
from app.modules.identity.infraestructura.modelos import UsuarioModelo
from app.modules.inventory.dominio.tipos import TipoMovimiento
from app.modules.inventory.infraestructura.modelos import MovimientoModelo, StockModelo

ESPACIO_SGA = uuid.UUID("5c1f1d0e-6a0b-4d3c-9a57-000000000001")


def id_fijo(tipo: str, codigo: str) -> uuid.UUID:
    """UUID determinista: el mismo código produce siempre el mismo identificador."""
    return uuid.uuid5(ESPACIO_SGA, f"{tipo}:{codigo}")


# --- Estructura orgánica (ADR-009): COLOGE y servicios, 2 Grandes Unidades con 2 unidades ---
ORGANOS: list[tuple[str, str, TipoOrgano, str | None]] = [
    ("COLOGE", "Comando Logístico del Ejército", TipoOrgano.COLOGE, None),
    ("SINTE", "Servicio de Intendencia del Ejército", TipoOrgano.SERVICIO, "COLOGE"),
    ("SMGE", "Servicio de Material de Guerra del Ejército", TipoOrgano.SERVICIO, "COLOGE"),
    # Órgano del auditor (solo consulta y verificación).
    ("IGE", "Inspectoría General del Ejército", TipoOrgano.SERVICIO, None),
    ("1DE", "1.ª División de Ejército", TipoOrgano.GRAN_UNIDAD, None),
    ("2DE", "2.ª División de Ejército", TipoOrgano.GRAN_UNIDAD, None),
    ("BIM-11", "Batallón de Infantería Motorizado N.° 11", TipoOrgano.UNIDAD, "1DE"),
    ("BIM-12", "Batallón de Infantería Motorizado N.° 12", TipoOrgano.UNIDAD, "1DE"),
    ("BIM-21", "Batallón de Infantería Motorizado N.° 21", TipoOrgano.UNIDAD, "2DE"),
    ("BIM-22", "Batallón de Infantería Motorizado N.° 22", TipoOrgano.UNIDAD, "2DE"),
]

# Un almacén por categoría (data-model.md almacen.categoria).
ALMACENES: list[tuple[str, str, str, Categoria]] = [
    ("SINTE", "Almacén de Intendencia", "SINTE", Categoria.INTENDENCIA),
    ("SMGE", "Almacén de Material de Guerra", "SMGE", Categoria.MATERIAL_GUERRA),
]

# 10 ítems de intendencia y 4 de material de guerra, con valor unitario y stock inicial.
ITEMS: list[tuple[str, str, Categoria, str, str, int]] = [
    ("INT-001", "Ración de campaña", Categoria.INTENDENCIA, "unidad", "35.50", 500),
    ("INT-002", "Uniforme de campaña", Categoria.INTENDENCIA, "unidad", "180.00", 200),
    ("INT-003", "Botas de combate", Categoria.INTENDENCIA, "par", "220.00", 150),
    ("INT-004", "Frazada de lana", Categoria.INTENDENCIA, "unidad", "65.00", 300),
    ("INT-005", "Carpa individual", Categoria.INTENDENCIA, "unidad", "340.00", 80),
    ("INT-006", "Mochila de campaña", Categoria.INTENDENCIA, "unidad", "150.00", 120),
    ("INT-007", "Agua de mesa (bidón de 20 L)", Categoria.INTENDENCIA, "bidón", "12.00", 400),
    ("INT-008", "Arroz (saco de 50 kg)", Categoria.INTENDENCIA, "saco", "160.00", 60),
    ("INT-009", "Menaje de campaña", Categoria.INTENDENCIA, "juego", "45.00", 250),
    ("INT-010", "Poncho impermeable", Categoria.INTENDENCIA, "unidad", "55.00", 10),
    ("MG-001", "Casco balístico", Categoria.MATERIAL_GUERRA, "unidad", "1200.00", 40),
    ("MG-002", "Chaleco de protección", Categoria.MATERIAL_GUERRA, "unidad", "2500.00", 30),
    ("MG-003", "Binocular de campaña", Categoria.MATERIAL_GUERRA, "unidad", "900.00", 25),
    ("MG-004", "Radio portátil", Categoria.MATERIAL_GUERRA, "unidad", "3500.00", 20),
]


@dataclass(frozen=True)
class UsuarioSemilla:
    usuario: str
    nombre_completo: str
    rol: Rol
    organo: str
    almacen: str | None = None


# Usuarios de quickstart.md §3, más los demás por rol que pide data-model.md §9.
USUARIOS: list[UsuarioSemilla] = [
    *(
        UsuarioSemilla(
            f"oficial.{u.lower().replace('-', '')}",
            f"Oficial de logística {u}",
            Rol.OFICIAL_LOGISTICA,
            u,
        )
        for u in ("BIM-11", "BIM-12", "BIM-21", "BIM-22")
    ),
    *(
        UsuarioSemilla(
            f"cmdte.{u.lower().replace('-', '')}", f"Comandante {u}", Rol.COMANDANTE_UNIDAD, u
        )
        for u in ("BIM-11", "BIM-12", "BIM-21", "BIM-22")
    ),
    UsuarioSemilla("jlog.1de", "Jefe de logística 1.ª DE", Rol.JEFE_LOGISTICA_GU, "1DE"),
    UsuarioSemilla("jlog.2de", "Jefe de logística 2.ª DE", Rol.JEFE_LOGISTICA_GU, "2DE"),
    UsuarioSemilla(
        "jalm.sinte", "Jefe del almacén de Intendencia", Rol.JEFE_ALMACEN, "SINTE", "SINTE"
    ),
    UsuarioSemilla(
        "almacenero.sinte", "Almacenero de Intendencia", Rol.ALMACENERO, "SINTE", "SINTE"
    ),
    UsuarioSemilla(
        "jalm.smge", "Jefe del almacén de Material de Guerra", Rol.JEFE_ALMACEN, "SMGE", "SMGE"
    ),
    UsuarioSemilla(
        "almacenero.smge", "Almacenero de Material de Guerra", Rol.ALMACENERO, "SMGE", "SMGE"
    ),
    UsuarioSemilla("auditor", "Auditor de la Inspectoría", Rol.AUDITOR, "IGE"),
]


def _cargar_catalogo(sesion: Session) -> None:
    for codigo, nombre, tipo, padre in ORGANOS:
        sesion.execute(
            insert(OrganoModelo)
            .values(
                id=id_fijo("organo", codigo),
                codigo=codigo,
                nombre=nombre,
                tipo=tipo,
                padre_id=id_fijo("organo", padre) if padre else None,
            )
            .on_conflict_do_nothing()
        )
    for codigo, nombre, organo, categoria in ALMACENES:
        sesion.execute(
            insert(AlmacenModelo)
            .values(
                id=id_fijo("almacen", codigo),
                nombre=nombre,
                organo_id=id_fijo("organo", organo),
                categoria=categoria,
            )
            .on_conflict_do_nothing()
        )
    for codigo, nombre, categoria, unidad_medida, valor, _ in ITEMS:
        sesion.execute(
            insert(ItemModelo)
            .values(
                id=id_fijo("item", codigo),
                codigo=codigo,
                nombre=nombre,
                categoria=categoria,
                unidad_medida=unidad_medida,
                valor_unitario=Decimal(valor),
                activo=True,
            )
            .on_conflict_do_nothing()
        )


def _cargar_usuarios(sesion: Session, contrasena_demo: str) -> int:
    existentes = set(sesion.scalars(select(UsuarioModelo.usuario)))
    nuevos = [u for u in USUARIOS if u.usuario not in existentes]
    if not nuevos:
        return 0
    hasher = HasherBcrypt()
    # Todos comparten la contraseña de demostración: se calcula el hash una sola vez.
    hash_demo = hasher.generar(contrasena_demo)
    for u in nuevos:
        sesion.execute(
            insert(UsuarioModelo)
            .values(
                id=id_fijo("usuario", u.usuario),
                usuario=u.usuario,
                nombre_completo=u.nombre_completo,
                hash_contrasena=hash_demo,
                rol=u.rol,
                organo_id=id_fijo("organo", u.organo),
                almacen_id=id_fijo("almacen", u.almacen) if u.almacen else None,
                activo=True,
            )
            .on_conflict_do_nothing()
        )
    return len(nuevos)


def _almacen_de(categoria: Categoria) -> str:
    return next(codigo for codigo, _, _, cat in ALMACENES if cat == categoria)


def _cargar_inventario(sesion: Session) -> None:
    """Stock inicial registrado como movimientos ENTRADA (invariante EQ-03)."""
    for codigo, _, categoria, _, _, cantidad in ITEMS:
        almacen = _almacen_de(categoria)
        almacen_id = id_fijo("almacen", almacen)
        item_id = id_fijo("item", codigo)
        sesion.execute(
            insert(MovimientoModelo)
            .values(
                id=id_fijo("movimiento-entrada", codigo),
                almacen_id=almacen_id,
                item_id=item_id,
                tipo=TipoMovimiento.ENTRADA,
                cantidad=cantidad,
                requerimiento_id=None,
                usuario_id=id_fijo("usuario", f"almacenero.{almacen.lower()}"),
            )
            .on_conflict_do_nothing()
        )
        sesion.execute(
            insert(StockModelo)
            .values(almacen_id=almacen_id, item_id=item_id, cantidad=cantidad)
            .on_conflict_do_nothing()
        )


def cargar(sesion: Session, contrasena_demo: str) -> dict[str, int]:
    """Carga los datos de prueba en la sesión dada (sin confirmar la transacción)."""
    _cargar_catalogo(sesion)
    usuarios_nuevos = _cargar_usuarios(sesion, contrasena_demo)
    _cargar_inventario(sesion)
    return {
        "organos": len(ORGANOS),
        "almacenes": len(ALMACENES),
        "items": len(ITEMS),
        "usuarios": len(USUARIOS),
        "usuarios_nuevos": usuarios_nuevos,
    }


def main() -> int:
    contrasena = obtener_configuracion().contrasena_demo
    if not contrasena:
        print("Falta CONTRASENA_DEMO en el entorno o en el archivo .env.", file=sys.stderr)
        return 1
    with obtener_fabrica_sesiones()() as sesion, sesion.begin():
        resumen = cargar(sesion, contrasena)
    print(
        "Seeds cargados: {organos} órganos, {almacenes} almacenes, {items} ítems, "
        "{usuarios} usuarios ({usuarios_nuevos} nuevos).".format(**resumen)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
