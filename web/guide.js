// ---------- "Hướng dẫn file": how to prepare the folder of each visa type (popup, toggles) ----------
// Ảnh ví dụ thật: đặt file vào web/guide/ (vd web/guide/L/ho_khau_goc.jpg) — có file thì thay hình minh hoạ.
// Ảnh ở đây ai có link cũng xem được: chỉ dùng ảnh mẫu / đã che thông tin.
// Loaded before the page script and used at load time: has its own esc() (same as the one in index.html).
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
const SVG_STYLE = 'font-family:system-ui,sans-serif';
const svgLines = (x, y, n, w, gap = 11) => Array.from({ length: n }, (_, i) =>
  `<rect x="${x}" y="${y + i * gap}" width="${w * (i % 3 === 2 ? .6 : 1)}" height="5" rx="2.5" fill="var(--line)"/>`).join('');
function mockPerson(x, y, w, name, role, hi) {
  return `<g><rect x="${x}" y="${y}" width="${w}" height="62" rx="6" fill="${hi ? 'var(--ok-bg)' : 'var(--card)'}" stroke="${hi ? 'var(--ok)' : 'var(--line)'}" stroke-width="${hi ? 2.5 : 1}"/>
    <rect x="${x + 8}" y="${y + 8}" width="34" height="46" rx="3" fill="var(--track)"/>
    <text x="${x + 50}" y="${y + 22}" font-size="12" font-weight="700" fill="var(--text)">${esc(name)}</text>
    <text x="${x + 50}" y="${y + 37}" font-size="11" fill="var(--muted)">Quan hệ: ${esc(role)}</text>
    ${svgLines(x + 50, y + 44, 1, w - 64)}</g>`;
}
const HOKHAU_PEOPLE = [['NGUYỄN VĂN BA', 'Chủ hộ (bố)'], ['TRẦN THỊ BỐN', 'Vợ chủ hộ (mẹ)'], ['NGUYỄN VĂN A', 'Con (người xin visa)'],
                       ['LÊ THỊ C', 'Con dâu (vợ)'], ['NGUYỄN VĂN D', 'Cháu (con)'], ['NGUYỄN THỊ E', 'Cháu (con)']];
function mockHokhau() {
  const rows = HOKHAU_PEOPLE.map(([n, r], i) => mockPerson(14, 46 + i * 70, 272, n, r, false)).join('');
  return `<svg viewBox="0 0 300 480" style="${SVG_STYLE}" role="img" aria-label="Ảnh gốc: một trang có nhiều người">
    <rect x="1" y="1" width="298" height="478" rx="8" fill="var(--bg)" stroke="var(--line)"/>
    <text x="150" y="28" font-size="14" font-weight="700" text-anchor="middle" fill="var(--text)">SỔ HỘ KHẨU / XÁC NHẬN CƯ TRÚ</text>
    ${rows}</svg>`;
}
function mockPiece(i) {
  const [n, r] = HOKHAU_PEOPLE[i];
  return `<svg viewBox="0 0 300 78" style="${SVG_STYLE}" role="img" aria-label="${esc(n)}"><rect width="300" height="78" fill="var(--bg)"/>${mockPerson(8, 8, 284, n, r, true)}</svg>`;
}
function mockDoc(kind) {
  const paper = (inner, h) => `<svg viewBox="0 0 160 ${h}" style="${SVG_STYLE}" role="img"><rect x="1" y="1" width="158" height="${h - 2}" rx="6" fill="var(--bg)" stroke="var(--line)"/>${inner}</svg>`;
  if (kind === 'passport') return paper(`<rect x="10" y="12" width="140" height="10" rx="3" fill="var(--accent)" opacity=".5"/>
    <rect x="10" y="32" width="44" height="58" rx="3" fill="var(--track)"/><circle cx="32" cy="52" r="10" fill="var(--line)"/><rect x="18" y="66" width="28" height="20" rx="10" fill="var(--line)"/>
    ${svgLines(62, 34, 5, 86)}<rect x="10" y="100" width="140" height="22" rx="3" fill="var(--track)"/>
    <text x="80" y="115" font-size="8" text-anchor="middle" fill="var(--muted)" font-family="monospace">P&lt;VNMNGUYEN&lt;&lt;VAN&lt;A&lt;&lt;&lt;</text>`, 132);
  if (kind === 'photo') return paper(`<rect x="30" y="16" width="100" height="130" rx="4" fill="#fff" stroke="var(--line)"/>
    <circle cx="80" cy="62" r="24" fill="#c9ced8"/><rect x="44" y="92" width="72" height="54" rx="30" fill="#c9ced8"/>
    <text x="80" y="166" font-size="10" text-anchor="middle" fill="var(--muted)">4x6 · nền trắng</text>`, 180);
  if (kind === 'visa') return paper(`<rect x="10" y="12" width="140" height="92" rx="5" fill="var(--ok-bg)" stroke="var(--ok)"/>
    <rect x="18" y="24" width="34" height="44" rx="3" fill="var(--track)"/>${svgLines(60, 26, 5, 80)}
    <text x="80" y="96" font-size="10" text-anchor="middle" fill="var(--ok)" font-weight="700">VISA</text>`, 116);
  if (kind === 'blank') return paper(`<text x="80" y="20" font-size="9" text-anchor="middle" fill="var(--muted)">VISAS / THỊ THỰC</text><rect x="12" y="28" width="136" height="92" rx="3" fill="none" stroke="var(--line)" stroke-dasharray="4 3"/><text x="150" y="128" font-size="8" text-anchor="end" fill="var(--muted)">12</text>`, 134);
  return paper(`<text x="80" y="24" font-size="10" font-weight="700" text-anchor="middle" fill="var(--text)">CỘNG HOÀ XHCN VIỆT NAM</text>
    ${svgLines(16, 40, 9, 128, 13)}<circle cx="122" cy="172" r="14" fill="none" stroke="var(--err)" stroke-width="2"/>`, 200);
}
// one example picture: the drawn example now, the real photo from web/guide/<img> once it loads
const gimg = (img, svg, name, hint) =>
  `<figure class="gimg" ${img ? `data-img="${esc(img)}"` : ''}>${svg}<figcaption>${esc(name)}${hint ? `<span class="hint">${esc(hint)}</span>` : ''}</figcaption></figure>`;

