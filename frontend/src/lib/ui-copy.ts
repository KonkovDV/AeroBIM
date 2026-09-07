/** One public copy surface; product wording is split by concern under i18n. */
import { RU_COPY } from "./i18n/ru";
import { WORKPLACE_COPY } from "./i18n/workplace";
import { EVIDENCE_COPY } from "./i18n/evidence";

export const UI_COPY = { ...RU_COPY, ...WORKPLACE_COPY, ...EVIDENCE_COPY } as const;
