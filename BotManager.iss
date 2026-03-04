; ============================================================
;  BotManager — Inno Setup Script
;  Para compilar: abrí este .iss con Inno Setup Compiler
;  y hacé click en Build > Compile (o F9)
; ============================================================

#define AppName        "Discord Bot Manager"
#define AppVersion     "1.1"
#define AppPublisher   "V3ct0R924"
#define AppURL         "https://github.com/V3ct0R924/DiscordBotManager"
#define AppExeName     "BotManager.exe"
#define AppDescription "Manage all your Discord bots from one place"

[Setup]
; Identidad de la app
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases

; Comportamiento del instalador
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=no

; Requiere permisos de admin para instalar en Program Files
PrivilegesRequired=admin

; Archivos de salida
OutputDir=installer_output
OutputBaseFilename=BotManager_Setup_v{#AppVersion}

; Ícono del instalador
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExeName}

; Compresión
Compression=lzma2/ultra64
SolidCompression=yes

; Pantalla de bienvenida y colores (estilo dark para que matchee la app)
WizardStyle=modern

; Versioning para que Windows reconozca la app en "Agregar o quitar programas"
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppDescription}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

[Languages]
; Idiomas del instalador
Name: "english";    MessagesFile: "compiler:Default.isl"
Name: "spanish";    MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
; Opciones que el usuario puede elegir durante la instalación
Name: "desktopicon";    Description: "Create a &desktop shortcut";         GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon";    Description: "Launch on &Windows startup";          GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Ejecutable principal — compilado con PyInstaller --onefile
; Asegurate de que BotManager.exe esté en la misma carpeta que este .iss
Source: "BotManager.exe";   DestDir: "{app}";   Flags: ignoreversion

; Ícono
Source: "icon.ico";         DestDir: "{app}";   Flags: ignoreversion

; Archivos de datos (si los tenés en la misma carpeta)
; Descomentá las líneas que necesitás:
; Source: "languages.json"; DestDir: "{app}";   Flags: ignoreversion
; Source: "config.json";    DestDir: "{app}";   Flags: ignoreversion onlyifdoesntexist

[Icons]
; Acceso directo en el menú de inicio
Name: "{group}\{#AppName}";             Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall {#AppName}";   Filename: "{uninstallexe}"

; Acceso directo en el escritorio (solo si el usuario lo eligió)
Name: "{autodesktop}\{#AppName}";       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Registry]
; Arranque con Windows (solo si el usuario lo eligió)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#AppName}"; \
  ValueData: """{app}\{#AppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Ofrecer abrir la app al terminar la instalación
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Cerrar la app antes de desinstalar (si está corriendo)
Filename: "taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[Code]
// ── Detectar si la app ya está corriendo al iniciar el instalador ──────────
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Intentar cerrar instancias previas antes de instalar
  Exec('taskkill.exe', '/F /IM {#AppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
