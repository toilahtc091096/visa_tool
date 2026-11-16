// Lọc cuối theo resources/china_locations.json (nhúng bởi
// scripts/build_n8n_china_location.py - KHÔNG sửa tay phần DATA).
// AI trích xuất -> so khớp từng cấp (chữ Hán trước, pinyin sau).
// Cấp nào không khớp / thiếu -> chuẩn bị danh sách ứng viên cho AI chọn nơi gần nhất.
const DATA = /*__CHINA_LOCATIONS__*/ null;

// ---------- chuẩn hoá ----------
function pyKey(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

const PY_SUFFIX = {
  province: ["zhuangzuzizhiqu", "weiwuerzizhiqu", "huizuzizhiqu", "tebiexingzhengqu", "zizhiqu", "sheng", "shi"],
  city: ["zizhizhou", "diqu", "meng", "shi"],
  district: ["zizhixian", "zizhiqi", "linqu", "shi", "xian", "qu", "qi"],
};

function stripPy(key, level) {
  for (const suffix of PY_SUFFIX[level]) {
    if (key.endsWith(suffix) && key.length > suffix.length) return key.slice(0, -suffix.length);
  }
  return key;
}

const cnKey = (value) => String(value ?? "").replace(/[\s·.,，。()（）]/g, "");

const CN_SUFFIX = [
  "特别行政区", "维吾尔自治区", "壮族自治区", "回族自治区", "自治区",
  "自治州", "自治县", "自治旗", "地区", "林区", "特区", "省", "市", "区", "县", "盟", "旗",
];
const ETHNIC_TAIL = /^(?:[一-鿿]{1,5}?族)+$/;

function cnBase(value) {
  let t = cnKey(value);
  for (const suffix of CN_SUFFIX) {
    if (t.endsWith(suffix) && t.length > suffix.length) {
      t = t.slice(0, -suffix.length);
      break;
    }
  }
  // 红河哈尼族彝族 -> 红河 (bỏ tên dân tộc của đơn vị tự trị)
  for (let i = 2; i < t.length - 1; i++) {
    if (ETHNIC_TAIL.test(t.slice(i))) return t.slice(0, i);
  }
  return t;
}

// ---------- dữ liệu ----------
const mk = (level) => (r) => {
  const [id, code, parent, name, cn, postcode] =
    level === "province" ? [r[0], r[1], "", r[2], r[3], ""] : r;
  const row = { level, id, code, parent, name, cn, postcode: postcode || "" };
  row.py = pyKey(name);
  row.pyBase = stripPy(row.py, level);
  row.cnKey = cnKey(cn);
  row.cnBase = cnBase(cn);
  return row;
};
const P = DATA.p.map(mk("province"));
const C = DATA.c.map(mk("city"));
const K = DATA.k.map(mk("district"));
const byId = new Map([...P, ...C, ...K].map((r) => [r.level + ":" + r.id, r]));
const getRow = (level, id) => byId.get(level + ":" + id) || null;
const citiesOf = (provId) => C.filter((r) => r.parent === provId);
const districtsOf = (cityId) => K.filter((r) => r.parent === cityId);
function districtsOfProvince(provId) {
  const ids = new Set(citiesOf(provId).map((r) => r.id));
  return K.filter((r) => ids.has(r.parent));
}

// Khớp 1 cấp: chữ Hán (đúng -> bỏ hậu tố -> tiền tố), rồi pinyin (đúng -> bỏ hậu tố -> tiền tố).
// Nhiều kết quả trùng tên -> dùng 6 số đầu CCCD phân biệt (cấp quận/huyện), không thì bỏ.
function pick(rows, cn, py, level, idCard) {
  const k = cnKey(cn);
  const b = cnBase(cn);
  const p = pyKey(py);
  const pb = stripPy(p, level);
  const tests = [];
  if (k) tests.push((r) => r.cnKey === k);
  if (b.length >= 2) tests.push((r) => r.cnBase === b);
  if (b.length >= 2)
    tests.push((r) => r.cnBase.length >= 2 && (r.cnBase.startsWith(b) || b.startsWith(r.cnBase)));
  if (p) tests.push((r) => r.py === p);
  if (pb.length >= 2) tests.push((r) => r.pyBase === pb);
  if (pb.length >= 3)
    tests.push((r) => r.pyBase.length >= 3 && (r.pyBase.startsWith(pb) || pb.startsWith(r.pyBase)));
  for (const test of tests) {
    let hits = rows.filter(test);
    if (hits.length > 1 && idCard && level === "district") {
      hits = hits.filter((r) => r.id === idCard.slice(0, 6));
    }
    if (hits.length === 1) return hits[0];
    if (hits.length > 1) return null; // trùng tên, không đoán
  }
  return null;
}

function resolve(ex, idCard) {
  const has = {
    province: Boolean(ex.provinceNameCn || ex.provinceNamePinyin),
    city: Boolean(ex.cityNameCn || ex.cityNamePinyin),
    district: Boolean(ex.districtNameCn || ex.districtNamePinyin),
  };
  const how = { province: "missing", city: "missing", district: "missing" };
  let prov = has.province
    ? pick(P, ex.provinceNameCn, ex.provinceNamePinyin, "province")
    : null;
  if (prov) how.province = "exact";

  // Thành phố
  let city = null;
  if (has.city) {
    city = pick(prov ? citiesOf(prov.id) : C, ex.cityNameCn, ex.cityNamePinyin, "city");
    if (city) {
      how.city = "exact";
      if (!prov) {
        prov = getRow("province", city.parent);
        how.province = has.province ? "corrected" : "inferred";
      }
    }
  }

  // Quận/huyện
  let dist = null;
  if (has.district && city) {
    dist = pick(districtsOf(city.id), ex.districtNameCn, ex.districtNamePinyin, "district", idCard);
    if (dist) how.district = "exact";
  }
  if (has.district && !city) {
    // Chưa có thành phố: tìm quận/huyện trong cả tỉnh (hoặc cả nước) rồi suy ngược lên.
    dist = pick(
      prov ? districtsOfProvince(prov.id) : K,
      ex.districtNameCn,
      ex.districtNamePinyin,
      "district",
      idCard,
    );
    if (dist) {
      how.district = "exact";
      city = getRow("city", dist.parent);
      how.city = has.city ? "corrected" : "inferred";
      if (city && !prov) {
        prov = getRow("province", city.parent);
        how.province = has.province ? "corrected" : "inferred";
      }
    }
  }
  if (has.city && !city) {
    // Thành phố cấp huyện ghi ở ô thành phố (南安市): là 1 quận/huyện của tỉnh.
    const k = pick(
      prov ? districtsOfProvince(prov.id) : K,
      ex.cityNameCn,
      ex.cityNamePinyin,
      "district",
      idCard,
    );
    if (k) {
      city = getRow("city", k.parent);
      how.city = "corrected";
      if (!dist) {
        dist = k;
        how.district = has.district ? "corrected" : "inferred";
      }
      if (city && !prov) {
        prov = getRow("province", city.parent);
        how.province = has.province ? "corrected" : "inferred";
      }
    }
  }

  // Tỉnh chỉ có 1 thành phố (北京/上海/天津/重庆...), thành phố chỉ có 1 quận/huyện (东莞...).
  if (prov && !city) {
    const list = citiesOf(prov.id);
    if (list.length === 1) {
      city = list[0];
      how.city = has.city ? "corrected" : "inferred";
    }
  }
  if (city && !dist) {
    const list = districtsOf(city.id);
    if (list.length === 1) {
      dist = list[0];
      how.district = has.district ? "corrected" : "inferred";
    }
  }

  for (const level of ["province", "city", "district"]) {
    if (has[level] && how[level] === "missing") how[level] = "unmatched";
  }
  return { prov, city, dist, how };
}

// Danh sách ứng viên cho AI chọn nơi gần nhất (chỉ cấp còn thiếu).
function nearestRequest(r) {
  if (!r.prov) {
    return {
      scope: "province",
      choose: "province_id and city_id",
      candidates: [...P, ...C],
    };
  }
  if (!r.city) {
    return {
      scope: "city",
      choose: "city_id and district_id",
      candidates: [...citiesOf(r.prov.id), ...districtsOfProvince(r.prov.id)],
    };
  }
  if (!r.dist) {
    const list = districtsOf(r.city.id);
    if (!list.length) return null;
    return { scope: "district", choose: "district_id", candidates: list };
  }
  return null;
}

const sources = $("Prepare").all();

return $input.all().map((item, index) => {
  const src = sources[index]?.json || {};
  const ai = parseAiJson(item.json);
  const extracted = {
    provinceNameCn: s(ai.provinceNameCn),
    cityNameCn: s(ai.cityNameCn),
    districtNameCn: s(ai.districtNameCn),
    provinceNamePinyin: s(ai.provinceNamePinyin),
    cityNamePinyin: s(ai.cityNamePinyin),
    districtNamePinyin: s(ai.districtNamePinyin),
  };
  const r = resolve(extracted, src._loc_id_card || "");
  const state = {
    extracted,
    how: r.how,
    province: pack(r.prov),
    city: pack(r.city),
    district: pack(r.dist),
  };

  const req = src._loc_address ? nearestRequest(r) : null;
  if (!req) {
    return { json: { ...finalize(src, state), _loc_need_nearest: false }, binary: sources[index]?.binary };
  }

  const matchedText =
    [
      r.prov && `province ${r.prov.id} ${r.prov.cn} ${r.prov.name}`,
      r.city && `city ${r.city.id} ${r.city.cn} ${r.city.name}`,
    ]
      .filter(Boolean)
      .join("; ") || "(none)";
  return {
    json: {
      ...src,
      _loc_need_nearest: true,
      _loc_state: state,
      _loc_nearest: {
        scope: req.scope,
        choose: req.choose,
        matched: matchedText,
        extracted: [extracted.provinceNameCn, extracted.cityNameCn, extracted.districtNameCn]
          .map((v) => v || "?")
          .join(" / "),
        candidatesText: req.candidates
          .map((x) => `${x.id} | ${x.level} | ${x.name} | ${x.cn} | ${x.parent}`)
          .join("\n"),
        candidates: req.candidates.map(pack),
      },
    },
    binary: sources[index]?.binary,
  };
});
