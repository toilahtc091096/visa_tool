// Test web/file_check.js (update.md K1 + K2). Chạy: node tests/file_check_cases.js
// (tests/test_file_check.py gọi file này trong bộ unittest).
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const FC = require('../web/file_check.js');

let passed = 0;
const failures = [];
function test(name, fn) {
  try { fn(); passed++; } catch (e) { failures.push(`${name}: ${e.message}`); }
}
const F = (...names) => names.map((n) => (typeof n === 'string' ? { rel: n, size: 100000 } : n));
const BASIC_N = ['IMG_2041.jpg', 'IMG_2042.jpg', 'scan_01.jpg'];   // hộ chiếu, ảnh thẻ, 1 trang trắng
const run = (files, visa, house = 'HAI', relation = 'ME') => FC.checkFolder(F(...files), { visa, house, relation });
const msgs = (r) => [...r.folder, ...r.files.flatMap((f) => f.issues)];
const hasMsg = (r, level, re) => msgs(r).some((i) => i.level === level && re.test(i.msg));
const fileOf = (r, rel) => r.files.find((f) => f.rel === rel);

// ---------- thư mục đúng: không chặn nhầm ----------
const GOOD = [
  ['L', 'HAI', ['IMG_2041.jpg', 'IMG_2042.jpg', 'scan_01.jpg', 'scan_02.jpg', 'ct07.pdf', 'visa2023.jpg', 'tt_cha.jpg', 'tt_me.jpg', 'con_1.jpg', 'con_2.jpg', 'vo_chong.jpg']],
  ['L', 'TAI', ['IMG_2041.jpg', 'IMG_2042.jpg', 'cv_1.jpg', 'cv_2.jpg', 'duoi18_ks.jpg', 'duoi18_dc1.jpg', 'duoi18_dc2.jpg', 'duoi18_pay.jpg']],
  ['M', 'HAI', [...BASIC_N, 'thumoi.jpg', 'dktq_1.jpg', 'dktq_2.jpg', 'dkvn.pdf', 'qdct.jpg', 'cv_1.jpg']],
  ['F', 'PHONG', [...BASIC_N, 'fthumoi_1.jpg', 'fqddh_1.pdf']],
  ['X1', 'TAI', ['IMG_2041.jpg', 'IMG_2042.jpg', 'xnh_1.jpg', 'xjw_1.pdf']],
  ['X2', 'HAI', [...BASIC_N, 'xjw_1.jpg']],
  ['Q1', 'HAI', [...BASIC_N, 'qmoi_1.jpg', 'qmoi_2.jpg', 'qcm_1.jpg', 'qcm_2.jpg', 'qcm_3.jpg', 'qcm_4.jpg', 'qchuki_1_goc.png', 'qbaolanh_1.png', 'qkhac_1.jpg', 'qthumoi_1.jpg']],
  ['Q2', 'TAI', ['IMG_2041.jpg', 'IMG_2042.jpg', 'qmoi_1.jpg', 'qmoi_2.jpg', 'qmoi_3.jpg', 'qmoi_4.jpg', 'qcm_1.jpg', 'qcm_2.jpg', 'qcm_3.jpg', 'qcm_4.jpg', 'qcm_5.jpg', 'qchuki_1.png']],
  ['S2', 'PHONG', [...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg', 'smoi_ruot_1.jpg', 'scm_1.jpg', 'scm_2.jpg', 'schuki_1.png', 'skhac_1.jpg', 'sthumoi_1.pdf']],
  ['Q2', 'HAI', [...BASIC_N, 'qmoi_1.jpg', 'qcm_1.jpg', 'duoi18_ks.jpg', 'duoi18_dc1.jpg', 'duoi18_dc2.jpg']],
];
GOOD.forEach(([visa, house, files], i) => test(`good #${i + 1} ${visa} ${house}`, () => {
  const r = run(files, visa, house);
  assert.strictEqual(r.errors, 0, JSON.stringify(msgs(r).filter((x) => x.level === 'err')));
  assert.strictEqual(r.warns, 0, JSON.stringify(msgs(r).filter((x) => x.level === 'warn')));
}));

// ---------- 1. ký tự ----------
test('1 dấu / dấu cách -> warn + tên gợi ý', () => {
  const r = run([...BASIC_N, 'Ảnh hộ chiếu (1).jpg'], 'L');
  const f = fileOf(r, 'Ảnh hộ chiếu (1).jpg');
  assert.strictEqual(f.level, 'warn');
  assert.strictEqual(f.issues[0].fix, 'Anh_ho_chieu_1');
});
test('1 slug đ', () => assert.strictEqual(FC.slug('đăng ký'), 'dang_ky'));

// ---------- 2. đuôi, dung lượng ----------
test('2 heic -> err', () => assert.strictEqual(fileOf(run([...BASIC_N, 'IMG_1.HEIC'], 'L'), 'IMG_1.HEIC').level, 'err'));
test('2 docx -> err', () => assert.strictEqual(fileOf(run([...BASIC_N, 'thu.docx'], 'L'), 'thu.docx').level, 'err'));
test('2 file quá lớn -> err', () => {
  const r = FC.checkFolder([...F(...BASIC_N), { rel: 'big.jpg', size: 60 * 1024 * 1024 }], { visa: 'L', house: 'HAI' });
  assert.strictEqual(fileOf(r, 'big.jpg').level, 'err');
});
test('2 file 20MB -> warn', () => {
  const r = FC.checkFolder([...F(...BASIC_N), { rel: 'big.jpg', size: 20 * 1024 * 1024 }], { visa: 'L', house: 'HAI' });
  assert.strictEqual(fileOf(r, 'big.jpg').level, 'warn');
});

// ---------- 3. tiền tố của loại khác ----------
test('3 qmoi_ trong S2 -> err, gợi ý smoi_', () => {
  const r = run([...BASIC_N, 'qmoi_1.jpg', 'smoi_2.jpg', 'scm_1.jpg'], 'S2');
  const f = fileOf(r, 'qmoi_1.jpg');
  assert.strictEqual(f.level, 'err');
  assert.strictEqual(f.issues[0].fix, 'smoi_1');
});
test('3 scm_ trong Q2 -> err, gợi ý qcm_', () => assert.strictEqual(fileOf(run([...BASIC_N, 'qmoi_1.jpg', 'scm_1.jpg'], 'Q2'), 'scm_1.jpg').issues[0].fix, 'qcm_1'));
test('3 thumoi trong F -> err, gợi ý fthumoi_1', () => {
  const f = fileOf(run([...BASIC_N, 'thumoi.jpg', 'fqddh_1.jpg'], 'F'), 'thumoi.jpg');
  assert.strictEqual(f.level, 'err');
  assert.strictEqual(f.issues[0].fix, 'fthumoi_1');
});
test('3 thumoi trong Q1 -> gợi ý qthumoi_1', () => assert.strictEqual(fileOf(run([...BASIC_N, 'qmoi_1.jpg', 'qcm_1.jpg', 'thumoi.jpg'], 'Q1'), 'thumoi.jpg').issues[0].fix, 'qthumoi_1'));
test('3 qthumoi trong S2 -> gợi ý sthumoi_1', () => assert.strictEqual(fileOf(run([...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg', 'scm_1.jpg', 'qthumoi_1.jpg'], 'S2'), 'qthumoi_1.jpg').issues[0].fix, 'sthumoi_1'));
test('3 fthumoi trong M -> err', () => assert.strictEqual(fileOf(run([...BASIC_N, 'fthumoi_1.jpg'], 'M'), 'fthumoi_1.jpg').level, 'err'));
test('3 xnh trong F -> err', () => assert.strictEqual(fileOf(run([...BASIC_N, 'fthumoi_1.jpg', 'fqddh_1.jpg', 'xnh_1.jpg'], 'F'), 'xnh_1.jpg').level, 'err'));
test('3 dkvn trong L -> err', () => assert.strictEqual(fileOf(run([...BASIC_N, 'dkvn.jpg'], 'L'), 'dkvn.jpg').level, 'err'));

// ---------- 4. sai dạng tên ----------
test('4 cv1 -> err, gợi ý cv_1', () => {
  const f = fileOf(run([...BASIC_N, 'cv1.jpg'], 'L'), 'cv1.jpg');
  assert.strictEqual(f.level, 'err');
  assert.strictEqual(f.issues[0].fix, 'cv_1');
});
test('4 smoi_1_ruot -> err, gợi ý smoi_ruot_1', () => {
  const f = fileOf(run([...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg', 'scm_1.jpg', 'smoi_1_ruot.jpg'], 'S2'), 'smoi_1_ruot.jpg');
  assert.strictEqual(f.level, 'err');
  assert.strictEqual(f.issues[0].fix, 'smoi_ruot_1');
});
test('4 smoiruot -> warn (n8n vẫn nhận), gợi ý smoi_ruot_1', () => {
  const f = fileOf(run([...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg', 'scm_1.jpg', 'smoiruot.jpg'], 'S2'), 'smoiruot.jpg');
  assert.strictEqual(f.level, 'warn');
  assert.strictEqual(f.issues[0].fix, 'smoi_ruot_1');
});
test('4 qchuki_goc_1 -> warn, gợi ý qchuki_1_goc', () => {
  const f = fileOf(run([...BASIC_N, 'qmoi_1.jpg', 'qcm_1.jpg', 'qchuki_goc_1.png'], 'Q2'), 'qchuki_goc_1.png');
  assert.strictEqual(f.level, 'warn');
  assert.strictEqual(f.issues[0].fix, 'qchuki_1_goc');
});
test('4 duoi18ks -> err, gợi ý duoi18_ks', () => {
  const f = fileOf(run([...BASIC_N, 'duoi18ks.jpg'], 'L'), 'duoi18ks.jpg');
  assert.strictEqual(f.level, 'err');
  assert.strictEqual(f.issues[0].fix, 'duoi18_ks');
});
test('4 duoi_18_dc1 -> err', () => assert.strictEqual(fileOf(run([...BASIC_N, 'duoi_18_dc1.jpg'], 'L'), 'duoi_18_dc1.jpg').issues[0].fix, 'duoi18_dc1'));
test('4 con1 -> err (n8n không nhận)', () => assert.strictEqual(fileOf(run([...BASIC_N, 'con1.jpg'], 'L'), 'con1.jpg').level, 'err'));
test('4 qmoi1 -> warn (n8n vẫn nhận)', () => assert.strictEqual(fileOf(run([...BASIC_N, 'qmoi1.jpg', 'qcm_1.jpg'], 'Q2'), 'qmoi1.jpg').level, 'warn'));

// ---------- 5. trùng, nhảy số ----------
test('5 trùng tên khác đuôi -> warn', () => assert.strictEqual(fileOf(run([...BASIC_N, 'tt_cha.jpg', 'tt_cha.png'], 'L'), 'tt_cha.png').level, 'warn'));
test('5 nhảy số qcm_1, qcm_3 -> warn', () => assert.ok(hasMsg(run([...BASIC_N, 'qmoi_1.jpg', 'qcm_1.jpg', 'qcm_3.jpg'], 'Q2'), 'warn', /thiếu qcm_2/)));
test('5 chỉ có qcm_2 -> warn thiếu qcm_1', () => assert.ok(hasMsg(run([...BASIC_N, 'qmoi_1.jpg', 'qcm_2.jpg'], 'Q2'), 'warn', /thiếu qcm_1/)));

// ---------- 6. file cơ bản tối thiểu ----------
test('6 Bắc 2 file cơ bản -> warn (cần 1 trang trắng)', () => assert.ok(hasMsg(run(['a.jpg', 'b.jpg'], 'L', 'HAI'), 'warn', /trang trắng/)));
test('6 Bắc 3 file cơ bản -> ok', () => assert.strictEqual(run(['a.jpg', 'b.jpg', 'c.jpg'], 'L', 'PHONG').warns, 0));
test('6 Nam 2 file cơ bản -> ok', () => assert.strictEqual(run(['a.jpg', 'b.jpg'], 'L', 'TAI').warns, 0));
test('6 Nam 1 file cơ bản -> warn', () => assert.ok(hasMsg(run(['a.jpg'], 'L', 'TAI'), 'warn', /file cơ bản/)));

// ---------- 7, 8. Q / S2 ----------
test('7 Q1 thiếu qmoi -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'qcm_1.jpg'], 'Q1'), 'err', /qmoi_1/)));
test('7 Q2 thiếu qcm -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'qmoi_1.jpg'], 'Q2'), 'err', /qcm_1/)));
test('7 S2 thiếu smoi_2 -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'smoi_1.jpg', 'scm_1.jpg'], 'S2'), 'err', /smoi_2/)));
test('7 S2 thiếu scm -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg'], 'S2'), 'err', /scm_1/)));
test('8 Q2 chưa chọn quan hệ -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'qmoi_1.jpg', 'qcm_1.jpg'], 'Q2', 'HAI', ''), 'err', /Quan hệ/)));
test('8 S2 chưa chọn quan hệ -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg', 'scm_1.jpg'], 'S2', 'TAI', ''), 'err', /Quan hệ/)));
test('8 L không cần quan hệ', () => assert.strictEqual(run(BASIC_N, 'L', 'HAI', '').errors, 0));

// ---------- 9, 10. M / F / X ----------
test('9 M thiếu qdct -> warn Áp dụng M', () => {
  const r = run([...BASIC_N, 'thumoi.jpg', 'dktq.jpg', 'dkvn.jpg'], 'M');
  assert.strictEqual(r.errors, 0);
  assert.ok(hasMsg(r, 'warn', /qdct.*Áp dụng M/));
});
test('9 M không có giấy công ty -> warn Áp dụng M', () => {
  const r = run(BASIC_N, 'M');
  assert.strictEqual(r.errors, 0);
  assert.ok(hasMsg(r, 'warn', /thumoi, dktq, dkvn, qdct.*Áp dụng M/));
});
test('10 F thiếu fqddh -> warn Áp dụng F', () => assert.ok(hasMsg(run([...BASIC_N, 'fthumoi_1.jpg'], 'F'), 'warn', /fqddh.*Áp dụng F/)));
test('10 F không có giấy trường -> warn Áp dụng F', () => assert.ok(hasMsg(run(BASIC_N, 'F'), 'warn', /Áp dụng F/)));
test('10 X2 thiếu cả xnh, xjw -> err', () => assert.ok(hasMsg(run(BASIC_N, 'X2'), 'err', /xnh_1/)));

// ---------- 11, 12. giới hạn miền Bắc ----------
test('11 Bắc qmoi_3 -> warn, gợi ý qkhac_3', () => {
  const f = fileOf(run([...BASIC_N, 'qmoi_1.jpg', 'qmoi_2.jpg', 'qmoi_3.jpg', 'qcm_1.jpg'], 'Q2', 'HAI'), 'qmoi_3.jpg');
  assert.strictEqual(f.level, 'warn');
  assert.strictEqual(f.issues[0].fix, 'qkhac_3');
});
test('11 Nam qmoi_3 -> ok', () => assert.strictEqual(fileOf(run(['a.jpg', 'b.jpg', 'qmoi_1.jpg', 'qmoi_2.jpg', 'qmoi_3.jpg', 'qcm_1.jpg'], 'Q2', 'TAI'), 'qmoi_3.jpg').level, 'ok'));
test('12 Bắc Q1 5 qcm -> warn, qcm_5 không tải', () => assert.ok(hasMsg(run([...BASIC_N, 'qmoi_1.jpg', 'qcm_1.jpg', 'qcm_2.jpg', 'qcm_3.jpg', 'qcm_4.jpg', 'qcm_5.jpg'], 'Q1', 'HAI'), 'warn', /KHÔNG tải: qcm_5\.jpg/)));
test('12 Bắc S2 4 scm -> warn', () => assert.ok(hasMsg(run([...BASIC_N, 'smoi_1.jpg', 'smoi_2.jpg', 'scm_1.jpg', 'scm_2.jpg', 'scm_3.jpg', 'scm_4.jpg'], 'S2', 'PHONG'), 'warn', /scm_4/)));
test('12 Nam 5 qcm -> ok', () => assert.ok(!hasMsg(run(['a.jpg', 'b.jpg', 'qmoi_1.jpg', 'qcm_1.jpg', 'qcm_2.jpg', 'qcm_3.jpg', 'qcm_4.jpg', 'qcm_5.jpg'], 'Q1', 'TAI'), 'warn', /KHÔNG tải/)));

// ---------- 13. dưới 18 ----------
test('13 có duoi18_ks, thiếu dc1 dc2 -> err', () => assert.ok(hasMsg(run([...BASIC_N, 'duoi18_ks.jpg'], 'L'), 'err', /duoi18_dc1, duoi18_dc2/)));
test('13 tên duoi18 lạ -> warn', () => assert.strictEqual(fileOf(run([...BASIC_N, 'duoi18_ks.jpg', 'duoi18_dc1.jpg', 'duoi18_dc2.jpg', 'duoi18_bo.jpg'], 'L'), 'duoi18_bo.jpg').level, 'warn'));

// ---------- 14. nhắc người đi cùng ----------
test('14 L không có cv_ -> info (không phải lỗi)', () => {
  const r = run(BASIC_N, 'L');
  assert.ok(r.folder.some((x) => x.level === 'info'));
  assert.strictEqual(r.errors + r.warns, 0);
});

// ---------- 16. tên tự do chứa từ khoá n8n ----------
test('16 anh_con.jpg -> warn bị hiểu là con', () => assert.ok(/con/.test(fileOf(run([...BASIC_N, 'anh_con.jpg'], 'L'), 'anh_con.jpg').issues[0].msg)));
test('16 thong_tin_cong_viec.jpg -> warn (cho biết hệ thống hiểu là gì)', () => assert.strictEqual(fileOf(run([...BASIC_N, 'thong_tin_cong_viec.jpg'], 'L'), 'thong_tin_cong_viec.jpg').level, 'warn'));
test('đường dẫn thư mục con: chỉ xét tên file', () => assert.strictEqual(fileOf(run([...BASIC_N, 'sub/tt_me.jpg'], 'L'), 'sub/tt_me.jpg').level, 'ok'));

// ---------- n8nGroup = code thật của n8n (khi có bản export trong n8n-flow/workflows, bị gitignore) ----------
const SAMPLES = ['IMG_2041.jpg', 'info.pdf', 'cv_1.jpg', 'cv1.jpg', 'fthumoi_1.jpg', 'fqddh_1.pdf', 'xnh_1.jpg', 'xjw_1.jpg',
  'qthumoi_1.jpg', 'sthumoi_1.pdf', 'smoi_ruot_1.jpg', 'smoiruot.jpg', 'smoi_1_ruot.jpg', 'qkhac_1.jpg', 'skhac_2.jpg', 'qmoi_1.jpg',
  'qmoi1.jpg', 'smoi_2.jpg', 'qcm_1.jpg', 'scm_3.jpg', 'qchuki_1_goc.png', 'qchuky_1.png', 'schuki_1.png', 'qbaolanh_1.png',
  'qbl_1.png', 'qblgoc_1.png', 'abcdefghijklmnopqrstuvwxyz.jpg', 'duoi18_ks.jpg', 'duoi18_pay.jpg', 'duoi18ks.jpg',
  'tt_cha.jpg', 'tt_me_2.jpg', 'ttcha.jpg', 'con_1.jpg', 'con1.jpg', 'vo_chong.jpg', 'thumoi.jpg', 'thu moi.pdf', 'dkvn.jpg',
  'dktq_2.jpg', 'qdct.jpg', 'thong_tin_cong_viec.jpg', 'hoc_van.jpg', 'anh_con.jpg', 'Ảnh mẹ.jpg', 'scan_01.jpg', 'ct07.pdf'];
const dir = path.join(__dirname, '..', 'n8n-flow', 'workflows');
const wf = fs.existsSync(dir) && fs.readdirSync(dir).find((f) => /^WF-04_Document_Classification.*\.json$/.test(f));
let parity = 'bỏ qua (không có n8n-flow/workflows/WF-04_Document_Classification*.json)';
if (wf) {
  const doc = JSON.parse(fs.readFileSync(path.join(dir, wf), 'utf8').replace(/^﻿/, ''));
  const node = doc.nodes.find((n) => n.name === 'Detect Processing Group');
  if (node) {
    const code = node.parameters.jsCode;
    const items = SAMPLES.map((n) => ({ json: { source_filename: n }, binary: {} }));
    const out = vm.runInNewContext(`(function(){ ${code} })()`, { $input: { all: () => items } });
    SAMPLES.forEach((n, i) => test(`n8n parity ${n}`, () => assert.strictEqual(FC.n8nGroup(n), out[i].json.processing_group)));
    parity = `so với ${wf}`;
  }
}

console.log(`file_check: ${passed} passed, ${failures.length} failed; n8n parity: ${parity}`);
if (failures.length) {
  failures.forEach((f) => console.log('FAIL ' + f));
  process.exit(1);
}
