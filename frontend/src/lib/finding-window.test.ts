import { describe, expect, it } from "vitest";

import {
	FINDING_GROUP_HEADER_HEIGHT,
	buildFindingListItems,
	buildItemOffsets,
	buildVisibleRuns,
	computeFindingWindow,
	computeScrollTopToRevealItem,
	findItemIndexForIssue,
} from "./finding-window";
import type { IndexedIssue } from "./issue-triage";

const ROW = 100;

function row(index: number): IndexedIssue {
	return { index, issue: {} as IndexedIssue["issue"] };
}

function group(key: string, indexes: number[]) {
	return { key, rows: indexes.map(row) };
}

describe("buildFindingListItems", () => {
	it("без группировки отдаёт только строки", () => {
		const items = buildFindingListItems([group("", [0, 1, 2])], false);
		expect(items).toHaveLength(3);
		expect(items.every((item) => item.kind === "row")).toBe(true);
	});

	it("с группировкой ставит заголовок перед строками группы", () => {
		const items = buildFindingListItems(
			[group("LB-011", [0, 1]), group("LB-012", [2])],
			true,
		);
		expect(items.map((item) => item.kind)).toEqual([
			"header",
			"row",
			"row",
			"header",
			"row",
		]);
		expect(items[0]).toMatchObject({ groupKey: "LB-011", count: 2 });
		expect(items[3]).toMatchObject({ groupKey: "LB-012", count: 1 });
	});
});

describe("buildItemOffsets", () => {
	it("учитывает разную высоту заголовка и строки", () => {
		const items = buildFindingListItems([group("A", [0, 1])], true);
		const offsets = buildItemOffsets(items, ROW);
		expect(offsets).toEqual([
			0,
			FINDING_GROUP_HEADER_HEIGHT,
			FINDING_GROUP_HEADER_HEIGHT + ROW,
			FINDING_GROUP_HEADER_HEIGHT + ROW * 2,
		]);
	});

	it("не допускает нулевую высоту строки", () => {
		const items = buildFindingListItems([group("", [0, 1])], false);
		expect(buildItemOffsets(items, 0)).toEqual([0, 1, 2]);
	});
});

describe("computeFindingWindow", () => {
	const items = buildFindingListItems(
		[group("", Array.from({ length: 100 }, (_, index) => index))],
		false,
	);
	const offsets = buildItemOffsets(items, ROW);

	it("возвращает пустое окно для пустого списка", () => {
		expect(computeFindingWindow([0], 0, 500, 4)).toEqual({
			start: 0,
			end: 0,
			padTop: 0,
			padBottom: 0,
		});
	});

	it("держит распорки равными полной высоте списка", () => {
		const view = computeFindingWindow(offsets, 1000, 500, 0);
		const rendered = (view.end - view.start) * ROW;
		expect(view.padTop + rendered + view.padBottom).toBe(ROW * 100);
	});

	it("не выходит за границы списка", () => {
		const view = computeFindingWindow(offsets, 99_000, 500, 4);
		expect(view.end).toBeLessThanOrEqual(100);
		expect(view.padBottom).toBeGreaterThanOrEqual(0);
	});

	it("оставляет выбранную находку в DOM, даже если она вне прокрутки", () => {
		const view = computeFindingWindow(offsets, 0, 500, 4, 90);
		expect(view.start).toBeLessThanOrEqual(90);
		expect(view.end).toBeGreaterThan(90);
	});
});

describe("computeScrollTopToRevealItem", () => {
	const items = buildFindingListItems(
		[group("", Array.from({ length: 10 }, (_, index) => index))],
		false,
	);
	const offsets = buildItemOffsets(items, ROW);

	it("не двигает прокрутку, если элемент уже виден", () => {
		expect(computeScrollTopToRevealItem(offsets, 2, 500, 0)).toBe(0);
	});

	it("поднимает список к элементу выше окна", () => {
		expect(computeScrollTopToRevealItem(offsets, 1, 500, 600)).toBe(ROW);
	});

	it("опускает список к элементу ниже окна", () => {
		expect(computeScrollTopToRevealItem(offsets, 9, 500, 0)).toBe(ROW * 10 - 500);
	});

	it("игнорирует отсутствующий элемент", () => {
		expect(computeScrollTopToRevealItem(offsets, -1, 500, 120)).toBe(120);
	});
});

describe("findItemIndexForIssue", () => {
	it("учитывает сдвиг из-за заголовков групп", () => {
		const items = buildFindingListItems(
			[group("A", [0, 1]), group("B", [2])],
			true,
		);
		expect(findItemIndexForIssue(items, 0)).toBe(1);
		expect(findItemIndexForIssue(items, 2)).toBe(4);
		expect(findItemIndexForIssue(items, 42)).toBe(-1);
	});
});

describe("buildVisibleRuns", () => {
	it("сшивает видимые элементы обратно в группы", () => {
		const items = buildFindingListItems(
			[group("A", [0, 1]), group("B", [2])],
			true,
		);
		const runs = buildVisibleRuns(items);
		expect(runs).toHaveLength(2);
		expect(runs[0]).toMatchObject({ groupKey: "A", headerCount: 2 });
		expect(runs[0]?.rows).toHaveLength(2);
		expect(runs[1]).toMatchObject({ groupKey: "B", headerCount: 1 });
	});

	it("помечает группу без заголовка, если он прокручен за окно", () => {
		const items = buildFindingListItems([group("A", [0, 1])], true);
		const runs = buildVisibleRuns(items.slice(1));
		expect(runs).toHaveLength(1);
		expect(runs[0]?.headerCount).toBeNull();
		expect(runs[0]?.rows).toHaveLength(2);
	});
});
