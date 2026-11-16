// ===== common (ghép vào đầu node Match Locations và Apply Nearest) =====
const s = (v) => String(v ?? "").replace(/\s+/g, " ").trim();

// JSON trong output của node OpenAI (nhiều dạng response khác nhau).
function parseAiJson(value) {
  const strings = [];
  const walk = (v) => {
    if (typeof v === "string") strings.push(v);
    else if (Array.isArray(v)) v.forEach(walk);
    else if (v && typeof v === "object") {
      if ("provinceNameCn" in v || "province_id" in v || "district_id" in v) {
        strings.unshift(JSON.stringify(v));
        return;
      }
      Object.values(v).forEach(walk);
    }
  };
  walk(value);
  for (const raw of strings) {
    const text = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();
    const m = text.match(/\{[\s\S]*\}/);
    if (!m) continue;
    try {
      return JSON.parse(m[0]);
    } catch {}
  }
  return {};
}

// Bản ghi gọn để lưu trong item: [id, level, code, parent, name, cn, postcode]
const pack = (r) =>
  r ? [r.id, r.level, r.code, r.parent, r.name, r.cn, r.postcode || ""] : null;
const unpack = (a) =>
  a
    ? {
        id: a[0],
        level: a[1],
        code: a[2],
        parent: a[3],
        name: a[4],
        cn: a[5],
        postcode: a[6],
      }
    : null;

// Ghi kết quả cuối: tên pinyin = đúng `name` trong china_locations.json
// (để /run tra ra mã COVA chắc chắn), kèm chữ Hán chuẩn và mã COVA.
function finalize(json, state) {
  const prov = unpack(state.province);
  const city = unpack(state.city);
  const dist = unpack(state.district);
  const out = { ...json };
  for (const key of Object.keys(out)) if (key.startsWith("_loc_")) delete out[key];
  out._loc_order = json._loc_idx ?? 0; // Restore Order dùng rồi xoá

  out.provinceNameCn = prov?.cn || "";
  out.cityNameCn = city?.cn || "";
  out.districtNameCn = dist?.cn || "";
  out.provinceNamePinyin = prov?.name || "";
  out.cityNamePinyin = city?.name || "";
  out.districtNamePinyin = dist?.name || "";
  out.province_code = prov?.code || "";
  out.city_code = city?.code || "";
  out.district_code = dist?.code || "";
  out.china_location = {
    address: json._loc_address || "",
    extracted: state.extracted || {},
    province: prov ? `${prov.cn} / ${prov.name}` : "",
    city: city ? `${city.cn} / ${city.name}` : "",
    district: dist ? `${dist.cn} / ${dist.name}` : "",
    postcode: dist?.postcode || "",
    // exact | inferred | corrected | nearest | missing | unmatched
    match: state.how,
    nearest: state.nearest || null,
  };
  return out;
}
// ===== end common =====
