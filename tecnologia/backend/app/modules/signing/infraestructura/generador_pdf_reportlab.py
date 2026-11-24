"""Implementa ``GeneradorPdf`` con ReportLab (ADR-011; research §8 de 002).

A4, formato de oficio militar sobrio y **sin escudos ni logos oficiales**: encabezado del SGA,
datos del requerimiento, tabla de ítems (en el acta: despachado, recibido y observación), un
recuadro por sello digital y, al pie de cada página, el código de verificación. El código va
también en los metadatos (``Keywords``), que ReportLab escribe sin comprimir: así la verificación
lo encuentra en los bytes sin leer el PDF con otra librería.
"""

from datetime import UTC, datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.modules.signing.dominio.documento import (
    ETIQUETAS_DECISION,
    ETIQUETAS_NIVEL,
    ETIQUETAS_ROL,
    DocumentoPdf,
    Referencia,
    SelloDocumento,
    TipoDocumento,
)
from app.modules.signing.dominio.tipos import DecisionFirma

# Hora de Perú (UTC−5, sin horario de verano).
HORA_PERU = timezone(timedelta(hours=-5), "PET")

OLIVA = colors.HexColor("#3d4a2a")
ARENA = colors.HexColor("#f3f0e6")
CARBON = colors.HexColor("#24272a")
ROJO = colors.HexColor("#8a2f2a")

LEYENDA = (
    "Documento firmado digitalmente con la clave del sistema SGA (SHA-256 + Ed25519, ADR-004). "
    "No reemplaza una firma con certificado acreditado. Verifique su autenticidad en el SGA, "
    "opción «Verificar PDF», con el código de verificación."
)


def _texto(valor: object) -> str:
    return escape("" if valor is None else str(valor))


def _ref(r: Referencia | None) -> str:
    return "—" if r is None else _texto(f"{r.codigo} · {r.nombre}")


def _fecha_hora(momento: datetime | None) -> tuple[str, str]:
    if momento is None:
        return "—", "—"
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=UTC)
    local = momento.astimezone(HORA_PERU)
    return local.strftime("%d/%m/%Y"), local.strftime("%H:%M") + " (hora de Perú)"


def huella_corta(huella: str) -> str:
    return huella if len(huella) <= 20 else f"{huella[:8]}…{huella[-8:]}"


