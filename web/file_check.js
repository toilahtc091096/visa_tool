// ---------- Kiểm tra thư mục hồ sơ trước khi tải lên (update.md K1 + K2) ----------
// Một nơi duy nhất cho quy tắc tên file. Dùng ở form /web (trình duyệt) và trong test Node
// (tests/file_check_cases.js). Không đụng tới n8n: classify() chép lại cách n8n WF-04 node
// "Detect Processing Group" xếp file theo tên, để báo trước "hệ thống sẽ hiểu file này là gì".
// Nghiệp vụ: HUONGDAN.md, web/guide.js. Giới hạn miền Bắc: constants.py (UPLOAD_FILE_CODE_NORTH).
(function (root) {
  'use strict';

  const NORTH = ['HAI', 'PHONG'];
  const OK_EXT = ['jpg', 'jpeg', 'png', 'webp', 'pdf'];
  const MB = 1024 * 1024;
  const WARN_SIZE = 15 * MB;
  const MAX_SIZE = 50 * MB;
  // Miền Bắc: số file qcm_ / scm_ được tải lên (Q1, Q2: 4 ô mfa-073 / mfa-094; S2: 3 ô mfa-125).
  const NORTH_REL_MAX = { Q1: 4, Q2: 4, S2: 3 };
  const RELATION_REQUIRED = ['Q1', 'Q2', 'S2'];
  const U18_VISAS = ['L', 'Q1', 'Q2', 'S2'];
  const CV_VISAS = ['L', 'M', 'F', 'X1', 'X2'];

  // Tiền tố riêng của từng loại visa: series -> loại visa dùng nó, tên để hiện.
  const OWN = {
    thumoi: ['M'], dktq: ['M'], dkvn: ['M'], qdct: ['M'],
    fthumoi: ['F'], fqddh: ['F'],
    xnh: ['X1', 'X2'], xjw: ['X1', 'X2'],
    qmoi: ['Q1', 'Q2'], qcm: ['Q1', 'Q2'], qkhac: ['Q1', 'Q2'], qthumoi: ['Q1', 'Q2'], qchuki: ['Q1', 'Q2'], qbaolanh: ['Q1', 'Q2'],
    smoi: ['S2'], smoi_ruot: ['S2'], scm: ['S2'], skhac: ['S2'], sthumoi: ['S2'], schuki: ['S2'],
  };
  const M_FILES = ['thumoi', 'dktq', 'dkvn', 'qdct'];
  const F_FILES = ['fthumoi', 'fqddh'];
  const U18_NEED = ['duoi18_ks', 'duoi18_dc1', 'duoi18_dc2'];
  const U18_NAMES = [...U18_NEED, 'duoi18_pay'];
  // Đánh số liên tục 1, 2, 3… (thứ tự trang / thứ tự người)
  const NUMBERED = ['qmoi', 'smoi', 'qcm', 'scm', 'qkhac', 'skhac', 'qthumoi', 'sthumoi', 'smoi_ruot', 'cv', 'con',
                    'fthumoi', 'fqddh', 'xnh', 'xjw', 'thumoi', 'dktq', 'dkvn', 'qdct'];
  const LABEL = {
    family_father: 'bố (tt_cha)', family_mother: 'mẹ (tt_me)', family_child: 'con (con_N)', family_spouse: 'vợ / chồng (vo_chong)',
    invitation_letter: 'thư mời visa M (thumoi)', vietnam_registration: 'đăng ký KD Việt Nam (dkvn)',
    china_registration: 'đăng ký KD Trung Quốc (dktq)', assignment_decision: 'quyết định công tác (qdct)',
    work_info: 'thông tin công việc', education_info: 'thông tin học vấn',
  };

  // ----- n8n WF-04 "Detect Processing Group" (chép lại, giữ đúng thứ tự kiểm) -----
  function tokenize(v) {
    return String(v).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter(Boolean);
  }
  function hasSeq(tokens, want) {
    for (let i = 0; i <= tokens.length - want.length; i++) if (want.every((w, j) => tokens[i + j] === w)) return true;
    return false;
  }
  const TOKEN_RULES = [
    ['family_father', [['cha'], ['ttcha'], ['thong', 'tin', 'cha'], ['thong', 'tin', 'cua', 'cha']]],
    ['family_mother', [['ttme'], ['me'], ['thong', 'tin', 'me'], ['thong', 'tin', 'cua', 'me']]],
    ['family_child', [['con'], ['thong', 'tin', 'con']]],
    ['family_spouse', [['vo', 'chong'], ['thong', 'tin', 'vo', 'chong'], ['thong', 'tin', 'vo'], ['thong', 'tin', 'chong']]],
    ['invitation_letter', [['thumoi'], ['thu', 'moi'], ['invitation']]],
    ['vietnam_registration', [['dkvn'], ['dang', 'ky', 'vn'], ['dang', 'ky', 'viet', 'nam']]],
    ['china_registration', [['dktq'], ['dang', 'ky', 'tq'], ['dang', 'ky', 'trung', 'quoc']]],
    ['assignment_decision', [['qdct'], ['quyet', 'dinh', 'cong', 'tac']]],
    ['work_info', [['thong', 'tin', 'cong', 'viec'], ['thong', 'tin', 'viec'], ['cong', 'viec', 'hien', 'tai'], ['work']]],
    ['education_info', [['trinh', 'do', 'hoc', 'van'], ['hoc', 'van'], ['trinh', 'o', 'hoc'], ['education'], ['edu']]],
  ];
  // name = tên file (không có thư mục). Trả về nhóm n8n sẽ xếp vào.
  function n8nGroup(name) {
    const raw = String(name).trim();
    if (tokenize(raw).join('') === 'infopdf') return 'info';
    if (/^cv_/i.test(raw)) return 'companion_passport';
    if (/^(fthumoi|fqddh|xjw|xnh)[_\-]?/i.test(raw)) return 'study_documents';
    if (/^[qs]thumoi[_\-]?/i.test(raw)) return 'visit_invitation_letter';
    if (/^smoi[_\-]?ruot/i.test(raw)) return 'visit_inviter_relative';
    if (/^[qs]khac[_\-]?/i.test(raw)) return 'visit_other_document';
    if (/^[qs]moi[_\-]?/i.test(raw)) return 'visit_inviter_id';
    if (/^[qs]cm[_\-]?/i.test(raw)) return 'visit_relationship';
    if (/^(?:[qs]chuk[yi]|qbaolanh|qbl(?=[_\-.]|goc|$))/i.test(raw)) return 'visit_signature';
    const stem = raw.replace(/\.[a-z0-9]+$/i, '');
    if (!/[_\-\s]/.test(stem) && stem.length >= 20) return 'general_document';
    const t = tokenize(raw);
    if (hasSeq(t, ['duoi18', 'pay']) || hasSeq(t, ['duoi18', 'payer'])) return 'minor_payer';
    if (hasSeq(t, ['duoi18'])) return 'minor_document';
    for (const [group, anyOf] of TOKEN_RULES) if (anyOf.some((w) => hasSeq(t, w))) return group;
    return 'general_document';
  }

  // ----- tên file -----
  const splitName = (rel) => {
    const base = String(rel).split('/').pop();
    const m = base.match(/^(.*?)(?:\.([^.]+))?$/);
    return { base, stem: m[1], ext: (m[2] || '').toLowerCase() };
  };
  // Tên không dấu, không cách: "Ảnh hộ chiếu (1)" -> "Anh_ho_chieu_1"
  function slug(stem) {
    return String(stem).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D')
      .replace(/[^A-Za-z0-9_-]+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'file';
  }
  const SERIES_RE = /^(smoi_ruot|qthumoi|sthumoi|fthumoi|qbaolanh|qchuki|qchuky|schuki|schuky|qkhac|skhac|fqddh|thumoi|qmoi|smoi|qcm|scm|qdct|dkvn|dktq|xnh|xjw|qbl|cv|con|tt_cha|tt_me|vo_chong)(?:[_-]?(\d+))?(?:[_-]goc)?$/i;
  // series + số thứ tự của tên đúng mẫu (qmoi_2 -> qmoi, 2). Không khớp -> null.
  function series(stem) {
    const m = String(stem).toLowerCase().match(SERIES_RE);
    if (!m) return null;
    let s = m[1];
    if (s === 'qchuky') s = 'qchuki';
    if (s === 'schuky') s = 'schuki';
    if (s === 'qbl') s = 'qbaolanh';
    return { s, n: m[2] ? Number(m[2]) : 0 };
  }

  // Q <-> S: cùng giấy, khác tiền tố
  const QS = { qmoi: 'smoi', qcm: 'scm', qkhac: 'skhac', qthumoi: 'sthumoi', qchuki: 'schuki' };
  const SQ = Object.fromEntries(Object.entries(QS).map(([a, b]) => [b, a]));
  // Thư mời theo loại visa (thumoi chỉ của M)
  const LETTER = { Q1: 'qthumoi', Q2: 'qthumoi', S2: 'sthumoi', F: 'fthumoi' };

  function swapPrefix(stem, from, to) { return to + stem.slice(from.length); }

  // ----- kiểm 1 file: [{level, msg, fix}] (fix = tên mới không có đuôi) -----
  function checkFile(f, ctx) {
    const out = [];
    const { stem, ext } = splitName(f.rel);
    const low = stem.toLowerCase();
    const visa = ctx.visa;
    const add = (level, msg, fix) => out.push({ level, msg, fix: fix || '' });

    // 2. đuôi, dung lượng
    if (!OK_EXT.includes(ext)) add('err', `Đuôi .${ext || '(không có)'} không dùng được — đổi sang .jpg, .png hoặc .pdf`);
    if (f.size > MAX_SIZE) add('err', `File ${(f.size / MB).toFixed(0)} MB, quá lớn (tối đa ${MAX_SIZE / MB} MB) — nén hoặc chụp lại`);
    else if (f.size > WARN_SIZE) add('warn', `File ${(f.size / MB).toFixed(0)} MB, khá lớn — tải lâu, nên nén bớt`);

    // 1. ký tự
    if (!/^[A-Za-z0-9_-]+$/.test(stem)) add('warn', 'Tên có dấu, dấu cách hoặc ký tự lạ — đổi sang không dấu, không cách', slug(stem));

    const name = slug(stem); // phần kiểm dưới đây theo tên đã bỏ dấu
    const lname = name.toLowerCase();

    // 4. sai dạng tên (các lỗi hay gặp trong HUONGDAN.md)
    let m;
    if ((m = lname.match(/^cv[-]?(\d+)$/))) { add('err', `Người đi cùng phải tên cv_${m[1]} — "${stem}" không được nhận là người đi cùng`, `cv_${m[1]}`); return out; }
    if ((m = lname.match(/^smoi[_-]?(\d+)[_-]?ruot$/))) { add('err', `Phải là smoi_ruot_${m[1]} — "${stem}" bị hiểu là giấy người mời (smoi)`, `smoi_ruot_${m[1]}`); return out; }
    if ((m = lname.match(/^smoi[-]?ruot(?:[_-]?(\d+))?$/)) && !/^smoi_ruot/.test(lname)) add('warn', 'Nên đặt đúng mẫu smoi_ruot_1', `smoi_ruot_${m[1] || 1}`);
    if ((m = lname.match(/^(qchuk[iy]|schuk[iy]|qbaolanh|qbl)[_-]?goc[_-]?(\d+)$/))) add('warn', `Đuôi _goc phải đặt cuối tên: ${m[1]}_${m[2]}_goc`, `${m[1]}_${m[2]}_goc`);
    if (/^duoi[_\-\s]*18/.test(lname) && !/^(minor_)/.test(n8nGroup(name + '.' + ext))) {
      const rest = lname.replace(/^duoi[_\-\s]*18[_-]?/, '');
      add('err', `Giấy dưới 18 phải bắt đầu bằng duoi18_ — "${stem}" không được nhận`, `duoi18_${rest || 'ks'}`);
      return out;
    }

    const group = n8nGroup(name + '.' + ext);
    const sr = series(name);

    // tên đúng mẫu nhưng thiếu "_" trước số (qmoi1 -> qmoi_1)
    // (con1, ttcha1, thumoi1… thì n8n không nhận ra -> chặn; qmoi1, qcm2… n8n vẫn nhận -> nhắc)
    if (sr && sr.n && !/[_-]\d+(?:[_-]goc)?$/i.test(name)) {
      const fix = name.replace(/(\d+)((?:[_-]goc)?)$/i, '_$1$2').replace(/__+/g, '_');
      if (group === 'general_document') add('err', `Hệ thống không nhận ra "${stem}" — phải có "_" trước số: ${fix}`, fix);
      else add('warn', `Nên có "_" trước số: ${fix}`, fix);
    }

    // dưới 18: tên lạ
    if (group === 'minor_document' || group === 'minor_payer') {
      const base = lname.replace(/[_-]\d+$/, '');
      if (!U18_NAMES.includes(base)) add('warn', `Tên giấy dưới 18 nên là 1 trong: ${U18_NAMES.join(', ')}`);
      if (!U18_VISAS.includes(visa)) add('warn', `Visa ${visa} không có bộ giấy dưới 18 trong hướng dẫn`);
    }

    // 3. tiền tố của loại visa khác
    if (sr && OWN[sr.s] && !OWN[sr.s].includes(visa)) {
      let fix = '';
      if (['Q1', 'Q2'].includes(visa) && SQ[sr.s]) fix = swapPrefix(lname, sr.s, SQ[sr.s]);
      else if (visa === 'S2' && QS[sr.s]) fix = swapPrefix(lname, sr.s, QS[sr.s]);
      else if (LETTER[visa] && /thumoi$/.test(sr.s)) fix = swapPrefix(lname, sr.s, LETTER[visa]) + (sr.n ? '' : '_1');
      const own = OWN[sr.s].join(' / ');
      add('err', `Tiền tố ${sr.s} là của visa ${own}, không dùng cho visa ${visa}${fix ? '' : ' — bỏ ra hoặc đổi tên đúng giấy của visa ' + visa}`, fix);
      return out;
    }

    // 16. tên tự do vô tình chứa từ khoá n8n (vd "anh_con.jpg" bị hiểu là con)
    if (LABEL[group] && !sr) add('warn', `Hệ thống sẽ hiểu file này là ${LABEL[group]} vì tên có từ khoá — nếu không phải thì đổi tên khác`);

    // 11. miền Bắc: giấy người mời từ tờ thứ 3 -> qkhac_ / skhac_
    if (ctx.north && sr && (sr.s === 'qmoi' || sr.s === 'smoi') && sr.n >= 3) {
      const khac = sr.s === 'qmoi' ? 'qkhac' : 'skhac';
      add('warn', `Miền Bắc chỉ dùng ${sr.s}_1, ${sr.s}_2 — tờ thứ 3 trở đi đặt ${khac}_`, `${khac}_${sr.n}`);
    }
    return out;
  }

  // ----- kiểm cả thư mục -----
  // files = [{rel, size}], ctx = {visa, house, relation}
  // -> { files: [{rel, level, issues:[{level,msg,fix}], group}], folder: [{level,msg}], errors, warns }
  function checkFolder(files, ctx0) {
    const ctx = { ...ctx0, north: NORTH.includes(String(ctx0.house || '').toUpperCase()) };
    const visa = ctx.visa;
    const rows = files.map((f) => {
      const issues = checkFile(f, ctx);
      const { stem, ext } = splitName(f.rel);
      const name = slug(stem);
      return { rel: f.rel, issues, group: n8nGroup(name + '.' + ext), sr: series(name), lname: name.toLowerCase() };
    });
    const folder = [];
    const addF = (level, msg) => folder.push({ level, msg });
    const bySeries = {};
    rows.forEach((r) => { if (r.sr) (bySeries[r.sr.s] = bySeries[r.sr.s] || []).push(r); });
    const has = (s) => (bySeries[s] || []).length > 0;
    const nums = (s) => (bySeries[s] || []).map((r) => r.sr.n || 1);

    // 5. trùng tên, nhảy số
    const seen = {};
    rows.forEach((r) => {
      const k = splitName(r.rel).stem.toLowerCase();
      if (seen[k]) r.issues.push({ level: 'warn', msg: `Trùng tên với ${splitName(seen[k]).base} — bỏ bớt 1 file`, fix: '' });
      else seen[k] = r.rel;
    });
    NUMBERED.forEach((s) => {
      if (OWN[s] && !OWN[s].includes(visa)) return; // tiền tố sai loại visa: đã báo lỗi ở từng file
      const n = [...new Set(nums(s))].sort((a, b) => a - b);
      if (n.length < 2 && !(n.length === 1 && n[0] > 1)) return;
      const miss = [];
      for (let i = 1; i <= n[n.length - 1]; i++) if (!n.includes(i)) miss.push(`${s}_${i}`);
      if (miss.length) addF('warn', `Đánh số nhảy cóc: thiếu ${miss.join(', ')} — đánh số lại liên tục 1, 2, 3…`);
    });

    // 6. file cơ bản tối thiểu (chỉ đếm được số file không tiền tố)
    const basic = rows.filter((r) => r.group === 'general_document' && !r.sr).length;
    const needBasic = ctx.north ? 3 : 2;
    if (basic < needBasic)
      addF('warn', `Chỉ có ${basic} file cơ bản (không tiền tố) — cần ít nhất hộ chiếu + ảnh thẻ${ctx.north ? ' + 1 trang trắng hộ chiếu (miền Bắc)' : ''}`);

    // 8. quan hệ
    if (RELATION_REQUIRED.includes(visa) && !String(ctx.relation || '').trim())
      addF('err', `Visa ${visa}: chưa chọn "Quan hệ" (người mời là gì của người xin visa)`);

    // 7. Q / S2: giấy bắt buộc
    if (visa === 'Q1' || visa === 'Q2') {
      if (!has('qmoi')) addF('err', 'Thiếu giấy tờ người mời qmoi_1 (CCCD / hộ chiếu người Trung Quốc)');
      if (!has('qcm')) addF('err', 'Thiếu giấy chứng minh quan hệ qcm_1');
    }
    if (visa === 'S2') {
      const n = nums('smoi');
      const miss = [1, 2].filter((i) => !n.includes(i)).map((i) => `smoi_${i}`);
      if (miss.length) addF('err', `Thiếu ${miss.join(', ')} (smoi_1 = hộ chiếu người mời, smoi_2 = giấy cư trú ở TQ)`);
      if (!has('scm')) addF('err', 'Thiếu giấy chứng minh quan hệ scm_1');
    }

    // 12. miền Bắc: số file quan hệ được tải lên
    const relS = visa === 'S2' ? 'scm' : 'qcm';
    if (ctx.north && NORTH_REL_MAX[visa] && (bySeries[relS] || []).length > NORTH_REL_MAX[visa]) {
      const sorted = bySeries[relS].map((r) => splitName(r.rel).base).sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
      addF('warn', `Miền Bắc chỉ tải lên ${NORTH_REL_MAX[visa]} file ${relS}_ đầu tiên — sẽ KHÔNG tải: ${sorted.slice(NORTH_REL_MAX[visa]).join(', ')}`);
    }

    // 9, 10. M / F (người sau trong đoàn không có giấy riêng), X
    // Thiếu (một phần hay hết) -> chỉ nhắc: người sau trong đoàn lấy giấy của người đầu bằng "Áp dụng M/F".
    const groupCheck = (list, code, owner) => {
      const missing = list.filter((s) => !has(s));
      if (missing.length)
        addF('warn', `Thiếu giấy ${owner}: ${missing.join(', ')} — người sau trong đoàn thì PHẢI bấm "Áp dụng ${code}" ở tab Chạy curl trước khi Chạy`);
    };
    if (visa === 'M') groupCheck(M_FILES, 'M', 'công ty');
    if (visa === 'F') groupCheck(F_FILES, 'F', 'trường');
    if ((visa === 'X1' || visa === 'X2') && !has('xnh') && !has('xjw'))
      addF('err', 'Thiếu giấy của trường: xnh_1 (giấy báo nhập học) hoặc xjw_1 (JW201 / JW202)');

    // 13. dưới 18: có 1 giấy duoi18_ thì phải đủ bộ
    const u18 = rows.filter((r) => r.group === 'minor_document' || r.group === 'minor_payer').map((r) => r.lname.replace(/[_-]\d+$/, ''));
    if (u18.length && U18_VISAS.includes(visa)) {
      const miss = U18_NEED.filter((n) => !u18.includes(n));
      if (miss.length) addF('err', `Hồ sơ dưới 18 thiếu: ${miss.join(', ')}`);
    }

    // 14. người đi cùng: chỉ nhắc
    if (CV_VISAS.includes(visa) && !has('cv'))
      addF('info', 'Có người đi cùng (gia đình / đoàn) thì thêm hộ chiếu của họ: cv_1, cv_2…');

    const level = (issues) => (issues.some((i) => i.level === 'err') ? 'err' : issues.some((i) => i.level === 'warn') ? 'warn' : 'ok');
    const out = rows.map((r) => ({ rel: r.rel, group: r.group, issues: r.issues, level: level(r.issues) }));
    const all = [...out.flatMap((r) => r.issues), ...folder];
    return {
      files: out,
      folder,
      errors: all.filter((i) => i.level === 'err').length,
      warns: all.filter((i) => i.level === 'warn').length,
    };
  }

  const api = { checkFolder, checkFile, n8nGroup, slug, series, NORTH_REL_MAX };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.FileCheck = api;
})(typeof window !== 'undefined' ? window : globalThis);
