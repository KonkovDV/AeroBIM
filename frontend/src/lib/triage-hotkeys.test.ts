import { describe, expect, it } from "vitest";

import { isTextEntryTarget, resolveTriageHotkey } from "./triage-hotkeys";

type Init = {
	key: string;
	code?: string;
	shiftKey?: boolean;
	ctrlKey?: boolean;
	metaKey?: boolean;
	altKey?: boolean;
};

function press(init: Init) {
	return {
		key: init.key,
		code: init.code ?? "",
		shiftKey: init.shiftKey ?? false,
		ctrlKey: init.ctrlKey ?? false,
		metaKey: init.metaKey ?? false,
		altKey: init.altKey ?? false,
	};
}

describe("resolveTriageHotkey", () => {
	it("читает латинскую раскладку", () => {
		expect(resolveTriageHotkey(press({ key: "j" }))).toBe("next");
		expect(resolveTriageHotkey(press({ key: "k" }))).toBe("prev");
		expect(resolveTriageHotkey(press({ key: "a" }))).toBe("accept");
		expect(resolveTriageHotkey(press({ key: "r" }))).toBe("reject");
		expect(resolveTriageHotkey(press({ key: "e" }))).toBe("edit");
	});

	it("читает верхний регистр", () => {
		expect(resolveTriageHotkey(press({ key: "A", shiftKey: true }))).toBe(
			"accept",
		);
	});

	it("читает Home End и страницу", () => {
		expect(resolveTriageHotkey(press({ key: "Home" }))).toBe("first");
		expect(resolveTriageHotkey(press({ key: "End" }))).toBe("last");
		expect(resolveTriageHotkey(press({ key: "PageDown" }))).toBe("pageNext");
		expect(resolveTriageHotkey(press({ key: "PageUp" }))).toBe("pagePrev");
	});

	it("работает на русской раскладке по физической клавише", () => {
		expect(resolveTriageHotkey(press({ key: "о", code: "KeyJ" }))).toBe("next");
		expect(resolveTriageHotkey(press({ key: "л", code: "KeyK" }))).toBe("prev");
		expect(resolveTriageHotkey(press({ key: "ф", code: "KeyA" }))).toBe(
			"accept",
		);
		expect(resolveTriageHotkey(press({ key: "к", code: "KeyR" }))).toBe(
			"reject",
		);
		expect(resolveTriageHotkey(press({ key: "у", code: "KeyE" }))).toBe("edit");
	});

	it("не считает решением системные сочетания", () => {
		expect(
			resolveTriageHotkey(press({ key: "r", code: "KeyR", ctrlKey: true })),
		).toBeNull();
		expect(
			resolveTriageHotkey(press({ key: "a", code: "KeyA", metaKey: true })),
		).toBeNull();
		expect(
			resolveTriageHotkey(press({ key: "e", code: "KeyE", altKey: true })),
		).toBeNull();
	});

	it("закрывает справку по Esc даже с модификатором", () => {
		expect(resolveTriageHotkey(press({ key: "Escape" }))).toBe("close");
		expect(resolveTriageHotkey(press({ key: "Escape", ctrlKey: true }))).toBe(
			"close",
		);
	});

	it("открывает справку в обеих раскладках", () => {
		expect(resolveTriageHotkey(press({ key: "?" }))).toBe("help");
		expect(
			resolveTriageHotkey(press({ key: "/", code: "Slash", shiftKey: true })),
		).toBe("help");
		expect(
			resolveTriageHotkey(press({ key: ",", code: "Slash", shiftKey: true })),
		).toBe("help");
	});

	it("не путает одиночный слеш со справкой", () => {
		expect(resolveTriageHotkey(press({ key: "/", code: "Slash" }))).toBeNull();
	});

	it("игнорирует посторонние клавиши", () => {
		expect(resolveTriageHotkey(press({ key: "z", code: "KeyZ" }))).toBeNull();
		expect(resolveTriageHotkey(press({ key: "Tab" }))).toBeNull();
	});
});

describe("isTextEntryTarget", () => {
	it("узнаёт поля ввода", () => {
		expect(isTextEntryTarget({ tagName: "INPUT" } as unknown as EventTarget)).toBe(
			true,
		);
		expect(
			isTextEntryTarget({ tagName: "TEXTAREA" } as unknown as EventTarget),
		).toBe(true);
		expect(
			isTextEntryTarget({ tagName: "SELECT" } as unknown as EventTarget),
		).toBe(true);
		expect(
			isTextEntryTarget({
				tagName: "DIV",
				isContentEditable: true,
			} as unknown as EventTarget),
		).toBe(true);
	});

	it("пропускает обычные элементы и пустую цель", () => {
		expect(isTextEntryTarget({ tagName: "DIV" } as unknown as EventTarget)).toBe(
			false,
		);
		expect(isTextEntryTarget(null)).toBe(false);
	});
});