class GeneradorPdfReportLab:
    def __init__(self) -> None:
        base = getSampleStyleSheet()
        self._normal = ParagraphStyle("normal", parent=base["Normal"], fontSize=9, leading=12)
        self._pequeno = ParagraphStyle("pequeno", parent=self._normal, fontSize=7.5, leading=10)
        self._titulo = ParagraphStyle(
            "titulo",
            parent=base["Title"],
            fontSize=13,
            leading=16,
            textColor=OLIVA,
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        self._subtitulo = ParagraphStyle(
            "subtitulo", parent=self._normal, alignment=TA_CENTER, textColor=CARBON
        )
        self._seccion = ParagraphStyle(
            "seccion", parent=base["Heading4"], fontSize=9.5, textColor=OLIVA, spaceBefore=8
        )

    # --- Partes del documento ---

    def _encabezado(self, d: DocumentoPdf) -> list:
        titulo = "ACTA DE RECEPCIÓN" if d.tipo is TipoDocumento.ACTA else "REQUERIMIENTO"
        fecha, _ = _fecha_hora(d.fecha)
        filas = [
            ["Número", _texto(d.numero), "Fecha", fecha],
            ["Unidad solicitante", _ref(d.unidad), "Gran Unidad", _ref(d.gran_unidad)],
            ["Almacén", _ref(d.almacen), "", ""],
        ]
        tabla = Table(
            [
                [
                    Paragraph(f"<b>{c}</b>" if i % 2 == 0 else c, self._normal)
                    for i, c in enumerate(f)
                ]
                for f in filas
            ],
            colWidths=[32 * mm, 58 * mm, 26 * mm, 58 * mm],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, OLIVA),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), ARENA),
                    ("BACKGROUND", (2, 0), (2, -1), ARENA),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return [
            Paragraph("SGA · SISTEMA DE GESTIÓN DE ALMACÉN CON FIRMA DIGITAL", self._subtitulo),
            Paragraph(titulo, self._titulo),
            Spacer(1, 3 * mm),
            tabla,
        ]

    def _items(self, d: DocumentoPdf) -> list:
        es_acta = d.tipo is TipoDocumento.ACTA
        if es_acta:
            cabecera = [
                "Código",
                "Descripción",
                "U. M.",
                "Solicitado",
                "Despachado",
                "Recibido",
                "Observación",
            ]
            anchos = [20, 48, 14, 18, 20, 18, 36]
        else:
            cabecera = ["Código", "Descripción", "U. M.", "Categoría", "Cantidad"]
            anchos = [24, 74, 18, 38, 20]
        filas = [[Paragraph(f"<b>{c}</b>", self._pequeno) for c in cabecera]]
        for li in d.lineas:
            if es_acta:
                valores = [
                    li.codigo,
                    li.descripcion,
                    li.unidad_medida,
                    li.cantidad_solicitada,
                    li.cantidad_despachada,
                    li.cantidad_recibida,
                    li.observacion or "—",
                ]
            else:
                valores = [
                    li.codigo,
                    li.descripcion,
                    li.unidad_medida,
                    li.categoria,
                    li.cantidad_solicitada,
                ]
            filas.append([Paragraph(_texto(v), self._pequeno) for v in valores])
        tabla = Table(filas, colWidths=[a * mm for a in anchos], repeatRows=1)
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, OLIVA),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), ARENA),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        partes: list = [Paragraph("ÍTEMS", self._seccion), tabla]
        if es_acta:
            texto = (
                "Se registraron diferencias entre lo despachado y lo recibido."
                if d.tiene_diferencias
                else "Lo recibido coincide con lo despachado."
            )
            partes += [Spacer(1, 2 * mm), Paragraph(texto, self._normal)]
        return partes

    def _sello(self, s: SelloDocumento) -> Table:
        fecha, hora = _fecha_hora(s.firmado_en)
        color = ROJO if s.decision is DecisionFirma.RECHAZAR else OLIVA
        lineas = [
            f"<b>{_texto(ETIQUETAS_NIVEL.get(s.nivel, s.nivel))}</b> · "
            f"<font color='{color.hexval()}'><b>{_texto(ETIQUETAS_DECISION.get(s.decision))}"
            f"</b></font>",
            f"{_texto(s.firmante)} — {_texto(ETIQUETAS_ROL.get(s.rol, s.rol))}",
            f"Órgano: {_ref(s.organo)}",
            f"Fecha: {fecha} · Hora: {hora}",
            f"Método: {_texto(s.metodo)} · Huella SHA-256: {_texto(huella_corta(s.huella_sha256))}",
        ]
        if s.motivo:
            lineas.append(f"Motivo: {_texto(s.motivo)}")
        tabla = Table([[Paragraph("<br/>".join(lineas), self._pequeno)]], colWidths=[174 * mm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return tabla

    def _firmas(self, d: DocumentoPdf, huella_contenido: str) -> list:
        partes: list = [Paragraph("FIRMAS (SELLOS DIGITALES)", self._seccion)]
        if not d.sellos:
            partes.append(Paragraph("Todavía no hay firmas.", self._normal))
        for sello in d.sellos:
            partes += [KeepTogether([self._sello(sello)]), Spacer(1, 2 * mm)]
        partes += [
            Spacer(1, 3 * mm),
            Paragraph(
                f"<b>Huella SHA-256 del documento:</b> {_texto(huella_contenido)}", self._pequeno
            ),
            Paragraph(LEYENDA, self._pequeno),
        ]
        return partes

    # --- Puerto ---

    def generar(self, documento: DocumentoPdf, codigo: str, huella_contenido: str) -> bytes:
        salida = BytesIO()
        plantilla = SimpleDocTemplate(
            salida,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=20 * mm,
            title=f"{documento.tipo.value} {documento.numero}",
            author="SGA - Proyecto académico IS488 UNSCH",
            subject=f"Código de verificación {codigo}",
            keywords=f"SGA-VERIFICACION {codigo}",
            creator="SGA",
        )

        def pie(lienzo, doc) -> None:
            lienzo.saveState()
            lienzo.setFont("Helvetica", 7.5)
            lienzo.setFillColor(CARBON)
            lienzo.drawString(
                18 * mm, 10 * mm, f"Código de verificación: {codigo} · {documento.numero}"
            )
            lienzo.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {doc.page}")
            lienzo.restoreState()

        historia = (
            self._encabezado(documento)
            + self._items(documento)
            + self._firmas(documento, huella_contenido)
        )
        plantilla.build(historia, onFirstPage=pie, onLaterPages=pie)
        return salida.getvalue()
