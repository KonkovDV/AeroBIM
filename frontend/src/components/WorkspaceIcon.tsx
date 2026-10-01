/** Local, decorative outline icons. No CDN, icon font or dependency. */
const paths: Record<string, string> = {
  projects: "M3 7h7l2 2h9v11H3V7Z M3 7V4h7l2 3h8v2",
  upload: "M12 16V3m-4 4 4-4 4 4 M4 15v6h16v-6",
  run: "m9 5 11 7-11 7V5Z M4 5v14",
  review: "M4 4h16v16H4V4Z M8 9l2 2 5-5 M8 16h8",
  remark: "M4 4h16v12H9l-5 4V4Z M8 8h8 M8 12h5",
  export: "M12 3v13m-4-4 4 4 4-4 M4 17v4h16v-4",
  diff: "M6 4v16 M18 4v16 M3 7h6 M15 17h6 M10 10l4 4m0-4-4 4",
  user: "M4 20V10h4v10 M10 20V4h4v16 M16 20v-7h4v7",
};
export default function WorkspaceIcon({ name }: { name: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d={paths[name] ?? paths.projects} />
    </svg>
  );
}
