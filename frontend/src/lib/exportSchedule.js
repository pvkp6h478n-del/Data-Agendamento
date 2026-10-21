import * as XLSX from "xlsx";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

const HEAD = ["Data", "Horário", "Transportadora", "Fornecedor", "Nota fiscal", "Volumes", "Doca", "Status"];
const br = (d) => (d ? d.split("-").reverse().join("/") : "");
const toRows = (list) => list.map((a) => [br(a.appointment_date), a.appointment_time, a.carrier_name, a.supplier_name, a.invoice_number, Number(a.volume_count), a.dock_door, a.status]);
const count = (n) => `${n} ${n === 1 ? "agendamento" : "agendamentos"}`;
const total = (list) => list.reduce((s, a) => s + Number(a.volume_count), 0);

export const periodLabel = (f) => {
  const parts = [f.end && f.end !== f.start ? `${br(f.start)} a ${br(f.end)}` : br(f.start) || "Todas as datas"];
  if (f.carrier) parts.push(`Transportadora: ${f.carrier}`);
  if (f.supplier) parts.push(`Fornecedor: ${f.supplier}`);
  return parts.join(" | ");
};
const fileName = (f, ext) => `docksync-agenda-${f.start || "geral"}${f.end && f.end !== f.start ? `_${f.end}` : ""}.${ext}`;

export function exportExcel(list, filters) {
  const data = [["DockSync — Agenda de recebimento"], [periodLabel(filters)], [], HEAD, ...toRows(list), [], ["", "", "", "", "TOTAL", total(list), "", count(list.length)]];
  const ws = XLSX.utils.aoa_to_sheet(data);
  ws["!cols"] = [12, 9, 26, 26, 16, 10, 8, 14].map((wch) => ({ wch }));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Agenda");
  XLSX.writeFile(wb, fileName(filters, "xlsx"));
}

export function exportPdf(list, filters) {
  const doc = new jsPDF({ orientation: "landscape" });
  doc.setFontSize(16).text("DockSync — Agenda de recebimento", 14, 16);
  doc.setFontSize(10).setTextColor(90).text(periodLabel(filters), 14, 23);
  doc.text(`Gerado em ${new Date().toLocaleString("pt-BR")}`, 14, 29);
  autoTable(doc, {
    startY: 34,
    head: [HEAD],
    body: toRows(list),
    foot: [["", "", "", "", "TOTAL", total(list), "", count(list.length)]],
    headStyles: { fillColor: [15, 23, 42] },
    footStyles: { fillColor: [241, 245, 249], textColor: [15, 23, 42], fontStyle: "bold" },
    styles: { fontSize: 9 },
  });
  doc.save(fileName(filters, "pdf"));
}
