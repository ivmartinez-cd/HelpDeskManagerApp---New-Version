# pyside_ui/controllers/contadores_controller.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence, Callable, List
import re

from PySide6 import QtCore, QtWidgets

from pyside_ui.core.Db3ToCsv import procesar_db_a_csv
from pyside_ui.core.CsvEn0 import filtrar_falta_contador_csv
from pyside_ui.ui.csven0_params_dialog import ask_csven0_params

from pyside_ui.core.Clientes_suma import convertir_xls_a_csv_arcos_headless
from pyside_ui.ui.suma_fija_params_dialog import ask_suma_fija_params

# ✅ Estimador manual (ventana no-modal always-on-top)
from pyside_ui.ui.estimador_manual_dialog import EstimadorManualDialog

from pyside_ui.ui.ftp_client_picker import FtpClientPickerDialog
from pyside_ui.ui.db3_csv_params_dialog import ask_db3_csv_params
from pyside_ui.core.Autoestim import ejecutar_generacion_dos_csv
from pyside_ui.ui.autoestimacion_dialog import AutoestimacionDialog



UncheckCb = Callable[[], None]
NotifyCb = Callable[[str, str, str, int], None]


class ContadoresController(QtCore.QObject):
    def __init__(
        self,
        parent,
        *,
        status_cb: Callable[[str], None],
        ftp_service,
        uncheck_ftp_cb: Optional[UncheckCb] = None,
        notify_cb: Optional[NotifyCb] = None,
    ):
        super().__init__(parent)
        self._parent = parent
        self._status_cb = status_cb
        self._ftp = ftp_service
        self._uncheck_ftp_cb = uncheck_ftp_cb
        self._notify_cb = notify_cb

        self._last_nombre_base: str = ""
        self._last_carpeta_salida: str = ""

        self._last_en0_csv_in: str = ""
        self._last_en0_out_dir: str = ""
        self._last_en0_cliente: str = ""

        self._last_suma_files: List[str] = []
        self._last_suma_out_dir: str = ""
        self._last_suma_fecha: str = ""
        self._last_suma_hojas: int = 0
        self._last_auto_csv_in: str = ""
        self._last_auto_fecha: str = ""


        # ✅ mantener referencia (no se destruye)
        self._estimador_manual_win: Optional[EstimadorManualDialog] = None

    def _notify(self, level: str, title: str, message: str, timeout_ms: int = 3000) -> None:
        if self._notify_cb:
            self._notify_cb(level, title, message, timeout_ms)

    def _get_theme(self) -> dict:
        try:
            w = self._parent.window()
            t = getattr(w, "theme", None)
            return t if isinstance(t, dict) else {}
        except Exception:
            return {}

    # =========================
    # ✅ Estimador manual
    # =========================
    def abrir_estimador_manual(self) -> None:
        # si ya está abierto, traerlo al frente
        if self._estimador_manual_win is not None and self._estimador_manual_win.isVisible():
            self._estimador_manual_win.raise_()
            self._estimador_manual_win.activateWindow()
            return

        dlg = EstimadorManualDialog(None, theme=self._get_theme())  # 👈 sin parent
        dlg.position_near(self._parent)

        # limpiar referencia al cerrar
        dlg.destroyed.connect(lambda _=None: self._clear_estimador_manual_ref())

        self._estimador_manual_win = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _clear_estimador_manual_ref(self) -> None:
        self._estimador_manual_win = None

    # --------- resto igual ---------

    def _pick_ftp_client(self, clients: list[str]) -> Optional[str]:
        dlg = FtpClientPickerDialog(self._parent, clients=clients, theme=self._get_theme())
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return getattr(dlg, "selected_client", None)
        return None

    def _derive_autocsv_name_from_dest_dir(self, dest_dir: Path) -> str:
        cliente = ""
        try:
            cliente = dest_dir.parents[1].name.strip()
        except Exception:
            cliente = ""
        if not cliente:
            cliente = "CLIENTE"
        cliente = re.sub(r"[^\w\-]+", "", cliente, flags=re.UNICODE)
        return cliente or "CLIENTE"

    def procesar_db3_a_csv(self, use_ftp: bool) -> bool:
        if use_ftp:
            return self._run_ftp_flow_steps()

        archivos = self._ask_manual_files()
        if not archivos:
            return False

        db3_dir = None
        try:
            db3_dir = Path(archivos[0]).parent
        except Exception:
            db3_dir = None

        self._run_db3_to_csv_flow(list(archivos), db3_download_dir=db3_dir)
        return True

    def _run_db3_to_csv_flow(
        self,
        archivos: List[Path],
        *,
        db3_download_dir: Optional[Path] = None,
    ) -> bool:
        self._status_cb("")
        today = datetime.now().strftime("%d/%m/%Y")

        suggested_nombre_base = self._last_nombre_base
        suggested_carpeta = self._last_carpeta_salida

        if db3_download_dir is not None:
            suggested_nombre_base = self._derive_autocsv_name_from_dest_dir(db3_download_dir)
            suggested_carpeta = str(db3_download_dir)

        params = ask_db3_csv_params(
            self._parent,
            default_fecha=today,
            default_nombre_base=suggested_nombre_base,
            default_carpeta=suggested_carpeta,
            theme=self._get_theme(),
        )
        if not params:
            return False

        self._last_nombre_base = params.nombre_base_salida
        self._last_carpeta_salida = params.carpeta_salida or ""

        try:
            procesar_db_a_csv(
                archivos_db=[str(p) for p in archivos],
                fecha_maxima=params.fecha_maxima,
                nombre_base_salida=params.nombre_base_salida,
                carpeta_salida=params.carpeta_salida,
            )
            self._status_cb("")
            self._notify("success", "Contadores", "CSV generado correctamente.", 4000)
            return True
        except Exception as e:
            self._status_cb("")
            self._notify("error", "Contadores", f"Error al generar CSV:\n\n{e}", 7000)
            return False

    def estimacion_en0_contadores_por_proceso(self) -> bool:
        self._status_cb("")
        params = ask_csven0_params(
            self._parent,
            default_in_path=self._last_en0_csv_in or None,
            default_out_dir=self._last_en0_out_dir or None,
            theme=self._get_theme(),
        )
        if not params:
            return False

        self._last_en0_csv_in = params.archivo_csv_entrada
        self._last_en0_out_dir = params.carpeta_salida or ""
        self._last_en0_cliente = params.nombre_cliente

        try:
            out_path = filtrar_falta_contador_csv(
                archivo_csv_entrada=params.archivo_csv_entrada,
                fecha_nueva=params.fecha_nueva,
                nombre_cliente=params.nombre_cliente,
                carpeta_salida=params.carpeta_salida,
                delimiter_entrada=params.delimiter_entrada,
            )
            out_name = Path(out_path).name
            self._status_cb("")
            self._notify("success", "Estimación en 0", f"CSV generado: {out_name}", 5000)
            return True
        except Exception as e:
            self._status_cb("")
            self._notify("error", "Estimación en 0", f"No se pudo generar el CSV:\n\n{e}", 8000)
            return False

    def estimacion_suma_fija(self) -> bool:
        self._status_cb("")
        today = datetime.now().strftime("%d/%m/%Y")
        default_fecha = self._last_suma_fecha or today

        params = ask_suma_fija_params(
            self._parent,
            default_files=self._last_suma_files or None,
            default_out_dir=self._last_suma_out_dir or None,
            default_fecha=default_fecha,
            default_hojas=int(self._last_suma_hojas or 0),
            theme=self._get_theme(),
        )
        if not params:
            return False

        self._last_suma_files = list(params.archivos_xls)
        self._last_suma_out_dir = params.carpeta_salida
        self._last_suma_fecha = params.fecha
        self._last_suma_hojas = int(params.hojas_a_sumar)

        try:
            rutas = convertir_xls_a_csv_arcos_headless(
                archivos_xls=list(params.archivos_xls),
                carpeta_salida=params.carpeta_salida,
                fecha_usuario=params.fecha,
                hojas_a_sumar=int(params.hojas_a_sumar),
            )
            self._status_cb("")
            if len(rutas) == 1:
                self._notify("success", "Suma fija", f"CSV generado: {Path(rutas[0]).name}", 5000)
            else:
                self._notify("success", "Suma fija", f"CSVs generados: {len(rutas)}", 5000)
            return True
        except Exception as e:
            self._status_cb("")
            self._notify("error", "Suma fija", f"No se pudo generar el/los CSV:\n\n{e}", 8000)
            return False

    def _run_ftp_flow_steps(self) -> bool:
        cfg_map, cfg_path = self._ftp.load_cfg()
        if not cfg_map or not cfg_path:
            self._status_cb("")
            self._notify("warning", "FTP", "No hay clientes FTP configurados.", 5000)
            if self._uncheck_ftp_cb:
                self._uncheck_ftp_cb()
            return False

        clientes = self._ftp.list_clients(cfg_path)
        if not clientes:
            self._status_cb("")
            self._notify("warning", "FTP", "No hay clientes FTP configurados.", 5000)
            if self._uncheck_ftp_cb:
                self._uncheck_ftp_cb()
            return False

        cliente = self._pick_ftp_client(clientes)
        if not cliente:
            return False

        dest_dir_str = QtWidgets.QFileDialog.getExistingDirectory(self._parent, "Elegir carpeta destino")
        if not dest_dir_str:
            return False

        dest_dir = Path(dest_dir_str)
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._notify("error", "FTP", f"No se pudo usar la carpeta destino:\n\n{e}", 6000)
            if self._uncheck_ftp_cb:
                self._uncheck_ftp_cb()
            self._status_cb("")
            return False

        self._notify("info", "FTP", "Conectando con cliente FTP…", 2500)
        self._status_cb("")
        QtCore.QTimer.singleShot(0, lambda: self._ftp_step_check_exists(cfg_map=cfg_map, cliente=cliente, dest_dir=dest_dir))
        return True

    def _ftp_step_check_exists(self, *, cfg_map, cliente: str, dest_dir: Path) -> None:
        self._notify("info", "FTP", "Verificando existencia del archivo DB3…", 3000)
        self._status_cb("")
        QtCore.QTimer.singleShot(0, lambda: self._ftp_step_download(cfg_map=cfg_map, cliente=cliente, dest_dir=dest_dir))

    def _ftp_step_download(self, *, cfg_map, cliente: str, dest_dir: Path) -> None:
        self._notify("info", "FTP", "Descargando archivo DB3…", 3000)
        self._status_cb("")
        try:
            res = self._ftp.download_many_db3(cfg_map=cfg_map, cliente=cliente, dest_dir=str(dest_dir), status_cb=None)
            local_path = Path(res.local_path)
            self._status_cb("")
            self._notify("success", "FTP", f"Descarga exitosa: {local_path.name}", 3500)
            QtCore.QTimer.singleShot(3500, lambda: self._run_db3_to_csv_flow([local_path], db3_download_dir=local_path.parent))
        except FileNotFoundError:
            self._status_cb("")
            self._notify("warning", "FTP", "No hay archivos DB3 disponibles.", 3500)
            if self._uncheck_ftp_cb:
                self._uncheck_ftp_cb()
        except Exception as e:
            self._status_cb("")
            self._notify("error", "FTP", f"No se pudo descargar:\n\n{e}", 4500)
            if self._uncheck_ftp_cb:
                self._uncheck_ftp_cb()

    def _ask_manual_files(self) -> Optional[Sequence[Path]]:
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self._parent, "Seleccionar archivos DB3", "", "Todos los archivos (*)")
        if not files:
            return None
        return [Path(f) for f in files]
    
    # =========================
    # ✅ Autoestimación
    # =========================
    def abrir_autoestimacion(self) -> None:
        self._status_cb("")

        today = datetime.now().strftime("%d/%m/%Y")

        dlg = AutoestimacionDialog(
            self._parent,
            theme=self._get_theme(),
            default_csv=self._last_auto_csv_in or None,
            default_fecha=self._last_auto_fecha or today,
        )

        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        csv_path, fecha = dlg.get_data()

        self._last_auto_csv_in = csv_path
        self._last_auto_fecha = fecha

        try:
            out1, out2 = ejecutar_generacion_dos_csv(
                ruta_csv_detalle=csv_path,
                fecha_nueva=fecha,
            )

            self._status_cb("")
            self._notify(
                "success",
                "Autoestimación",
                f"Archivos generados:\n{Path(out1).name}\n{Path(out2).name}",
                6000,
            )

        except Exception as e:
            self._status_cb("")
            self._notify(
                "error",
                "Autoestimación",
                f"No se pudo generar la autoestimación:\n\n{e}",
                8000,
            )



