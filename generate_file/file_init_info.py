from datetime import date, timedelta
from pathlib import Path
from typing import Any
import re

from docxtpl import DocxTemplate

from generate_file.docx_to_pdf import convert_docx_to_pdf
from utils import pdf_helper


def build_itinerary(first: date) -> list[dict]:

    routes = [
        {
            "title": "HÀ NỘI – BẮC KINH",
            "content": """
Đón đoàn khách tại sân bay, đưa khách về Khách sạn nghỉ ngơi.
""",
        },
        {
            "title": "BẮC KINH",
            "content": """
Đưa khách đi tham quan Tử Cấm Thành, Di Hòa Viên.
""",
        },
        {
            "title": "BẮC KINH",
            "content": """
Thăm quan Bát Đạt Lĩnh.
Thiên Đàn ( Đàn mặt trời ).
""",
        },
        {
            "title": "BẮC KINH",
            "content": """
Vương Phủ Tỉnh.
Thiên An Môn.
""",
        },
        {
            "title": "BẮC KINH",
            "content": """
Sân vận động tổ chim.
Đường Tràng An.
""",
        },
        {
            "title": "BẮC KINH",
            "content": """
Thăm quan phim trường Cổ Trang.
Chụp Ảnh với Trang phục Cổ Trang.
""",
        },
        {
            "title": "BẮC KINH – THƯỢNG HẢI",
            "content": """
Sau bữa ăn sáng, Quý khách checkout Khách sạn, Xe và HDV đưa khách ra ga đi tàu cao tốc đến Thượng Hải. Thời gian đi mất khoảng 4:30 phút. Trên tàu quý khách có thể ngắm cảnh đẹp trên đường đi. Đến nơi nhận phòng nghỉ ngơi.
""",
        },
        {
            "title": "THƯỢNG HẢI",
            "content": """
Sau bữa ăn sáng, quý khách tự do mua săm ở trung tâm Thượng Mại, ngắm các con phố ven song sầm uất.
Chiều đưa quý khách tham quan tháp truyền hình Đông Phương Minh Châu. Tòa tháp cao nhât Châu Á, và cao thứ 3 hành tinh.
""",
        },
        {
            "title": "THƯỢNG HẢI",
            "content": """
Thăm quan Miếu Thành Hoàng tọa lạc trên Quận Hoàng Phố là địa điểm mà thu hút nhiều khách du lịch đến thăm quan.
Chiều tham quan khu Tô giới Pháp là nơi trước đây sinh sống của người Pháp, Người Anh.
""",
        },
        {
            "title": "THƯỢNG HẢI",
            "content": """
Qúy khách tham quan Vườn Dự Viên là khu vườn và nhà cổ êm đềm tĩnh lặng giữa thành phố Thượng Hải náo nhiệt. Vườn được xây dựng từ thời Nhà Minh. Đây là địa điểm luôn xuất hiện bất cứ tour du lịch Thượng Hải nào.
Và quý khách sẽ được đến công viên Fuxing khi đến Thượng Hải, bởi đây là một công viên có không gian xanh giữa long thành phố. Và là nơi cảm nhận được nhip sống thường ngày của người dân Thượng Hải.
""",
        },
        {
            "title": "THƯỢNG HẢI",
            "content": """
Quý khách thăm quan Bảo Tàng Thượng Hải là một bảo tang nghệ thuật cổ Trung Hoa. Bảo Tàng năm trên Quảng Trường Nhân Dân, là một trong những địa điểm du lịch Thượng Hải hấp dẫn nhất dành cho những ai yêu thích.
Đường Dong Tai là thiên đường của những món quà lưu niệm đậm chất Trung Quốc. Tại đây bạn có thể gặp rất nhiều món đồ cổ từ thời xa xưa cách mạng văn hóa Trung Quốc.
""",
        },
        {
            "title": "THƯỢNG HẢI",
            "content": """
Quý khách thăm quan Tân Thiên Địa khu phố sầm uất nằm trong trung tâm Thành Phố. Đây là nơi được cho là thiên đường mua sắm với khách du lịch.
Chùa Phật Ngọc – Đây là ngôi chùa có 2 bức tượng Phật Thích Ca được tạc ở 2 tư thế khác nhau được chạm khắc tinh xảo và thể hiên nét uy nghi của Đức Phật.
""",
        },
        {
            "title": "THƯỢNG HẢI",
            "content": """
Đây là ngày mà quý khách sẽ rất vui vì sẽ được thưởng thức ẩm thực trung hoa nổi tiếng trên đường phố ẩm thực của Thượng Hải. Được thưởng thức các món Dimsum nổi tiếng tại nhà hang Xindalu.
Chiều Quý khách sẽ đi đên công viên Disneyland Thượng Hải, với đầy đủ các điểm tham quan và khu vui chơi giải trí.
""",
        },
        {
            "title": "THƯỢNG HẢI - QUẢNG CHÂU",
            "content": """
Sau bữa ăn sáng, Quý khách đi tàu Cao tốc đến Tp Quảng Châu là nơi phát triển bậc nhất Của Trung Quốc. Đến nơi quý khách nhận phòng nghỉ ngơi.
""",
        },
        {
            "title": "QUẢNG CHÂU",
            "content": """
Đưa quý khách tham quan tòa nhà cao 80 tầng năm ở quận Thiên Hà. Tòa nhà cao 391m được xây dựng từ năm 1997 với nhiều cửa hang thương hiệu cao cấp. Nơi lý tưởng chó các du khách có niềm đam mê với shopping.
Chiều quý khách thăm quan Tháp truyền hình Quảng Châu với chiều cao 600m, tháp truyền hình cao thư 2 thế giới. chỉ sau tháp truyền hinh Tokyo.
""",
        },
        {
            "title": "QUẢNG CHÂU",
            "content": """
Quý khách tham quan Công viên Việt Tú, công trình được xây dựng là cong viên lớn nhất của thành phố Quảng Châu.
Chiều tham quan Quảng trường Haizhu, một địa điểm nằm bên bờ song Việt Tú. Tại đây có bức tượng giải phòng Quảng Châu năm 1959.
""",
        },
        {
            "title": "QUẢNG CHÂU",
            "content": """
Sau bữa ăn sáng, quý khách thăm quan nhà tưởng niệm Tôn Trung Sơn, là một trong những nhà tưởng niệm lớn mà người Trung Quốc xây dựng để nhớ về người lãnh tụ vĩ đại của mình.
Chiều tham quan Núi Bạch Vân được người dân Trung hoa gọi là “Dương Thành đệ nhất tú” được thiên nhiên uu ai với 30 ngọn núi nhỏ tại nên cảnh đẹp Hùng vĩ.
""",
        },
        {
            "title": "QUẢNG CHÂU",
            "content": """
Qúy khách thăm quan công viên Liên Hoa Sơn, được mệnh danh là “ Vườn Quan Âm” bởi trên núi có cả ngàn bức tượng Quan Âm lớn nhỏ. Là nơi quy tụ nhiều tượng quan âm nhất thế giới.
Tham quan bảo tang Quảng Đông là bảo tang có quy mô lớn nhất tại Trung Quốc. Bảo tang này như là một kho báu chứa đồ cổ của Thành phố.
""",
        },
        {
            "title": "QUẢNG CHÂU",
            "content": """
Qúy khách tham quan Trần Gia Từ, hay còn gọi là từ đường Trần Gia, là từ đường nổi tiếng nhất Quảng Châu, đây là nơi ở của tầng lớp thượng lưu, phương nam Trung Quốc.
Chiều tham quan Vườn Bảo Mặc hay còn gọi là Vườn Bao Công là thắng cảnh luôn có tên trong danh sách điểm đến nổi tiếng nhất Quảng Châu.
""",
        },
        {
            "title": "QUẢNG CHÂU",
            "content": """
Quý khách tự do mua sắm và dạo chơi tại Quảng Châu.
""",
        },
        {
            "title": "QUẢNG CHÂU – HÀ NỘI",
            "content": """
Sau khi ăn sáng, quý khách trả phòng và về Hà Nội. Kết thúc hành trình.
""",
        },
    ]

    itinerary = []

    for idx, item in enumerate(routes):
        d = first + timedelta(days=idx)

        itinerary.append(
            {
                "day_no": idx + 1,
                "date": d.strftime("%d/%m/%Y"),
                "title": item["title"],
                "content": item["content"],
            }
        )

    return itinerary


