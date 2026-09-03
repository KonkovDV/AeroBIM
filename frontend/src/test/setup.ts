import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

const originalAnchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function click(this: HTMLAnchorElement) {
  // jsdom throws "Not implemented: navigation to another Document" on
  // blob/object-URL downloads. Tests assert UI + URL.createObjectURL, not I/O.
  if (this.download || this.hasAttribute("download")) {
    return;
  }
  return originalAnchorClick.call(this);
};

HTMLElement.prototype.scrollIntoView = function scrollIntoView() {
  // jsdom has no layout. Production uses nearest-block scroll for export/findings.
};

afterEach(() => {
  cleanup();
});
