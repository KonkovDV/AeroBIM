/** Pack kind from filename. Not a product capability matrix. */

export type PackKind =
  | "ifc"
  | "ids"
  | "pdf"
  | "office"
  | "dxf"
  | "dwg"
  | "rvt"
  | "nwd"
  | "lir"
  | "zip"
  | "other";

export type PackKindVerdict = "upload_ok" | "fail_closed";

const FAIL_CLOSED: ReadonlySet<PackKind> = new Set(["dwg", "rvt", "nwd", "lir"]);

export function detectPackKind(filename: string): PackKind {
  const lower = filename.trim().toLowerCase();
  const dot = lower.lastIndexOf(".");
  const ext = dot >= 0 ? lower.slice(dot) : "";
  if (ext === ".ifc" || ext === ".ifczip") return "ifc";
  if (ext === ".ids") return "ids";
  if (ext === ".pdf") return "pdf";
  if (ext === ".xlsx" || ext === ".xlsm" || ext === ".docx" || ext === ".doc") return "office";
  if (ext === ".dxf") return "dxf";
  if (ext === ".dwg") return "dwg";
  if (ext === ".rvt" || ext === ".rte") return "rvt";
  if (ext === ".nwd" || ext === ".nwc") return "nwd";
  if (ext === ".lir" || ext === ".spr") return "lir";
  if (ext === ".zip") return "zip";
  return "other";
}

export function packKindVerdict(kind: PackKind): PackKindVerdict {
  return FAIL_CLOSED.has(kind) ? "fail_closed" : "upload_ok";
}

export function packKindHonesty(kind: PackKind): string {
  switch (kind) {
    case "dwg":
      return "Закрытый .dwg на MVP — fail-closed. Та же отметка, что у векторного PDF/DXF. Не тихий skip.";
    case "rvt":
      return "Нативный RVT не продукт приёма. Выгрузите IFC из САПР. Fail-closed.";
    case "nwd":
      return "Нативный NWD не продукт приёма. Федерация — IFC. Stock Navisworks не пишет IFC.";
    case "lir":
      return "Нативный .lir не разбираем. Загрузите читаемую записку (PDF/Excel).";
    case "zip":
      return "ZIP смотрит сервер. Autodesk natives внутри остаются fail-closed.";
    case "ids":
      return "Набор правил IDS 1.0. Запрошенный набор, который не грузится, — fail-closed.";
    case "ifc":
      return "IFC — формат модели на общем шлюзе.";
    case "pdf":
      return "PDF/A и векторный PDF — обмен чертежами и записками.";
    case "office":
      return "Office сравнивает заявленные поля; MATCH не есть верность расчёта.";
    case "dxf":
      return "DXF — опциональный приём, не чтение закрытого .dwg.";
    default:
      return "Неизвестный тип. Сервер проверяет magic bytes. 200 на другом файле не значит успех.";
  }
}
