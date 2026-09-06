/**
 * Разбор хоткеев триажа.
 *
 * Две проблемы, которые здесь закрыты:
 * 1. Раскладка. Сравнение только по event.key ломало J/K/A/R/E на русской
 *    раскладке: физическая клавиша R даёт key === "к". Сверяем и key, и
 *    event.code.
 * 2. Модификаторы. Ctrl+R (перезагрузка) и Cmd+A (выделить всё) попадали в
 *    обработчик и записывались как решение эксперта по замечанию. Любой
 *    Ctrl/Cmd/Alt теперь не хоткей триажа.
 *
 * Функции чистые: их проверяет triage-hotkeys.test.ts.
 */

export type TriageHotkey =
	| "help"
	| "close"
	| "next"
	| "prev"
	| "accept"
	| "reject"
	| "edit";

type HotkeyEvent = {
	key: string;
	code?: string;
	shiftKey?: boolean;
	ctrlKey?: boolean;
	metaKey?: boolean;
	altKey?: boolean;
};

/** Совпадение по латинской букве или по физической клавише. */
function matches(event: HotkeyEvent, letter: string, code: string): boolean {
	if (event.key.length === 1 && event.key.toLowerCase() === letter) {
		return true;
	}
	return Boolean(event.code) && event.code === code;
}

/** Поле ввода: там хоткеи не работают, иначе эксперт не сможет набрать текст. */
export function isTextEntryTarget(target: EventTarget | null): boolean {
	const element = target as
		| (Partial<HTMLElement> & { tagName?: string })
		| null;
	const tag = element?.tagName;
	if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
		return true;
	}
	return element?.isContentEditable === true;
}

export function resolveTriageHotkey(event: HotkeyEvent): TriageHotkey | null {
	// Esc закрывает справку в любом случае — это выход, а не решение.
	if (event.key === "Escape") {
		return "close";
	}
	if (event.ctrlKey === true || event.metaKey === true || event.altKey === true) {
		return null;
	}
	if (
		event.key === "?" ||
		(event.shiftKey === true && (event.key === "/" || event.code === "Slash"))
	) {
		return "help";
	}
	if (event.key === "ArrowDown" || matches(event, "j", "KeyJ")) {
		return "next";
	}
	if (event.key === "ArrowUp" || matches(event, "k", "KeyK")) {
		return "prev";
	}
	if (matches(event, "a", "KeyA")) {
		return "accept";
	}
	if (matches(event, "r", "KeyR")) {
		return "reject";
	}
	if (matches(event, "e", "KeyE")) {
		return "edit";
	}
	return null;
}
