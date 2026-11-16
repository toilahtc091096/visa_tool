// Input: item của flow gọi (passthrough). Địa chỉ lấy theo thứ tự:
// location_address > companyAddress > school_address > addressRaw > inviterAddress.
// Đánh số để trả kết quả đúng thứ tự (bên gọi nhận lại đúng item của mình).
const s = (v) => String(v ?? "").replace(/\s+/g, " ").trim();

return $input.all().map((item, index) => {
  const j = item.json || {};
  const address = s(
    j.location_address ||
      j.companyAddress ||
      j.company_address ||
      j.school_address ||
      j.addressRaw ||
      j.inviterAddress,
  );

  return {
    json: {
      ...j,
      _loc_idx: index,
      _loc_address: address,
      _loc_id_card: s(j.idCardNumber || j.inviterIdCard).toUpperCase(),
      // Gợi ý (nếu flow gọi đã có sẵn), AI chung vẫn đọc lại từ địa chỉ.
      _loc_hint: [
        s(j.provinceNameCn) || s(j.provinceNamePinyin),
        s(j.cityNameCn) || s(j.cityNamePinyin),
        s(j.districtNameCn) || s(j.districtNamePinyin),
      ]
        .filter(Boolean)
        .join(" / "),
    },
    binary: item.binary,
  };
});