// Tên file: chỉ chữ không dấu, số, "_" hoặc "-" (a-z A-Z 0-9).
// File cơ bản: giữ tên gốc (AI tự đọc ra là giấy gì). File người thân / đi cùng / dưới 18
// (tt_cha, tt_me, vo_chong, con_N, cv_N, duoi18_…) phải đặt ĐÚNG tên vì hệ thống nhận diện theo tên.
const NORTH_HOUSES = ['HAI', 'PHONG'];   // miền Bắc: thêm trang trắng hộ chiếu
// [tên file, là ai so với người xin visa, người trong hình minh hoạ]
const FAMILY_FILES = [
  ['tt_cha', 'Bố (cha) của người xin visa', 0],
  ['tt_me', 'Mẹ của người xin visa', 1],
  ['vo_chong', 'Vợ hoặc chồng', 3],
  ['con_1', 'Con thứ nhất (con lớn nhất)', 4],
  ['con_2', 'Con thứ hai; con thứ ba là con_3…', 5],
];
// [ví dụ tên, hình minh hoạ, giấy tờ, ghi chú, bắt buộc?(house) ]
const BASIC_L = [
  ['hochieu', 'passport', 'Trang thông tin hộ chiếu', 'Chụp/scan thẳng, đủ 4 góc, rõ dòng mã ở chân trang, không loá.', () => true],
  ['anhthe', 'photo', 'Ảnh thẻ 4x6 nền trắng', 'Ảnh mới, nhìn thẳng, không đeo kính.', () => true],
  ['trangtrang_1', 'blank', 'Trang trắng hộ chiếu (2 trang)', 'Chỉ nhà HAI, PHONG (miền Bắc). Nhà khác không cần.', (h) => NORTH_HOUSES.includes(h)],
  ['ct07_1', 'doc', 'Xác nhận cư trú CT07 / xác nhận việc làm', 'Nếu có. Nhiều trang thì đánh số theo thứ tự trang.', () => false],
  ['visacu_1', 'visa', 'Visa Trung Quốc cũ', 'Nếu có. Mỗi visa 1 file.', () => false],
];
// short meaning shown next to the file in the folder trees
const U18_SHORT = { duoi18_ks: 'giấy khai sinh', duoi18_dc1: 'người đi cùng 1 (vd bố)', duoi18_dc2: 'người đi cùng 2 (vd mẹ)', duoi18_pay: 'người trả tiền chuyến đi' };
const u18Tree = () => U18_FILES.map(([n]) => (n + '.jpg').padEnd(22) + `<span class="hint">${U18_SHORT[n]} (dưới 18) — đổi về đúng tên như hướng dẫn</span>`);
const U18_FILES = [
  ['duoi18_ks', 'Giấy khai sinh của người xin visa'],
  ['duoi18_dc1', 'Thông tin người đi cùng thứ 1 (vd bố)'],
  ['duoi18_dc2', 'Thông tin người đi cùng thứ 2 (vd mẹ)'],
  ['duoi18_pay', 'Thông tin người sẽ thanh toán chuyến đi'],
];
const nameRule = '<p><b>Giữ tên gốc của file</b>, không cần đổi tên — AI tự đọc ra đó là giấy gì. Chỉ cần tên là chữ không dấu, số, <code>_</code> hoặc <code>-</code> (vd <code>IMG_2041.jpg</code>, <code>scan-01.png</code>). Tên có dấu cách / dấu tiếng Việt thì đổi lại cho không dấu.</p>';
// Folder tree lines -> text with ├── / └── and a "Xem" example button after the file name column.
// The example of a file without a fixed name (basic files) is picked by the sample name used in the tree.
const TREE_EX = { IMG_2041: 'hochieu', IMG_2042: 'anhthe', scan_01: 'trangtrang', scan_02: 'trangtrang', ct07: 'ct07', visa2023: 'visacu' };
function treeLines(lines) {
  return lines.map((l, i) => {
    const m = l.match(/^(\S+?)(\.[a-z0-9]+)(\s*)(<span class="hint">)(.*)$/i);
    let line = l;
    if (m) {
      const stem = m[1];
      const key = TREE_EX[stem] || exKey(stem.replace(/_goc$/, ''));
      const what = m[5].replace(/<[^>]+>/g, '').split(' — ')[0];
      const btn = `<button type="button" class="secondary exbtn extree" title="Xem ảnh ví dụ" data-ex="${esc(key)}" data-name="${esc(stem)}" data-what="${esc(what)}">🖼 Xem</button>`;
      line = (m[1] + m[2]).padEnd(22) + btn + m[4] + m[5];
    }
    return (i === lines.length - 1 ? '└── ' : '├── ') + line;
  }).join('\n');
}
// two kinds of names, shown at the top of the guide
const nameKinds = `<div class="tbl-wrap" style="margin-top:10px"><table class="data">
  <tr><th>Loại file</th><th>Tên file</th></tr>
  <tr><td>File cơ bản: hộ chiếu, ảnh thẻ, trang trắng, CT07, visa cũ</td><td><b>Không cần đổi tên</b> — chỉ cần tên tiếng Anh, không dấu (a-z A-Z 0-9 _ -). AI tự nhận ra.</td></tr>
  <tr><td>Người thân cắt từ hộ khẩu, người đi cùng, giấy tờ dưới 18</td><td><b>Đổi về đúng tên như hướng dẫn</b>: <code>tt_cha</code>, <code>tt_me</code>, <code>vo_chong</code>, <code>con_1</code>, <code>cv_1</code>, <code>duoi18_ks</code>…</td></tr>
</table></div>`;
// Ảnh ví dụ: web/guide/vd/<key>/ (admin thả ảnh vào, server liệt kê). key = tên file bỏ số cuối,
// trừ các file mà mỗi số là 1 giấy khác nhau (mặt trước / mặt sau).
const EX_KEEP_NUM = ['qmoi_1', 'qmoi_2', 'qmoi_3', 'smoi_1', 'smoi_2', 'smoi_3'];
// con_N -> con_cai: Windows does not allow a folder named "con"
const exKey = (n) => (EX_KEEP_NUM.includes(n) ? n : /^con_\d+$/.test(n) ? 'con_cai' : n.replace(/_\d+$/, ''));
const fcell = (n, what, shown = n) => `<span class="fname">${esc(shown)}.jpg</span><button type="button" class="secondary exbtn"
  data-ex="${esc(exKey(n))}" data-name="${esc(shown)}" data-what="${esc(String(what).replace(/<[^>]+>/g, ''))}">🖼 Ảnh ví dụ</button>`;
const fileTable = (rows, head = 'Là gì') => `<div class="tbl-wrap"><table class="data"><tr><th>Tên file</th><th>${head}</th></tr>
  ${rows.map(([n, what]) => `<tr><td>${fcell(n, what)}</td><td>${what}</td></tr>`).join('')}</table></div>`;

