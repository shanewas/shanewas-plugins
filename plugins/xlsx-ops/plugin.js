export const plugin = async (ctx) => {
  return {
    name: "xlsx-ops",
    description: "Spreadsheet edits through one JSON CLI on openpyxl: read, find, set cells and ranges, rows, columns, sheets, merges, formats, images, plus formula recalculation in real Excel over COM.",
    version: "1.1.0"
  };
};
