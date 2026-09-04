/**
 * Gerador mínimo de .xlsx no browser, sem biblioteca.
 * Porte enxuto do utilitário usado na referência Skyline (skyline-precos.js):
 * ZIP (store/deflate-raw) + uma planilha com inlineStr / números.
 *
 * API: XlsxMini.baixar(nomeArquivo, cabecalhos[], linhas[][])
 */
window.XlsxMini = (() => {
  const enc = new TextEncoder();

  let crcTable;
  function crc32(bytes) {
    if (!crcTable) {
      crcTable = new Uint32Array(256);
      for (let i = 0; i < 256; i++) {
        let c = i;
        for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
        crcTable[i] = c >>> 0;
      }
    }
    let crc = 0xffffffff;
    for (let i = 0; i < bytes.length; i++) crc = crcTable[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
    return (crc ^ 0xffffffff) >>> 0;
  }

  const u16 = (n) => new Uint8Array([n & 255, (n >>> 8) & 255]);
  const u32 = (n) => new Uint8Array([n & 255, (n >>> 8) & 255, (n >>> 16) & 255, (n >>> 24) & 255]);

  function concat(parts) {
    const total = parts.reduce((n, p) => n + p.length, 0);
    const out = new Uint8Array(total);
    let o = 0;
    for (const p of parts) { out.set(p, o); o += p.length; }
    return out;
  }

  async function deflateRaw(bytes) {
    if (typeof CompressionStream === "undefined") return null;
    try {
      const s = new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"));
      return new Uint8Array(await new Response(s).arrayBuffer());
    } catch { return null; }
  }

  async function makeZip(files) {
    const locals = [], centrals = [];
    let offset = 0;
    for (const f of files) {
      const name = enc.encode(f.name);
      const data = typeof f.data === "string" ? enc.encode(f.data) : f.data;
      const crc = crc32(data);
      const def = await deflateRaw(data);
      const useDef = def && def.length < data.length;
      const payload = useDef ? def : data;
      const method = useDef ? 8 : 0;
      const local = concat([
        enc.encode("PK\x03\x04"), u16(20), u16(0), u16(method), u16(0), u16(0),
        u32(crc), u32(payload.length), u32(data.length), u16(name.length), u16(0), name, payload,
      ]);
      const central = concat([
        enc.encode("PK\x01\x02"), u16(20), u16(20), u16(0), u16(method), u16(0), u16(0),
        u32(crc), u32(payload.length), u32(data.length), u16(name.length),
        u16(0), u16(0), u16(0), u16(0), u32(0), u32(offset), name,
      ]);
      locals.push(local); centrals.push(central); offset += local.length;
    }
    const dir = concat(centrals);
    const end = concat([
      enc.encode("PK\x05\x06"), u16(0), u16(0), u16(files.length), u16(files.length),
      u32(dir.length), u32(offset), u16(0),
    ]);
    return concat([...locals, dir, end]);
  }

  const esc = (s) => String(s ?? "")
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  const colRef = (c) => {
    let s = "";
    c++;
    while (c > 0) { const m = (c - 1) % 26; s = String.fromCharCode(65 + m) + s; c = ((c - m) / 26) | 0; }
    return s;
  };

  function cell(c, r, v) {
    const ref = colRef(c) + r;
    if (typeof v === "number" && Number.isFinite(v)) return `<c r="${ref}"><v>${v}</v></c>`;
    return `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${esc(v)}</t></is></c>`;
  }

  function sheetXml(headers, rows) {
    const all = [headers, ...rows];
    const body = all.map((row, i) =>
      `<row r="${i + 1}">${row.map((v, c) => cell(c, i + 1, v)).join("")}</row>`,
    ).join("");
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${body}</sheetData></worksheet>`;
  }

  async function baixar(nome, headers, rows) {
    const files = [
      { name: "[Content_Types].xml", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>` },
      { name: "_rels/.rels", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>` },
      { name: "xl/_rels/workbook.xml.rels", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>` },
      { name: "xl/workbook.xml", data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Estoque" sheetId="1" r:id="rId1"/></sheets></workbook>` },
      { name: "xl/worksheets/sheet1.xml", data: sheetXml(headers, rows) },
    ];
    const zip = await makeZip(files);
    const blob = new Blob([zip], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = nome; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 20000);
  }

  return { baixar };
})();
