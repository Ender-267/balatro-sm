from ppadb.client import Client as AdbClient
from pathlib import Path
import platform
from colorama import Fore, Back, Style, init

cliente = AdbClient()
dispositivo = cliente.devices()[0]


def buscar_paths_pc() -> dict:
    sistema_op = platform.system()
    paths_a_buscar: list[Path]
    match sistema_op:
        case "Windows":
            paths_a_buscar = [Path.home() / "AppData" / "Roaming" / "Balatro"]
        case "Linux":
            paths_a_buscar = [Path("~/Juegos/Balatro/Files").expanduser()]
        case _:
            paths_a_buscar = []

    for path in paths_a_buscar:
        try:
            return extraer_perfiles_pc(path)
        except FileNotFoundError:
            continue

    raise FileNotFoundError("No se encontro la carpeta del juego")


def extraer_perfiles_pc(path: Path) -> dict:
    se_encontro_un_perfil: bool = False
    perfiles: dict[str, dict] = {}
    for id_perfil in ("1", "2", "3"):
        perfil: dict = {}
        for archivo in ("meta", "profile"):
            path_archivo = path / id_perfil / f"{archivo}.jkr"
            if path_archivo.is_file():
                perfil[archivo] = path_archivo
        if ("meta" in perfil) and ("profile" in perfil):
            se_encontro_un_perfil = True
            perfiles[id_perfil] = perfil
    if se_encontro_un_perfil:
        return perfiles
    else:
        raise FileNotFoundError("No se encontro un perfil en el path determinado")


def existe_archivo_android(path: str) -> bool:
    comando = f'su -c "[ -f \\"{path}\\" ] && echo existe || echo no"'
    salida = dispositivo.shell(comando).strip().lower()
    return "existe" in salida


def buscar_perfiles_android() -> dict:
    path = Path("/data/data/com.playstack.balatro.android/files")
    se_encontro_un_perfil: bool = False
    perfiles: dict[str, dict] = {}
    for id_perfil in ("1", "2", "3"):
        perfil: dict = {}
        for archivo in ("meta", "profile"):
            path_archivo = (path / f"{id_perfil}-{archivo}.jkr").as_posix()
            if existe_archivo_android(path_archivo):
                perfil[archivo] = Path(path_archivo)
        if ("meta" in perfil) and ("profile" in perfil):
            se_encontro_un_perfil = True
            perfiles[id_perfil] = perfil
    if se_encontro_un_perfil:
        return perfiles
    else:
        raise FileNotFoundError("No se encontro un perfil en el path determinado")


def adb_pull_root(path_android: str, path_pc: str):
    RUTA_TEMP = "/sdcard"
    nombre_archivo: str = path_android.split("/")[-1]
    ruta_completa = f"{RUTA_TEMP}/{nombre_archivo}"
    dispositivo.shell(f"su -c 'cp {path_android} {ruta_completa}'")
    dispositivo.shell(f"su -c 'chmod 644 {ruta_completa}'")
    try:
        dispositivo.pull(ruta_completa, path_pc)
    except:
        pass
    dispositivo.shell(f"rm {ruta_completa}")


def adb_push_root(path_pc: str, path_android: str):
    RUTA_TEMP = "/sdcard"
    nombre_archivo: str = path_android.split("/")[-1]
    ruta_completa = f"{RUTA_TEMP}/{nombre_archivo}"
    dispositivo.push(path_pc, ruta_completa)
    dispositivo.shell(f"su -c 'cp {ruta_completa} {path_android}'")
    dispositivo.shell(f"su -c 'chmod 644 {path_android}'")
    dispositivo.shell(f"rm {ruta_completa}")


def main() -> None:
    init(autoreset=True)
    print(
        f"{Fore.YELLOW}Sistema operativo: {Fore.WHITE}{platform.system()}",
        end="\n\n",
    )

    try:
        perfiles_pc = buscar_paths_pc()
    except FileNotFoundError:
        print(f"{Fore.LIGHTRED_EX}No se encontraron perfiles de pc")
        return cexit()

    if list(perfiles_pc.keys()):
        print(f"{Fore.YELLOW}Se encontraron perfiles en pc: ")
        for perfil in sorted(perfiles_pc.keys()):
            print(f"\t{Fore.WHITE}{perfil} ", end="")
        print("")
    try:
        perfiles_android = buscar_perfiles_android()
    except FileNotFoundError:
        print(f"{Fore.LIGHTRED_EX}No se encontraron perfiles de android")
        return cexit()

    if list(perfiles_android.keys()):
        print(f"{Fore.YELLOW}Se encontraron perfiles en android: ")
        for perfil in sorted(perfiles_android.keys()):
            print(f"\t{Fore.WHITE}{perfil} ", end="")
        print("")
    MaPC = 1
    PCaM = 2

    while True:
        seleccion = input(
            f"{Fore.GREEN}Selecciona la dirección de la transferencia:\n"
            f"{Fore.LIGHTGREEN_EX}1) De móvil a PC\n2) De PC a móvil\n{Style.RESET_ALL}"
        )

        if seleccion in ("1", "2"):
            break
        print(f"{Fore.LIGHTRED_EX}La selección no es válida")

    match seleccion:
        case "1":
            modo = MaPC
        case "2":
            modo = PCaM
        case _:
            modo = None

    while True:
        seleccion = input(
            f"{Fore.GREEN}Selecciona el perfil del pc a mover:\n{Style.RESET_ALL}"
        )
        if seleccion in list(perfiles_pc.keys()):
            break
        print(f"{Fore.LIGHTRED_EX}La selección no es válida")

    id_perfil_pc = seleccion

    while True:
        seleccion = input(
            f"{Fore.GREEN}Selecciona el perfil del movil a mover:\n{Style.RESET_ALL}"
        )
        if seleccion in list(perfiles_android.keys()):
            break
        print(f"{Fore.LIGHTRED_EX}La selección no es válida")

    id_perfil_android = seleccion

    if modo == MaPC:
        for archivo in ("meta", "profile"):
            adb_pull_root(
                perfiles_android[id_perfil_android][archivo].as_posix(),
                perfiles_pc[id_perfil_pc][archivo].as_posix(),
            )
    elif modo == PCaM:
        for archivo in ("meta", "profile"):
            adb_push_root(
                perfiles_pc[id_perfil_pc][archivo].as_posix(),
                perfiles_android[id_perfil_android][archivo].as_posix(),
            )
    else:
        raise ValueError("Modo no valido")

    return cexit()


def cexit():
    print(Style.RESET_ALL)


main()