async def render_init_pdf(
    payload: dict[str, Any],
    output_path: str = "",
) -> str:
    file_name: str = payload.get("file_name")
    names: list[str] = payload.get("names", [])
    first: date = payload.get("first")

    templates_base = Path(__file__).resolve().parent / ".." / "resources"
    output_base = Path(__file__).resolve().parent / ".." / "resources" / "data"

    src = (templates_base / file_name).resolve()

    out_dir = (output_base / output_path).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Docx not found: {src}")

    if src.suffix.lower() != ".docx":
        raise ValueError(f"Not a .docx file: {src}")

    name_part = "_".join(names)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name_part).strip("_")
    safe = safe or "NONAME"

    out = out_dir / (Path(file_name).stem + ".docx")

    itinerary = build_itinerary(first)

    total_days = len(itinerary)
    total_nights = total_days - 1

    end_date = first + timedelta(days=total_days - 1)

    context = {
        "names": names,
        "route": "HÀ NỘI – BẮC KINH – THƯỢNG HẢI – QUẢNG CHÂU",
        "total_days": total_days,
        "total_nights": total_nights,
        "start_date": first.strftime("%d/%m/%Y"),
        "end_date": end_date.strftime("%d/%m/%Y"),
        "itinerary": itinerary,
    }

    doc = DocxTemplate(str(src))
    doc.render(context)
    doc.save(str(out))

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert_docx_to_pdf(str(out), str(pdf_out))
    pdf_helper.remove_last_blank_page(str(pdf_out))

    out.unlink()

    return str(pdf_out)
