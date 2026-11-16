// Trả về đúng thứ tự input ban đầu, bỏ field nội bộ.
return $input
  .all()
  .sort((a, b) => (a.json._loc_order ?? 0) - (b.json._loc_order ?? 0))
  .map((item) => {
    const { _loc_order, _loc_need_nearest, ...json } = item.json;
    return { json, binary: item.binary };
  });
