// AI đã chọn nơi gần nhất: chỉ nhận id có trong danh sách ứng viên và đúng
// quan hệ cha-con; cấp đã khớp chính xác giữ nguyên.
const sources = $("Need Nearest").all(0);

return $input.all().map((item, index) => {
  const src = sources[index]?.json || {};
  const state = { ...(src._loc_state || {}), how: { ...(src._loc_state?.how || {}) } };
  const req = src._loc_nearest || {};
  const ai = parseAiJson(item.json);

  const cands = new Map((req.candidates || []).map((a) => [a[1] + ":" + a[0], a]));
  const get = (level, id) => cands.get(level + ":" + s(id)) || null;

  let prov = state.province;
  let city = state.city;
  let dist = state.district;
  const chosen = {
    province: s(ai.province_id),
    city: s(ai.city_id),
    district: s(ai.district_id),
  };

  if (req.scope === "province") {
    const p = get("province", chosen.province);
    const c = get("city", chosen.city);
    if (c) {
      // Thành phố quyết định tỉnh (tránh lệch cha-con).
      city = c;
      prov = get("province", c[3]) || prov;
    } else if (p) {
      prov = p;
    }
  } else if (req.scope === "city") {
    const c = get("city", chosen.city);
    const d = get("district", chosen.district);
    if (d && (!c || d[3] === c[0])) {
      dist = d;
      city = get("city", d[3]);
    } else if (c) {
      city = c;
    }
  } else if (req.scope === "district") {
    const d = get("district", chosen.district);
    if (d) dist = d;
  }

  for (const [level, before, after] of [
    ["province", state.province, prov],
    ["city", state.city, city],
    ["district", state.district, dist],
  ]) {
    if (after && (!before || before[0] !== after[0])) state.how[level] = "nearest";
  }
  state.province = prov;
  state.city = city;
  state.district = dist;
  state.nearest = {
    scope: req.scope,
    chosen,
    confidence: ai.confidence ?? null,
    reason: s(ai.reason),
  };

  return { json: finalize(src, state), binary: sources[index]?.binary };
});