// opt = { kind: 'canhan' | 'giadinh', order: 'dau' | 'sau', u18: bool }, house = Nhà đang chọn
const GUIDES = {
  L: {
    title: 'Visa L (du lịch) — chuẩn bị file',
    intro: 'Mỗi hồ sơ là 1 thư mục trên máy, đặt tên kiểu "L30 - NGUYEN VAN A". Kéo cả thư mục vào ô gần cuối form. Đuôi file giữ nguyên (.jpg, .png, .pdf).',
    options: true,
    sections: [
      { id: 'tree', title: 'Thư mục hoàn chỉnh trông như thế nào', hint: 'xem nhanh', open: true, html: (o, h) => {
        const lines = ['IMG_2041.jpg          <span class="hint">hộ chiếu — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'IMG_2042.jpg          <span class="hint">ảnh thẻ — không cần đổi tên (tên tiếng Anh, không dấu)</span>'];
        if (NORTH_HOUSES.includes(h)) lines.push('scan_01.jpg           <span class="hint">trang trắng — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'scan_02.jpg           <span class="hint">trang trắng — không cần đổi tên (tên tiếng Anh, không dấu)</span>');
        lines.push('ct07.pdf              <span class="hint">CT07, nếu có — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'visa2023.jpg          <span class="hint">visa cũ, nếu có — không cần đổi tên (tên tiếng Anh, không dấu)</span>',
                   'tt_cha.jpg            <span class="hint">bố — cắt từ hộ khẩu, nếu có — đổi về đúng tên như hướng dẫn</span>', 'tt_me.jpg             <span class="hint">mẹ — cắt từ hộ khẩu, nếu có — đổi về đúng tên như hướng dẫn</span>');
        if (o.kind === 'giadinh') lines.push('cv_1.jpg              <span class="hint">hộ chiếu người đi cùng 1 — đổi về đúng tên như hướng dẫn</span>', 'cv_2.jpg              <span class="hint">hộ chiếu người đi cùng 2 — đổi về đúng tên như hướng dẫn</span>');
        if (o.u18) lines.push(...u18Tree());
        const tree = treeLines(lines);
        return `<p>Theo lựa chọn ở trên (nhà ${esc(h)}), thư mục hồ sơ có dạng:</p>
          <div class="gtree">L30 - NGUYEN VAN A/\n${tree}</div>
          <p class="hint">Không có giấy tờ nào thì bỏ qua, không tạo file trống.</p>${nameKinds}`;
      } },
      { id: 'basic', title: 'File cơ bản', hint: 'hộ chiếu + ảnh thẻ bắt buộc', html: (o, h) => nameRule + BASIC_L.map(([name, kind, what, note, need]) => `
        <div class="gbasic">${gimg(`L/${name}.jpg`, mockDoc(kind), what, 'không cần đổi tên')}
          <div><b>${esc(what)} <span class="st ${need(h) ? 'approved' : ''}">${need(h) ? 'bắt buộc' : 'nếu có'}</span></b><p>${esc(note)}</p></div></div>`).join('') },
      { id: 'family', title: 'Gia đình: file người đi cùng (cv_)', hint: 'đi theo gia đình', when: (o) => o.kind === 'giadinh', html: (o) => `
        <p>Mỗi người đi cùng 1 file, tên <b>bắt buộc</b> bắt đầu bằng <code>cv_</code> rồi đánh số: <code>cv_1</code>, <code>cv_2</code>…</p>
        <p>Ví dụ đi cùng bố mẹ: thêm <code>cv_1</code> (bố) và <code>cv_2</code> (mẹ).</p>
        ${fileTable([['cv_1', 'Người đi cùng thứ 1 (vd bố)'], ['cv_2', 'Người đi cùng thứ 2 (vd mẹ)'], ['cv_3', 'Người thứ 3… (nếu có)']])}
        <p class="hint">Bạn đang chọn: <b>${o.order === 'dau' ? 'người đầu' : 'người sau'}</b> trong gia đình. Hiện người đầu và người sau chuẩn bị giống nhau.</p>` },
      { id: 'u18', title: 'Người xin visa dưới 18 tuổi', hint: 'bắt buộc nếu dưới 18', when: (o) => o.u18, html: () => `
        ${fileTable(U18_FILES.map(([n, w]) => [n, esc(w)]))}
        <div class="msg err" style="margin-top:12px">Chỉ đi cùng <b>1</b> người: thay 1 trong 2 file <code>duoi18_dc</code> bằng <b>giấy uỷ quyền của người còn lại</b>.<br>
          Vd đi cùng bố: <code>duoi18_dc1</code> = thông tin bố, <code>duoi18_dc2</code> = giấy uỷ quyền của mẹ.</div>` },
      { id: 'hokhau', title: 'Hộ khẩu / giấy tờ có nhiều người → cắt từng người', hint: 'nếu có · đặt đúng tên', html: () => `
        <p>Ảnh hộ khẩu hay xác nhận cư trú thường có <b>nhiều người trên 1 trang</b>. Cắt ra <b>mỗi người thân 1 file</b> và <b>đặt đúng tên</b> trong bảng dưới (khác file cơ bản: ở đây hệ thống dựa vào tên để biết là ai). Tên theo quan hệ <b>với người xin visa</b>, không phải với chủ hộ.</p>
        <ul><li>Cắt đủ khung của người đó: ảnh (nếu có), họ tên, ngày sinh, quan hệ.</li>
            <li>Phần của chính người xin visa: không cần cắt riêng.</li>
            <li>Cắt xong thì bỏ ảnh gốc ra khỏi thư mục (tránh tải trùng).</li></ul>
        <div class="gflow">
          <div><div class="gcap">Ảnh cũ (gốc)</div>${gimg('L/ho_khau_goc.jpg', mockHokhau(), 'hokhau.jpg', 'bỏ ra khỏi thư mục sau khi cắt')}</div>
          <div class="garrow" aria-hidden="true">➜</div>
          <div><div class="gcap">Ảnh mới (đã cắt + đổi tên)</div><div class="gout">
            ${FAMILY_FILES.map(([n, what, i]) => gimg(`L/${n}.jpg`, mockPiece(i), n + '.jpg', what)).join('')}
          </div></div>
        </div>
        ${fileTable(FAMILY_FILES.map(([n, w]) => [n, esc(w)]), 'Là ai (so với người xin visa)')}
        <p class="hint">Con đánh số theo tuổi: con_1 lớn nhất. Một người có 2 ảnh thì thêm số: tt_cha_1, tt_cha_2.</p>` },
      { id: 'err', title: 'Lỗi hay gặp', hint: 'kiểm tra trước khi Gửi', html: () => `
        <ul><li>Tên file có dấu cách hoặc dấu tiếng Việt (<code>ảnh hộ chiếu.jpg</code>) → đổi sang không dấu, không cách.</li>
            <li>File người thân / đi cùng / dưới 18 đặt sai tên (<code>bo.jpg</code>, <code>cv1.jpg</code>, <code>ks.jpg</code>) → phải đúng <code>tt_cha</code>, <code>cv_1</code>, <code>duoi18_ks</code>…</li>
            <li>Ảnh nghiêng, mất góc, loá đèn → chụp lại.</li>
            <li>Để cả ảnh gốc hộ khẩu lẫn ảnh đã cắt → xoá ảnh gốc.</li></ul>` },
    ],
  },
};

// M: company files. [tên file, giấy gì, của ai / từ đâu, cần khi nào]
const M_FILES = [
  ['thumoi', 'Thư mời của công ty Trung Quốc', 'công ty TQ mời người VN sang', 'luôn cần'],
  ['dktq', 'Đăng ký kinh doanh của công ty Trung Quốc', 'công ty TQ (bên mời)', 'luôn cần'],
  ['dkvn', 'Đăng ký kinh doanh của công ty Việt Nam', 'công ty VN của người đi', 'luôn cần'],
  ['qdct', 'Quyết định cử đi công tác', 'giám đốc công ty VN cử nhân viên sang TQ theo thư mời', 'luôn cần'],
];
// Người đi cùng: hộ chiếu, tên bắt đầu bằng cv_ (n8n WF-04: companion_passport). M, F, X.
const CV_TREE = 'cv_1.jpg              <span class="hint">hộ chiếu người đi cùng 1, nếu có — đổi về đúng tên như hướng dẫn</span>';
const companionSection = { id: 'cv', title: 'Người đi cùng (cv_)', hint: 'nếu có · đặt đúng tên', html: () => `
  <p>Mỗi người đi cùng 1 file <b>trang thông tin hộ chiếu</b>, tên <b>bắt buộc</b> bắt đầu bằng <code>cv_</code> rồi đánh số: <code>cv_1</code>, <code>cv_2</code>…</p>
  ${fileTable([['cv_1', 'Hộ chiếu người đi cùng thứ 1'], ['cv_2', 'Hộ chiếu người đi cùng thứ 2'], ['cv_3', 'Người thứ 3… (nếu có)']])}
  <p class="hint">Đặt sai (<code>cv1.jpg</code>, <code>nguoi di cung.jpg</code>) thì hệ thống không nhận ra đó là người đi cùng.</p>` };
// Đoàn đi cùng công ty / trường: người sau chỉ cần file cơ bản, rồi "Áp dụng M/F" ở lịch sử curl.
const orderSeg = () => `<div><div class="gcap">Trong đoàn là</div>${seg('order', [['dau', 'Người đầu / đi 1 mình'], ['sau', 'Người sau']])}</div>`;
const isNext = (o) => o.order === 'sau';
const groupSection = ({ code, files, what, key, owner }) => ({
  id: 'group', title: `Đi theo đoàn: người sau dùng "Áp dụng ${code}"`, hint: 'người sau chỉ cần file cơ bản', open: true, when: isNext, html: () => `
  <p>Người sau trong đoàn (cùng ${owner} với người đầu) <b>chỉ cần file cơ bản</b> (+ <code>cv_</code>, hộ khẩu nếu có). <b>Không cần</b> ${files}.</p>
  <ol><li>Chạy <b>người đầu</b> trước, đủ file, tới khi chạy curl thành công.</li>
      <li>Người sau: tải thư mục chỉ có file cơ bản → <b>Gửi</b> → chờ có curl.</li>
      <li>Tab <b>Chạy curl</b>: <b>Đọc curl</b> của người sau → ở <b>Lịch sử curl</b> tìm hồ sơ người đầu (gõ số hộ chiếu) → bấm <b>"Áp dụng ${code}"</b> → xem lại các trường được ghi → <b>Chạy</b>.</li></ol>
  <p class="hint">"Áp dụng ${code}" chép ${what} của người đầu, và ghi số hộ chiếu người đầu vào <code>${key}</code> để hệ thống dùng lại giấy tờ ${owner} của người đầu.</p>` });

// ---------- "Thứ tự làm file" (section 2 of every type except L) ----------
const stepsWrap = (intro, items) => `<p>${intro}</p><ol class="gsteps">${items.map((x) => `<li>${x}</li>`).join('')}</ol>`;
// Q1, Q2, S2: invitation papers in this order: moi -> cm -> chuki -> khac (p = 'q' or 's').
const inviteSteps = (p, maxRel, inviterDocs) => ({ id: 'steps', title: 'Thứ tự làm file', hint: `${p}moi → ${p}cm → ${p}chuki → ${p}khac`, open: true, html: (o, h) => {
  const north = NORTH_HOUSES.includes(h);
  const sig = (n) => `<code>${n}_1_goc</code> nếu là chữ ký gốc, không thì <code>${n}_1</code>`;
  return stepsWrap(`Sau khi có file cơ bản, làm giấy tờ phía người mời <b>theo đúng thứ tự dưới đây</b> — làm lần lượt thì không sót, không đặt nhầm tên:`, [
    `<b>${p}moi_ — giấy tờ người mời</b>: ${inviterDocs}.<br>
     ${north ? `<b>Nhà ${esc(h)} (miền Bắc)</b>: chỉ <code>${p}moi_1</code>, <code>${p}moi_2</code> (2 giấy quan trọng nhất). Giấy người mời còn lại → <code>${p}khac_</code>.`
             : `<b>Nhà ${esc(h)} (miền Nam)</b>: <code>${p}moi_1</code> → <code>${p}moi_n</code>, đánh số đúng thứ tự trang.`}`,
    `<b>${p}cm_ — chỉ giấy quan hệ chính giữa 2 người</b>: người mời ↔ người được mời (vd con mời mẹ: giấy khai sinh của con).
     Giấy quan hệ của 1 trong 2 người <b>với người khác</b> (vd đăng ký kết hôn của mẹ với bố) → <code>${p}khac_</code>. Xem thêm mục "Giấy chứng minh quan hệ".
     ${north ? `<br>Miền Bắc chỉ tải ${maxRel} file <code>${p}cm_</code> đầu tiên — giấy quan trọng nhất để số nhỏ.` : ''}`,
    `<b>Chữ ký</b>: ${sig(p + 'chuki')}.${p === 'q' ? `<br>Cần người bảo lãnh (ký thay người mời): ${sig('qbaolanh')}.` : ''}`,
    `<b>${p}khac_ — còn lại</b>: mọi giấy tờ khác${north ? ` (gồm giấy người mời từ tờ thứ 3)` : ''}.<br>
     <span class="hint">Thư mời khách đưa sẵn (đã viết, ký) → <code>${p}thumoi_1</code>, không phải <code>${p}khac_</code>.</span>`,
  ]);
} });
// M, F, X: basic files first, then only the papers special to the type.
const specialSteps = (special, when) => ({ id: 'steps', title: 'Thứ tự làm file', hint: 'file cơ bản → file đặc thù', open: true, when, html: (o, h) => stepsWrap('Làm theo thứ tự:', [
  `<b>File cơ bản</b> (hộ chiếu, ảnh thẻ${NORTH_HOUSES.includes(h) ? ', 2 trang trắng' : ''}, CT07, visa cũ): <b>giữ tên gốc</b>, chỉ cần không dấu.`,
  `<b>Xác định các file đặc thù</b> của loại visa này và <b>đặt đúng tên</b>: ${typeof special === 'function' ? special(o, h) : special}`,
  `<b>Người đi cùng / người thân</b> (nếu có): <code>cv_1</code>, <code>cv_2</code>…; hộ khẩu cắt ra <code>tt_cha</code>, <code>tt_me</code>…`,
]) });

GUIDES.M = {
  title: 'Visa M (thương mại) — chuẩn bị file',
  intro: 'Công ty Trung Quốc mời người Việt Nam sang làm việc. Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "M - NGUYEN VAN A". Ngoài file cơ bản của người đi (như visa L) còn 4 file của 2 công ty.',
  options: () => `<div class="gopts">
    ${orderSeg()}
    <div><div class="gcap">Người được mời là</div>${seg('owner', [['false', 'Nhân viên'], ['true', 'Chủ doanh nghiệp']])}</div>
  </div>`,
  sections: [
    { id: 'tree', title: 'Thư mục hoàn chỉnh trông như thế nào', hint: 'xem nhanh', open: true, html: (o, h) => {
      const lines = ['IMG_2041.jpg          <span class="hint">hộ chiếu — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'IMG_2042.jpg          <span class="hint">ảnh thẻ — không cần đổi tên (tên tiếng Anh, không dấu)</span>'];
      if (NORTH_HOUSES.includes(h)) lines.push('scan_01.jpg           <span class="hint">trang trắng — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'scan_02.jpg           <span class="hint">trang trắng — không cần đổi tên (tên tiếng Anh, không dấu)</span>');
      lines.push('ct07.pdf              <span class="hint">CT07, nếu có — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'tt_cha.jpg            <span class="hint">bố — cắt từ hộ khẩu, nếu có — đổi về đúng tên như hướng dẫn</span>', CV_TREE);
      if (!isNext(o)) {
        lines.push('thumoi.jpg            <span class="hint">thư mời của công ty TQ — đổi về đúng tên như hướng dẫn</span>', 'dktq.jpg              <span class="hint">đăng ký kinh doanh công ty TQ — đổi về đúng tên như hướng dẫn</span>',
                   'dkvn.jpg              <span class="hint">đăng ký kinh doanh công ty VN — đổi về đúng tên như hướng dẫn</span>');
        lines.push(o.owner ? 'qdct.jpg              <span class="hint">BẢN SAO của thumoi.jpg — đổi về đúng tên như hướng dẫn</span>'
                           : 'qdct.jpg              <span class="hint">quyết định cử đi công tác — đổi về đúng tên như hướng dẫn</span>');
      }
      const tree = treeLines(lines);
      return `<p>Theo lựa chọn ở trên (nhà ${esc(h)}, ${isNext(o) ? '<b>người sau trong đoàn</b>' : o.owner ? '<b>chủ doanh nghiệp</b>' : 'nhân viên'}), thư mục hồ sơ có dạng:</p>
        ${isNext(o) ? '<p class="hint">Người sau: không có 4 file công ty — lấy từ người đầu bằng "Áp dụng M" (mục bên dưới).</p>' : ''}
        <div class="gtree">M - NGUYEN VAN A/\n${tree}</div>
        <p class="hint">Giấy nhiều trang: thêm số, vd <code>dktq_1</code>, <code>dktq_2</code>. Không có giấy tờ nào thì bỏ qua, không tạo file trống.</p>`;
    } },
    specialSteps((o) => `<code>thumoi</code>, <code>dktq</code> (bên Trung Quốc), <code>dkvn</code>, <code>qdct</code> (bên Việt Nam).${o.owner
      ? '<br><b>Chủ doanh nghiệp</b>: không có quyết định công tác → chép <code>thumoi</code> thành <code>qdct</code> (xem mục "Người được mời là chủ doanh nghiệp").'
      : '<br><span class="hint">Mời giám đốc / chủ doanh nghiệp: chọn "Chủ doanh nghiệp" ở trên để xem cách làm.</span>'}`, (o) => !isNext(o)),
    groupSection({ code: 'M', files: '4 file công ty (<code>thumoi</code>, <code>dktq</code>, <code>dkvn</code>, <code>qdct</code>)',
      what: 'thông tin công ty Trung Quốc / Việt Nam và ngày đi / về', key: 'company_passport', owner: 'công ty' }),
    { id: 'company', title: 'Giấy tờ của 2 công ty', hint: 'đặt đúng tên', open: true, when: (o) => !isNext(o), html: (o) => `
      <p>4 file này <b>phải đặt đúng tên</b> (hệ thống dựa vào tên để biết là giấy gì):</p>
      <div class="tbl-wrap"><table class="data"><tr><th>Tên file</th><th>Giấy gì</th><th>Của ai / từ đâu</th><th>Cần khi nào</th></tr>
        ${M_FILES.map(([n, what, who, when]) => {
          const copy = o.owner && n === 'qdct';
          return `<tr><td>${fcell(n, what)}</td><td>${copy ? 'Bản sao của <code>thumoi</code>' : esc(what)}</td>
            <td>${copy ? 'chủ doanh nghiệp không có quyết định công tác' : esc(who)}</td>
            <td><span class="st approved">${copy ? 'chép từ thumoi' : esc(when)}</span></td></tr>`;
        }).join('')}
      </table></div>
      <ul><li>2 file của bên Trung Quốc: <code>thumoi</code>, <code>dktq</code>. 2 file của bên Việt Nam: <code>dkvn</code>, <code>qdct</code>.</li>
          <li>Hệ thống đọc tên, địa chỉ, điện thoại công ty TQ và ngày đi / về từ <b>quyết định công tác</b> (<code>qdct</code>); đọc công ty VN và người đại diện từ <code>dkvn</code>. <code>thumoi</code>, <code>dktq</code> chỉ được tải lên, không đọc nội dung.</li></ul>` },
    { id: 'owner', title: 'Người được mời là chủ doanh nghiệp', hint: 'không có qdct · 2 việc phải tự làm', when: (o) => o.owner && !isNext(o), open: true, html: () => `
      <p>Chủ doanh nghiệp không tự ra quyết định cử chính mình đi, nên <b>không có quyết định công tác</b>. Làm 2 việc sau:</p>
      <ol><li><b>Trước khi tải thư mục lên:</b> chép file <code>thumoi</code> thành thêm 1 file tên <code>qdct</code> (cùng nội dung, vd <code>thumoi.jpg</code> → thêm <code>qdct.jpg</code>; nhiều trang thì chép cả: <code>qdct_1</code>, <code>qdct_2</code>…).
            Hệ thống đọc công ty Trung Quốc và ngày đi / về từ file <code>qdct</code>, nên phải có file này.</li>
          <li><b>Sau khi chạy xong (curl / Chạy):</b> vào hồ sơ trên trang visa, mục tải giấy tờ, ô <b>"Quyết định công tác"</b>: xoá file đang có (là thư mời) và tải lên file <b>đăng ký kinh doanh VN</b> (<code>dkvn</code>) để chứng minh người đi là chủ doanh nghiệp.</li></ol>
      <p class="hint">Tên người đi phải trùng tên <b>người đại diện</b> trên <code>dkvn</code>.</p>` },
    companionSection,
    { ...GUIDES.L.sections.find((x) => x.id === 'basic') },
    { ...GUIDES.L.sections.find((x) => x.id === 'hokhau') },
    { id: 'err', title: 'Lỗi hay gặp', hint: 'kiểm tra trước khi Gửi', html: (o) => `
      <ul>${isNext(o) ? '<li>Người sau quên bấm "Áp dụng M" trước khi Chạy → hồ sơ thiếu thông tin công ty.</li>' : ''}
          <li>4 file công ty đặt sai tên (<code>dang ky kinh doanh.jpg</code>, <code>thu moi TQ.pdf</code>) → phải đúng <code>dkvn</code>, <code>dktq</code>, <code>thumoi</code>, <code>qdct</code>.</li>
          <li>Lẫn 2 bản đăng ký: <code>dktq</code> là công ty <b>Trung Quốc</b> (bên mời), <code>dkvn</code> là công ty <b>Việt Nam</b> (bên đi).</li>
          ${o.owner ? '<li>Chủ doanh nghiệp mà quên chép <code>thumoi</code> thành <code>qdct</code> → hồ sơ thiếu công ty TQ và ngày đi.</li><li>Chạy xong quên thay ô "Quyết định công tác" bằng <code>dkvn</code> trên trang visa.</li>'
                    : '<li>Thiếu <code>qdct</code> → hồ sơ thiếu công ty TQ và ngày đi.</li>'}
          <li>Tên file có dấu cách hoặc dấu tiếng Việt → đổi sang không dấu, không cách.</li>
          <li>Ảnh nghiêng, mất góc, loá đèn → chụp lại.</li></ul>` },
  ],
};

// ---------- guides F, X1, X2, Q1, Q2, S2 (from the n8n naming rules: WF-04, WF-04D, WF-04I) ----------
// file row: [tên ví dụ, giấy gì, của ai / từ đâu, cần khi nào, hệ thống làm gì]
// WF-04: qchuki_ / qbaolanh_ / qbl_ / schuki_ ending in _goc -> keep the original strokes (white background + resize only)
const isSign = (n) => /^(qchuki|qbaolanh|qbl|schuki)_/.test(n);
const sigName = (n, o) => (o.goc && isSign(n) ? n + '_goc' : n);
const READ = (what) => `<span class="st approved">đọc: ${esc(what)}</span>`;
const UPLOAD_ONLY = '<span class="st">chỉ tải lên</span>';
function typeGuide({ code, title, intro, docs, docsNote = '', extra = [], errors = [], group = null, companions = false, u18 = false, sign = false, steps = null }) {
  const next = (o) => !!group && isNext(o);
  const u18Seg = () => `<div><div class="gcap">Tuổi người xin visa</div>${seg('u18', [['false', 'Từ 18 tuổi'], ['true', 'Dưới 18 tuổi']])}</div>`;
  const signSeg = () => `<div><div class="gcap">Chữ ký người mời</div>${seg('goc', [['false', 'Vẽ lại nét'], ['true', 'Chữ ký gốc (_goc)']])}</div>`;
  return {
    title, intro,
    options: group || u18 || sign ? () => `<div class="gopts">${group ? orderSeg() : ''}${u18 ? u18Seg() : ''}${sign ? signSeg() : ''}</div>` : undefined,
    sections: [
      { id: 'tree', title: 'Thư mục hoàn chỉnh trông như thế nào', hint: 'xem nhanh', open: true, html: (o, h) => {
        const lines = ['IMG_2041.jpg          <span class="hint">hộ chiếu — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'IMG_2042.jpg          <span class="hint">ảnh thẻ — không cần đổi tên (tên tiếng Anh, không dấu)</span>'];
        if (NORTH_HOUSES.includes(h)) lines.push('scan_01.jpg           <span class="hint">trang trắng — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'scan_02.jpg           <span class="hint">trang trắng — không cần đổi tên (tên tiếng Anh, không dấu)</span>');
        lines.push('ct07.pdf              <span class="hint">CT07, nếu có — không cần đổi tên (tên tiếng Anh, không dấu)</span>', 'tt_cha.jpg            <span class="hint">bố — cắt từ hộ khẩu, nếu có — đổi về đúng tên như hướng dẫn</span>');
        if (companions) lines.push(CV_TREE);
        if (u18 && o.u18) lines.push(...u18Tree());
        // short label in the tree: the part before "(" or ":"
        // North: inviter papers from the 3rd one go to qkhac_ / skhac_, so no qmoi_3 / smoi_3 line
        if (!next(o)) docs.filter(([n]) => !(NORTH_HOUSES.includes(h) && /^[qs]moi_3$/.test(n))).forEach(([n, what, , , , short]) => lines.push(`${(sigName(n, o) + '.jpg').padEnd(22)}<span class="hint">${esc((short || what.split(/[(:]/)[0].trim()).replace(/^./, (c) => c.toLowerCase()))} — đổi về đúng tên như hướng dẫn</span>`));
        const tree = treeLines(lines);
        return `<p>Nhà ${esc(h)}${next(o) ? ', <b>người sau trong đoàn</b>' : ''}, thư mục hồ sơ có dạng:</p>
          ${next(o) ? `<p class="hint">Người sau: không có giấy tờ riêng của ${esc(code)} — lấy từ người đầu bằng "Áp dụng ${esc(group.code)}" (mục bên dưới).</p>` : ''}
          <div class="gtree">${esc(code)} - NGUYEN VAN A/\n${tree}</div>
          <p class="hint">Giấy nhiều trang / nhiều tờ: tăng số cuối (<code>_1</code>, <code>_2</code>…). Không có giấy tờ nào thì bỏ qua, không tạo file trống.</p>`;
      } },
      ...(steps ? [steps.id ? steps : specialSteps(steps, (o) => !next(o))] : []),
      ...(group ? [groupSection(group)] : []),
      { id: 'docs', title: `Giấy tờ riêng của visa ${code}`, hint: 'tên phải bắt đầu đúng tiền tố', open: true, when: (o) => !next(o), html: (o, h) => `
        <p>Các file này <b>phải bắt đầu bằng đúng tiền tố</b> trong bảng (hệ thống dựa vào tiền tố để biết là giấy gì), sau đó là số thứ tự.</p>
        <div class="tbl-wrap"><table class="data"><tr><th>Tên file</th><th>Giấy gì</th><th>Của ai / từ đâu</th><th>Cần</th><th>Hệ thống</th></tr>
          ${docs.map(([n, what, who, need, sys]) => `<tr><td>${fcell(n, what, sigName(n, o))}</td><td>${esc(what)}</td><td>${esc(who)}</td>
            <td><span class="st ${need === 'bắt buộc' ? 'approved' : ''}">${esc(need)}</span></td><td>${sys}</td></tr>`).join('')}
        </table></div>${typeof docsNote === 'function' ? docsNote(o, h) : docsNote}` },
      ...extra,
      ...(companions ? [companionSection] : []),
      ...(u18 ? [{ ...GUIDES.L.sections.find((x) => x.id === 'u18'), open: true }] : []),
      { ...GUIDES.L.sections.find((x) => x.id === 'basic') },
      { ...GUIDES.L.sections.find((x) => x.id === 'hokhau') },
      { id: 'err', title: 'Lỗi hay gặp', hint: 'kiểm tra trước khi Gửi', html: (o) => `
        <ul>${next(o) ? `<li>Người sau quên bấm "Áp dụng ${esc(group.code)}" trước khi Chạy → hồ sơ thiếu thông tin ${esc(group.owner)}.</li>` : ''}
            ${errors.map((e) => `<li>${e}</li>`).join('')}
            <li>Tên file có dấu cách hoặc dấu tiếng Việt → đổi sang không dấu, không cách.</li>
            <li>Ảnh nghiêng, mất góc, loá đèn → chụp lại.</li></ul>` },
    ],
  };
}

GUIDES.F = typeGuide({
  code: 'F', title: 'Visa F (trao đổi / học ngắn hạn) — chuẩn bị file',
  intro: 'Trường / đơn vị bên Trung Quốc mời sang học, trao đổi ngắn hạn. Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "F - NGUYEN VAN A". Ngoài file cơ bản của người đi (như visa L) còn 2 loại giấy của trường.',
  docs: [
    ['fthumoi_1', 'Thư mời / giấy tiếp nhận của trường Trung Quốc', 'trường bên Trung Quốc (bên mời)', 'bắt buộc', READ('tên trường, địa chỉ, ngày đến / đi')],
    ['fqddh_1', 'Quyết định cử đi học', 'trường Việt Nam của người đi', 'bắt buộc', READ('tên trường VN, bậc học, ngành')],
  ],
  docsNote: `<ul><li><code>fthumoi</code> là trường <b>bên mời</b> (Trung Quốc); <code>fqddh</code> là trường <b>của người đi</b> (Việt Nam). Không lẫn 2 loại.</li>
      <li>Cả đoàn cùng 1 trường: chỉ người đầu cần 2 file này — chọn "Người sau" ở trên để xem cách làm cho người sau.</li></ul>`,
  group: { code: 'F', files: '2 file trường (<code>fthumoi</code>, <code>fqddh</code>)',
           what: 'thông tin trường mời, ngày học và học vấn', key: 'school_passport', owner: 'trường' },
  companions: true, steps: '<code>fthumoi_</code> (thư mời của trường Trung Quốc), <code>fqddh_</code> (quyết định cử đi học của trường Việt Nam).',
  errors: ['Đặt thư mời tên <code>thumoi</code> (của visa M / Q) thay vì <code>fthumoi</code> → hệ thống không nhận là giấy của trường.',
           'Đảo 2 loại: <code>fthumoi</code> = trường Trung Quốc, <code>fqddh</code> = trường Việt Nam.'],
});

const xDocs = [
  ['xnh_1', 'Giấy báo nhập học (录取通知书)', 'trường Trung Quốc', 'bắt buộc', READ('tên trường, địa chỉ, ngày nhập học / kết thúc')],
  ['xjw_1', 'Mẫu JW201 / JW202', 'trường Trung Quốc', 'bắt buộc', READ('tên trường, ngày học (bổ sung khi giấy báo thiếu)')],
];
const xNote = (code) => `<ul><li>Hệ thống ưu tiên thông tin trên <code>xnh</code>, thiếu mới lấy từ <code>xjw</code>.</li>
    <li>${code === 'X1' ? 'X1: thời gian học <b>trên 180 ngày</b>.' : 'X2: thời gian học <b>tối đa 180 ngày</b>.'} Giấy tờ ghi thời gian không khớp loại visa thì hệ thống cảnh báo (vd X2 mà học 1 năm → phải là X1).</li></ul>`;
const xSteps = '<code>xnh_</code> (giấy báo nhập học), <code>xjw_</code> (mẫu JW201 / JW202) — cả 2 của trường Trung Quốc.';
GUIDES.X1 = typeGuide({
  code: 'X1', title: 'Visa X1 (du học dài hạn, trên 180 ngày) — chuẩn bị file',
  intro: 'Du học tại Trung Quốc trên 180 ngày. Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "X1 - NGUYEN VAN A". Ngoài file cơ bản (như visa L) còn 2 giấy của trường.',
  docs: xDocs, docsNote: xNote('X1'), companions: true, steps: xSteps,
  errors: ['Thiếu tiền tố (<code>giay bao nhap hoc.jpg</code>, <code>JW202.pdf</code>) → phải là <code>xnh_1</code>, <code>xjw_1</code>.',
           'Thời gian học ≤ 180 ngày mà chọn X1 → đổi sang X2.'],
});
GUIDES.X2 = typeGuide({
  code: 'X2', title: 'Visa X2 (du học ngắn hạn, tối đa 180 ngày) — chuẩn bị file',
  intro: 'Du học tại Trung Quốc tối đa 180 ngày. Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "X2 - NGUYEN VAN A". Ngoài file cơ bản (như visa L) còn 2 giấy của trường.',
  docs: xDocs, docsNote: xNote('X2'), companions: true, steps: xSteps,
  errors: ['Thiếu tiền tố (<code>giay bao nhap hoc.jpg</code>, <code>JW202.pdf</code>) → phải là <code>xnh_1</code>, <code>xjw_1</code>.',
           'Thời gian học trên 180 ngày mà chọn X2 → đổi sang X1.'],
});

// Q1 / Q2: thăm người thân là công dân Trung Quốc (thư mời do hệ thống tạo)
const signNote = (o, ex) => o.goc
  ? `<li><b>Chữ ký gốc</b> (đã chọn ở trên): tên file chữ ký có đuôi <code>_goc</code>, vd <code>${ex}_1_goc</code>. Hệ thống <b>giữ nguyên nét</b>, chỉ làm nền trắng và chỉnh cỡ. Dùng khi ảnh chữ ký rõ, nét đẹp.</li>`
  : `<li><b>Vẽ lại nét</b> (đã chọn ở trên): tên file bình thường, vd <code>${ex}_1</code>. Hệ thống làm nền trắng và <b>vẽ lại nét</b> cho đều. Dùng khi ảnh chữ ký mờ, nhoè, chụp nghiêng.</li>`;
// qcm_ / scm_ = the MAIN proof of the relation, which depends on who invites whom; the other relation papers go to qkhac_ / skhac_.
const relSection = (cm, khac) => ({ id: 'rel', title: `Giấy chứng minh quan hệ (${cm}_) theo quan hệ người mời`, hint: `${cm}_ hay ${khac}_`, open: true, html: () => `
  <p><code>${cm}_</code> chỉ chứa <b>giấy chứng minh đúng quan hệ</b> chọn ở ô "Quan hệ" của form. Chỉ giấy quan hệ <b>trực tiếp giữa người mời và người được mời</b>; giấy quan hệ của 1 trong 2 người với người khác đặt <code>${khac}_</code>.</p>
  <div class="tbl-wrap"><table class="data"><tr><th>Quan hệ (ví dụ)</th><th><code>${cm}_1</code>, <code>${cm}_2</code>… là</th><th><code>${khac}_1</code>, <code>${khac}_2</code>… là</th></tr>
    <tr><td><b>Vợ mời chồng</b> / chồng mời vợ</td>
        <td><b>Giấy đăng ký kết hôn</b>: bản Trung Quốc và bản Việt Nam. Bản có đóng dấu thì đưa kèm vào luôn (vd <code>${cm}_1</code> = ĐKKH TQ, <code>${cm}_2</code> = ĐKKH VN, <code>${cm}_3</code> = bản có đóng dấu).</td>
        <td>Giấy tờ khác, nếu có</td></tr>
    <tr><td><b>Con mời mẹ</b> / con mời bố</td>
        <td><b>Giấy khai sinh</b> (của người con, có tên bố / mẹ)</td>
        <td>Giấy đăng ký kết hôn (của bố mẹ) và giấy tờ khác — lúc này ĐKKH <b>không</b> để ở <code>${cm}_</code></td></tr>
    <tr><td>Quan hệ khác</td><td>Giấy chứng minh đúng quan hệ đó</td><td>Các giấy quan hệ còn lại → <code>${khac}_</code></td></tr>
  </table></div>
  <p class="hint">Cùng một giấy (vd ĐKKH) có thể là <code>${cm}_</code> ở hồ sơ này nhưng là <code>${khac}_</code> ở hồ sơ khác — xem quan hệ người mời trước khi đặt tên.</p>` });
const qSign = { id: 'sign', title: 'Chữ ký trên thư mời', hint: 'qchuki_ · qbaolanh_ · _goc', open: true, html: (o) => `
  <p>Thư mời do <b>hệ thống tự tạo</b> từ giấy tờ người mời + quan hệ chọn ở form. Chữ ký đưa vào thư mời:</p>
  <ul>${signNote(o, 'qchuki')}
      <li><code>${sigName('qchuki_1', o)}</code>: chữ ký của <b>người mời</b>.</li>
      <li><code>${sigName('qbaolanh_1', o)}</code> (hoặc <code>${sigName('qbl_1', o)}</code>): chữ ký <b>người bảo lãnh</b> — người ký thay người mời (vd người mời chưa đủ 18 tuổi). Có file này thì hệ thống dùng mẫu thư mời có thêm dòng người bảo lãnh.</li></ul>` };
const qDocs = (maxRel) => [
  ['qmoi_1', 'Giấy tờ người mời: CCCD / hộ khẩu / hộ chiếu Trung Quốc (mặt trước)', 'người mời (công dân TQ)', 'bắt buộc', READ('họ tên, số giấy tờ, địa chỉ, tỉnh / thành / quận'), 'giấy tờ người mời — mặt trước'],
  ['qmoi_2', 'Giấy tờ người mời (mặt sau / trang 2)', 'người mời', 'nếu có', READ('như trên'), 'giấy tờ người mời — mặt sau / trang 2'],
  ['qmoi_3', 'Giấy tờ người mời: trang 3, 4, 5 (qmoi_3 … qmoi_5) — chỉ miền Nam; miền Bắc đặt qkhac_', 'người mời', 'nếu có', READ('như trên'), 'giấy tờ người mời — trang 3 (thêm qmoi_4, qmoi_5 nếu có)'],
  ['qcm_1', `Giấy chứng minh quan hệ — giấy chính theo quan hệ người mời (xem mục bên dưới): qcm_1 … qcm_5`, 'người xin visa ↔ người mời', 'bắt buộc', UPLOAD_ONLY, 'giấy chứng minh quan hệ (thêm qcm_2 … qcm_5 nếu có)'],
  ['qthumoi_1', 'Thư mời khách cung cấp (người mời đã viết, ký sẵn)', 'người mời / khách', 'nếu có', `<span class="st approved">thay thư hệ thống tạo</span>`, 'thư mời khách cung cấp, nếu có'],
  ['qchuki_1', 'Chữ ký người mời (cho thư mời)', 'người mời', 'nên có', READ('làm nền trắng, đưa vào thư mời'), 'chữ ký người mời (cho thư mời)'],
  ['qbaolanh_1', 'Chữ ký người bảo lãnh (ký thay người mời)', 'người bảo lãnh', 'nếu có', READ('đưa vào thư mời mẫu bảo lãnh'), 'chữ ký người bảo lãnh (ký thay người mời)'],
  ['qkhac_1', 'Giấy tờ khác hỗ trợ hồ sơ, gồm giấy quan hệ không phải giấy chính (vd ĐKKH khi con mời mẹ)', '—', 'nếu có', UPLOAD_ONLY, 'giấy tờ khác + giấy quan hệ phụ, nếu có'],
];
// maxRel: North upload slots for qcm_ (Q1: 4, Q2: 3). South merges every file into 1 PDF.
const manyNote = (h, moi, cm, maxRel) => NORTH_HOUSES.includes(h)
  ? `<li>Nhiều trang: <code>${moi}_1</code> … <code>${moi}_5</code>, <code>${cm}_1</code> … <code>${cm}_5</code>. <b>Nhà ${esc(h)} (miền Bắc)</b>: chỉ dùng <code>${moi}_1</code>, <code>${moi}_2</code> — giấy người mời còn lại đặt <code>${moi.replace('moi', 'khac')}_</code>; chỉ tải lên <b>${maxRel} file quan hệ</b> đầu tiên (theo số thứ tự) — để giấy quan trọng nhất ở số nhỏ.</li>`
  : `<li>Nhiều trang: <code>${moi}_1</code> … <code>${moi}_5</code>, <code>${cm}_1</code> … <code>${cm}_5</code>. <b>Nhà ${esc(h)} (miền Nam)</b>: hệ thống gộp tất cả file cùng loại thành 1 PDF theo số thứ tự, nên đánh số đúng thứ tự trang.</li>`;
const qNote = (maxRel) => (o, h) => `<ul><li><b>Bắt buộc chọn "Quan hệ"</b> ở form (người mời là gì của người xin visa). Quan hệ này được in vào thư mời.</li>
    ${manyNote(h, 'qmoi', 'qcm', maxRel)}
    <li>Thư mời: bình thường không cần chuẩn bị — hệ thống tạo từ <code>qmoi</code> + quan hệ + chữ ký.</li>
    <li><code>qthumoi_1</code> (<code>qthumoi_2</code>… nếu nhiều trang): thư mời <b>khách tự cung cấp</b>. Q1, Q2 (cả miền Bắc và miền Nam): có <code>qthumoi</code> thì hệ thống tải lên đúng thư này (gộp các trang thành 1 PDF theo số thứ tự); thư hệ thống tạo vẫn được làm và lưu dự phòng (tên <code>…_backup.pdf</code>). Không có thì dùng thư hệ thống tạo.</li></ul>`;
const signErrors = (p) => [`Chọn chữ ký gốc mà quên đuôi <code>_goc</code> (hoặc ngược lại) → hệ thống xử lý chữ ký sai kiểu. Đuôi phải đặt <b>cuối tên</b>: <code>${p}_1_goc</code>, không phải <code>${p}_goc_1</code>.`];
const qErrors = [...signErrors('qchuki'), 'Con mời mẹ mà để giấy đăng ký kết hôn ở <code>qcm_</code> → <code>qcm_</code> phải là giấy khai sinh, ĐKKH chuyển sang <code>qkhac_</code>.',
                 'Thư mời khách đưa đặt tên <code>thumoi</code> (của visa M) hay <code>sthumoi</code> (của S2) → hồ sơ Q phải là <code>qthumoi_1</code>.',
                 'Đánh số nhảy cóc hoặc sai thứ tự (<code>qmoi_1</code>, <code>qmoi_3</code>, thiếu <code>qmoi_2</code>) → trang bị xếp sai thứ tự.', 'Giấy tờ người mời đặt tên <code>cccd.jpg</code>, <code>nguoi moi.jpg</code> → phải là <code>qmoi_1</code>, <code>qmoi_2</code>.',
                 'Dùng tiền tố của visa S (<code>smoi_</code>, <code>scm_</code>) cho hồ sơ Q → hệ thống xếp nhầm loại.',
                 'Quên chọn "Quan hệ" ở form → không gửi được.'];
GUIDES.Q1 = typeGuide({
  code: 'Q1', title: 'Visa Q1 (đoàn tụ gia đình, trên 180 ngày) — chuẩn bị file',
  intro: 'Sang Trung Quốc đoàn tụ, ở lâu hơn 180 ngày với người thân là công dân Trung Quốc (hoặc người có thường trú TQ). Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "Q1 - NGUYEN VAN A".',
  docs: qDocs(4), docsNote: qNote(4), steps: inviteSteps('q', 4, 'CCCD, visa nhập cảnh Việt Nam, dấu nhập cảnh Việt Nam… của người Trung Quốc đang mời'), extra: [relSection('qcm', 'qkhac'), qSign], errors: qErrors, u18: true, sign: true,
});
GUIDES.Q2 = typeGuide({
  code: 'Q2', title: 'Visa Q2 (thăm thân ngắn hạn, tối đa 180 ngày) — chuẩn bị file',
  intro: 'Thăm người thân là công dân Trung Quốc (hoặc người có thường trú TQ), ở tối đa 180 ngày. Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "Q2 - NGUYEN VAN A".',
  docs: qDocs(3), docsNote: qNote(3), steps: inviteSteps('q', 3, 'CCCD, visa nhập cảnh Việt Nam, dấu nhập cảnh Việt Nam… của người Trung Quốc đang mời'), extra: [relSection('qcm', 'qkhac'), qSign], errors: qErrors, u18: true, sign: true,
});

// S2: thăm người thân là người nước ngoài đang làm việc / học ở Trung Quốc
GUIDES.S2 = typeGuide({
  code: 'S2', title: 'Visa S2 (thăm người thân là người nước ngoài ở TQ) — chuẩn bị file', u18: true,
  intro: 'Thăm người thân là người nước ngoài (vd người Việt) đang làm việc / học / sống ở Trung Quốc. Mỗi hồ sơ là 1 thư mục, đặt tên kiểu "S2 - NGUYEN VAN A".',
  docs: [
    ['smoi_1', 'Giấy tờ người mời: hộ chiếu (trang thông tin)', 'người mời (người đang ở TQ)', 'bắt buộc', READ('họ tên, số giấy tờ, địa chỉ ở TQ'), 'hộ chiếu người mời'],
    ['smoi_2', 'Giấy tờ người mời: giấy cư trú / giấy phép ở TQ', 'người mời', 'bắt buộc', READ('như trên'), 'giấy cư trú ở TQ của người mời'],
    ['smoi_3', 'Giấy tờ người mời: trang 3, 4, 5 (smoi_3 … smoi_5) — chỉ miền Nam; miền Bắc đặt skhac_', 'người mời', 'nếu có', READ('như trên'), 'giấy tờ người mời — trang 3 (thêm smoi_4, smoi_5 nếu có)'],
    ['scm_1', 'Giấy chứng minh quan hệ — giấy chính theo quan hệ người mời (xem mục bên dưới): scm_1 … scm_5', 'người xin visa ↔ người mời', 'bắt buộc', UPLOAD_ONLY, 'giấy chứng minh quan hệ (thêm scm_2 … scm_5 nếu có)'],
    ['sthumoi_1', 'Thư mời khách cung cấp (người mời đã viết, ký sẵn)', 'người mời / khách', 'nếu có', `<span class="st approved">thay thư hệ thống tạo</span>`, 'thư mời khách cung cấp, nếu có'],
    ['smoi_ruot_1', 'Giấy tờ của chính người mời khi giấy smoi_ là của người khác', 'người mời', 'nếu có', READ('giới tính, ngày sinh người mời (cho thư mời)'), 'giấy tờ của chính người mời (khi smoi_ là của người khác)'],
    ['schuki_1', 'Chữ ký (cho thư mời)', '—', 'nên có', READ('làm nền trắng, đưa vào thư mời'), 'chữ ký (cho thư mời)'],
    ['skhac_1', 'Giấy tờ khác hỗ trợ hồ sơ, gồm giấy quan hệ không phải giấy chính (vd ĐKKH khi con mời mẹ)', '—', 'nếu có', UPLOAD_ONLY, 'giấy tờ khác + giấy quan hệ phụ, nếu có'],
  ],
  docsNote: (o, h) => `<ul><li><b>Bắt buộc chọn "Quan hệ"</b> ở form; với S2, "Chồng / Vợ sắp cưới" nằm đầu danh sách.</li>
      ${manyNote(h, 'smoi', 'scm', 3)}
      <li>Thư mời: <code>sthumoi_1</code> là thư <b>khách tự cung cấp</b> — có thì hệ thống tải lên đúng thư đó (cả 2 miền); không có thì hệ thống tự tạo từ mẫu.</li>
      <li><code>smoi_ruot</code>: dùng khi giấy <code>smoi</code> là của người khác (vd chị lấy chồng TQ mời em: <code>smoi</code> = giấy của chồng, <code>smoi_ruot</code> = giấy của chị). Địa chỉ vẫn lấy từ <code>smoi</code>, giới tính + ngày sinh người mời lấy từ <code>smoi_ruot</code>.</li>
</ul>`,
  steps: inviteSteps('s', 3, 'hộ chiếu, giấy cư trú / giấy phép ở Trung Quốc… của người đang ở Trung Quốc mời sang (giấy <code>smoi</code> là của người khác thì thêm <code>smoi_ruot_1</code> — xem bảng)'),
  extra: [relSection('scm', 'skhac'), { id: 'sign', title: 'Chữ ký trên thư mời', hint: 'schuki_ · _goc', open: true, html: (o) => `
    <p>Khi hệ thống tự tạo thư mời (không có <code>sthumoi</code>), chữ ký <code>${sigName('schuki_1', o)}</code> được đưa vào thư mời:</p>
    <ul>${signNote(o, 'schuki')}</ul>` }],
  sign: true,
  errors: [...signErrors('schuki'), 'Con mời mẹ mà để giấy đăng ký kết hôn ở <code>scm_</code> → <code>scm_</code> phải là giấy khai sinh, ĐKKH chuyển sang <code>skhac_</code>.', 'Dùng tiền tố của visa Q (<code>qmoi_</code>, <code>qcm_</code>) cho hồ sơ S2 → hệ thống xếp nhầm loại.',
           'Đặt <code>smoi_ruot</code> thành <code>smoiruot</code> hay <code>smoi_1_ruot</code> → phải bắt đầu đúng <code>smoi_ruot_</code>.',
           'Thư mời đặt tên <code>thumoi</code> (của visa M) hay <code>qthumoi</code> (của Q) → hồ sơ S2 phải là <code>sthumoi_1</code>.',
           'Đánh số nhảy cóc hoặc sai thứ tự (<code>smoi_1</code>, <code>smoi_3</code>, thiếu <code>smoi_2</code>) → trang bị xếp sai thứ tự.'],
});

let guideOpt = { kind: 'canhan', order: 'dau', u18: false, owner: false, goc: false };
const seg = (key, items) => `<div class="seg" role="group">${items.map(([v, label]) =>
  `<button type="button" data-k="${key}" data-v="${v}" class="${String(guideOpt[key]) === v ? 'on' : ''}">${label}</button>`).join('')}</div>`;
function guideOptions() {
  return `<div class="gopts">
    <div><div class="gcap">Hồ sơ</div>${seg('kind', [['canhan', 'Cá nhân'], ['giadinh', 'Gia đình']])}</div>
    ${guideOpt.kind === 'giadinh' ? `<div><div class="gcap">Trong gia đình là</div>${seg('order', [['dau', 'Người đầu'], ['sau', 'Người sau']])}</div>` : ''}
    <div><div class="gcap">Tuổi người xin visa</div>${seg('u18', [['false', 'Từ 18 tuổi'], ['true', 'Dưới 18 tuổi']])}</div>
  </div>`;
}

// ---------- shared by the popup (index.html) and the page /web/huong-dan (guide.html) ----------
const GUIDE_BOOL = ['u18', 'owner', 'goc'];
// After a Cá nhân / Gia đình… button: the section that just appeared opens by itself.
const GUIDE_OPEN_ON = { kind: 'family', u18: 'u18', owner: 'owner', order: 'group', goc: 'sign' };

// The guide of visa `v` for house `house` into `body`, keeping the sections the reader opened.
// Returns the guide (undefined = no guide for that type).
function guideFill(body, v, house) {
  const g = GUIDES[v];
  const wasOpen = new Set([...body.querySelectorAll('details[open]')].map((d) => d.dataset.id));
  const first = !body.childElementCount;
  body.innerHTML = g
    ? `<p class="guide-intro">${esc(g.intro)}</p>` + (g.options ? (typeof g.options === 'function' ? g.options() : guideOptions()) : '') + g.sections
        .filter((s) => !s.when || s.when(guideOpt, house))
        .map((s, i) => `<details data-id="${s.id}"${(first ? s.open : wasOpen.has(s.id) || s.open) ? ' open' : ''}><summary>${i + 1}. ${esc(s.title)}${s.hint ? `<span class="hint">${esc(s.hint)}</span>` : ''}</summary><div class="guide-sec">${s.html(guideOpt, house)}</div></details>`).join('')
    : `<p class="guide-intro">Chưa có hướng dẫn cho loại ${esc(v)}. Hiện có: ${Object.keys(GUIDES).join(', ')}.</p>`;
  // real example photos when web/guide has them (else the drawn example stays)
  body.querySelectorAll('figure[data-img]').forEach((f) => {
    const im = new Image();
    im.alt = f.querySelector('figcaption')?.textContent || '';
    im.onload = () => f.firstElementChild.replaceWith(im);
    im.src = '/web/guide/' + f.dataset.img;
  });
  return g;
}

// A click on an option button (.seg button): update guideOpt, re-render with fill(), open the new section.
function guidePick(b, body, fill) {
  guideOpt[b.dataset.k] = GUIDE_BOOL.includes(b.dataset.k) ? b.dataset.v === 'true' : b.dataset.v;
  fill();
  const id = GUIDE_OPEN_ON[b.dataset.k];
  const d = id && body.querySelector(`details[data-id="${id}"]`);
  if (d) d.open = true;
}

// "Mở hết" / "Đóng hết" of the sections in body; returns the new button text.
function guideToggleAll(body) {
  const all = [...body.querySelectorAll('details')];
  const open = !all.every((d) => d.open);
  all.forEach((d) => { d.open = open; });
  return open ? 'Đóng hết' : 'Mở hết';
}

// Example files of one key (GET /web/guide-examples/<key>): { files, base, isDefault }.
async function guideExamples(key) {
  try {
    const r = await fetch('/web/guide-examples/' + encodeURIComponent(key));
    if (r.ok) { const d = await r.json(); return { files: d.files || [], base: d.base || 'vd', isDefault: !!d.default }; }
  } catch (_) { /* no list: shown as empty */ }
  return { files: [], base: 'vd', isDefault: false };
}
// Grid of example photos / PDFs. canDelete: ADMIN gets a "Xoá" button on the photos they added.
function guideExGrid(key, { files, base, isDefault }, canDelete = false) {
  return `<div class="exgrid">${files.map((f, i) => {
    const url = `/web/guide/${base}/${encodeURIComponent(key)}/${encodeURIComponent(f)}`;
    const view = /\.pdf$/i.test(f)
      ? `<a class="expdf" href="${url}" target="_blank" rel="noopener" title="Mở PDF"><iframe src="${url}#toolbar=0&navpanes=0&view=FitH" loading="lazy" tabindex="-1" title="PDF ví dụ ${i + 1}"></iframe><span>📄 Mở PDF</span></a>`
      : `<a href="${url}" target="_blank" rel="noopener"><img src="${url}" alt="Ví dụ ${i + 1}" loading="lazy"></a>`;
    return `<figure>${view}
      <figcaption>${isDefault ? 'Mẫu' : 'Ví dụ'} ${i + 1}${canDelete && !isDefault ? `<button type="button" class="secondary exdel" data-f="${esc(f)}">Xoá</button>` : ''}</figcaption></figure>`;
  }).join('')}</div>`;
}

// Link to the page /web/huong-dan with the same visa, house and options.
function guidePageUrl(v, house) {
  const q = new URLSearchParams({ visa: v, house });
  Object.entries(guideOpt).forEach(([k, val]) => q.set(k, String(val)));
  return '/web/huong-dan?' + q.toString();
}
