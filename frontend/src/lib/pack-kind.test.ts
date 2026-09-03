import { describe, expect, it } from "vitest";
import { detectPackKind, packKindHonesty, packKindVerdict } from "./pack-kind";

describe("pack-kind", () => {
  it("fail-closes native Autodesk and LIRA before upload", () => {
    expect(detectPackKind("model.rvt")).toBe("rvt");
    expect(packKindVerdict("rvt")).toBe("fail_closed");
    expect(packKindHonesty("rvt")).toMatch(/жёсткий отказ/i);
    expect(packKindHonesty("dwg")).toMatch(/не тихий пропуск/i);
    expect(packKindHonesty("nwd")).toMatch(/не пишет IFC/i);
    expect(packKindVerdict("ifc")).toBe("upload_ok");
    expect(packKindHonesty("ifc")).not.toMatch(/DWG-ready/);
  });

  it("treats .ifczip as the IFC slot kind", () => {
    expect(detectPackKind("model.ifczip")).toBe("ifc");
    expect(detectPackKind("MODEL.IFCZIP")).toBe("ifc");
    expect(packKindVerdict("ifc")).toBe("upload_ok");
  });
});
