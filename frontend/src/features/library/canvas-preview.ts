import type { Row } from "../../model";

const legacyCanvasLink = /(?:https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?\/|(?:^|[\s([`])\/?)#canvas\/([\w-]+)\/([1-9]\d*)(?=$|[\s)\]`.,;])/g;

export function matchesCanvasPublication(ticket: Row, profile: Row, version: number) {
  if (ticket.project !== profile.project) return false;

  const hasDesign = ticket.criteria?.some(criterion => criterion.design);
  if (hasDesign) {
    return !!ticket.criteria?.some(({ design }) => design?.document_id === profile.id && design.version === version);
  }

  // Older tickets stored a pinned local Canvas URL alongside their Design Profile Context link.
  if (!ticket.documents?.includes(profile.id)) return false;
  return Array.from((ticket.description || "").matchAll(legacyCanvasLink)).some(
    match => match[1] === profile.id && Number(match[2]) === version,
  );
}

export function verifiedScreenCount(count: number | null | undefined) {
  return typeof count === "number" && Number.isSafeInteger(count) && count > 0 ? String(count) : "Not recorded";
}

export function canvasPreviewGeometry(width: number, height: number, fit: boolean) {
  if (!fit || height <= 0 || width <= 0) return { width: "100%", height: "100%", scale: 1 };

  // Archived galleries control their own contents. Fit their outer viewport without reaching into the sandbox.
  const logicalHeight = 980;
  const scale = Math.min(1, height / logicalHeight);
  return {
    width: `${Math.ceil(width < 720 ? width : width / scale)}px`,
    height: `${Math.ceil(height / scale)}px`,
    scale,
  };
}
