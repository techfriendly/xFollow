export type Severity = "critica" | "alta" | "media" | "baja";

export function formatEuro(value?: number | null) {
  if (value === undefined || value === null) return "Pendiente";
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0
  }).format(value);
}

export function statusLabel(value: string) {
  const labels: Record<string, string> = {
    queued: "En cola",
    running: "En curso",
    retrying: "Reintentando",
    completed: "Completado",
    failed: "Fallido",
    needs_review: "Requiere revisión",
    at_risk: "En riesgo",
    scope: "Alcance",
    schedule: "Plazo",
    resources: "Recursos",
    quality: "Calidad",
    economic: "Económico",
    legal: "Jurídico",
    other: "Otro",
    will_extend: "Se prorrogará",
    no_renewal: "No se renueva"
  };
  return labels[value] || value.replaceAll("_", " ");
}

export function severityClass(severity?: string) {
  return {
    critica: "danger",
    alta: "danger",
    media: "warning",
    baja: "info"
  }[severity || "media"] || "info";
}

export function shortDate(value?: string | null) {
  if (!value) return "Pendiente";
  return new Intl.DateTimeFormat("es-ES", { dateStyle: "medium" }).format(new Date(value));
}
