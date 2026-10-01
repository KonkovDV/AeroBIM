/**
 * Оконный (виртуализированный) список находок.
 *
 * Зачем отдельный модуль: до этого виртуализация в FindingListPanel считалась
 * по плоскому списку строк, из-за чего при числе находок больше порога
 * заголовки групп молча пропадали — эксперт видел «сплошную кашу» вместо
 * группировки по правилу/этажу/оси. Здесь заголовок — такой же элемент
 * списка, как строка, поэтому окно и отступы считаются честно.
 *
 * Функции чистые и не знают про React: их проверяет finding-window.test.ts.
 */

import type { IndexedIssue } from "./issue-triage";

export type FindingListItem =
	| { kind: "header"; groupKey: string; count: number }
	| { kind: "row"; groupKey: string; row: IndexedIssue };

/** Высота заголовка группы в оконном режиме. Держать синхронно со styles.css. */
export const FINDING_GROUP_HEADER_HEIGHT = 36;

export type FindingVisibleRun = {
	groupKey: string;
	/** null — заголовок группы вне окна прокрутки. */
	headerCount: number | null;
	rows: IndexedIssue[];
};

export type FindingWindow = {
	start: number;
	end: number;
	padTop: number;
	padBottom: number;
};

/** Плоский список элементов: заголовок группы + её строки. */
export function buildFindingListItems(
	groups: ReadonlyArray<{ key: string; rows: IndexedIssue[] }>,
	withHeaders: boolean,
): FindingListItem[] {
	const items: FindingListItem[] = [];
	for (const group of groups) {
		if (withHeaders) {
			items.push({
				kind: "header",
				groupKey: group.key,
				count: group.rows.length,
			});
		}
		for (const row of group.rows) {
			items.push({ kind: "row", groupKey: group.key, row });
		}
	}
	return items;
}

/**
 * Накопленные смещения по вертикали: offsets[i] — верх элемента i,
 * offsets[items.length] — полная высота списка.
 */
export function buildItemOffsets(
	items: ReadonlyArray<FindingListItem>,
	rowHeight: number,
	headerHeight: number = FINDING_GROUP_HEADER_HEIGHT,
): number[] {
	const safeRow = Math.max(1, Math.round(rowHeight));
	const safeHeader = Math.max(1, Math.round(headerHeight));
	const offsets: number[] = [0];
	for (const item of items) {
		const previous = offsets[offsets.length - 1] ?? 0;
		offsets.push(previous + (item.kind === "header" ? safeHeader : safeRow));
	}
	return offsets;
}

/** Индекс элемента списка по индексу находки. -1, если находка отфильтрована. */
export function findItemIndexForIssue(
	items: ReadonlyArray<FindingListItem>,
	issueIndex: number,
): number {
	return items.findIndex(
		(item) => item.kind === "row" && item.row.index === issueIndex,
	);
}

function lastIndexAtOrBefore(
	offsets: ReadonlyArray<number>,
	target: number,
): number {
	const last = offsets.length - 2;
	if (last < 0) {
		return 0;
	}
	let low = 0;
	let high = last;
	let best = 0;
	while (low <= high) {
		const mid = (low + high) >> 1;
		if ((offsets[mid] ?? 0) <= target) {
			best = mid;
			low = mid + 1;
		} else {
			high = mid - 1;
		}
	}
	return best;
}

/**
 * Окно видимых элементов и отступы-распорки.
 *
 * mustInclude — индекс элемента, который обязан остаться в DOM (выбранная
 * находка). Без него aria-activedescendant ссылается на неотрисованный id,
 * и скринридер уводит фокус в пустоту.
 */
export function computeFindingWindow(
	offsets: ReadonlyArray<number>,
	scrollTop: number,
	viewportHeight: number,
	overscan: number,
	mustInclude = -1,
): FindingWindow {
	const count = Math.max(0, offsets.length - 1);
	if (count === 0) {
		return { start: 0, end: 0, padTop: 0, padBottom: 0 };
	}
	const total = offsets[count] ?? 0;
	const top = Math.min(Math.max(0, scrollTop), total);
	const bottom = top + Math.max(1, viewportHeight);
	const safeOverscan = Math.max(0, Math.round(overscan));
	let start = Math.max(0, lastIndexAtOrBefore(offsets, top) - safeOverscan);
	let end = Math.min(
		count,
		lastIndexAtOrBefore(offsets, bottom) + 1 + safeOverscan,
	);
	if (mustInclude >= 0 && mustInclude < count) {
		start = Math.min(start, Math.max(0, mustInclude - safeOverscan));
		end = Math.max(end, Math.min(count, mustInclude + safeOverscan + 1));
	}
	end = Math.max(end, Math.min(count, start + 1));
	return {
		start,
		end,
		padTop: offsets[start] ?? 0,
		padBottom: Math.max(0, total - (offsets[end] ?? total)),
	};
}

/** Минимальная прокрутка, при которой элемент itemIndex попадает в окно. */
export function computeScrollTopToRevealItem(
	offsets: ReadonlyArray<number>,
	itemIndex: number,
	viewportHeight: number,
	scrollTop: number,
): number {
	const count = Math.max(0, offsets.length - 1);
	if (itemIndex < 0 || itemIndex >= count || viewportHeight <= 0) {
		return scrollTop;
	}
	const top = offsets[itemIndex] ?? 0;
	const bottom = offsets[itemIndex + 1] ?? top;
	if (top < scrollTop) {
		return top;
	}
	if (bottom > scrollTop + viewportHeight) {
		return Math.max(0, bottom - viewportHeight);
	}
	return scrollTop;
}

/**
 * Видимые элементы, сшитые обратно в группы. Нужно, чтобы разметка осталась
 * валидной: у role="listbox" дочерними могут быть только option и group.
 */
export function buildVisibleRuns(
	items: ReadonlyArray<FindingListItem>,
): FindingVisibleRun[] {
	const runs: FindingVisibleRun[] = [];
	for (const item of items) {
		let run = runs[runs.length - 1];
		if (!run || run.groupKey !== item.groupKey) {
			run = { groupKey: item.groupKey, headerCount: null, rows: [] };
			runs.push(run);
		}
		if (item.kind === "header") {
			run.headerCount = item.count;
		} else {
			run.rows.push(item.row);
		}
	}
	return runs;
}
