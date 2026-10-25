# Chuyển giao: UV-Vis (thường/đạo hàm) + NMR cho phân tích định tính cao chiết

Ngày: 2026-10-25
Phiên gốc: phiên Claude Code trên đám mây (claude.ai/code), nhánh `claude/bold-cannon-vmfmr5`, repo `hoangphu23101989-max/project`.
Lý do chuyển: container đám mây bị chặn mạng tới các máy chủ xuất bản (doi.org, link.springer.com, mdpi.com, pmc.ncbi.nlm.nih.gov, europepmc, api.unpaywall.org, api.crossref.org, api.openalex.org) và không có quyền ghi file lên máy người dùng. Việc tải PDF phải làm trên máy cục bộ.

---

## 1. Lấy mã về máy

```bash
git clone https://github.com/hoangphu23101989-max/project.git
cd project
git checkout claude/bold-cannon-vmfmr5
cd uvvis-dao-ham
```

Môi trường Python cần: `numpy scipy scikit-learn pandas matplotlib requests`.

```bash
pip install numpy scipy scikit-learn pandas matplotlib requests
```

---

## 2. Bối cảnh và các kết luận đã thống nhất

1. **Không có skill công khai nào trên GitHub** chuyên về phổ đạo hàm UV-Vis. Skill gần nhất là `uv-vis-nir-analyzer` (a5c-ai/babysitter, MIT), chỉ bao quát LSPR, đồ thị Tauc và Beer–Lambert. Vì vậy cần tự xây skill.
2. **Vai trò của UV-Vis trong cao chiết thô:** chỉ dùng để sàng lọc/gợi ý nhóm chromophore, lập dấu vân tay phổ để phân biệt mẫu (kết hợp hóa trắc học), và phân giải dải chồng lấp (sắc tố). Không dùng để định danh từng hợp chất.
3. **Kết hợp với ¹H NMR và HSQC** (người dùng xác nhận sẽ dùng). Logic: UV-Vis tạo giả thuyết về nhóm chất; ¹H xác định kiểu thế, cấu hình anomer, cấu hình *trans*; HSQC tách tín hiệu chồng lấp và cho cặp ¹H–¹³C đặc trưng. Khuyến nghị thêm HMBC (vị trí gắn đường/acyl) và LC-HRMS (công thức phân tử).
4. **Mức tin cậy khi công bố:** UV + ¹H + HSQC đối chiếu tài liệu, không có chất chuẩn → mức 2 MSI (putatively annotated). Mức 1 cần chất chuẩn thật (spiking HSQC + phổ đạo hàm UV của chuẩn).
5. **Văn phong** cho mọi tài liệu: học thuật, cấp độ tiến sĩ, chia phần rõ ràng, không hoa mỹ, không ẩn dụ.

---

## 3. Những gì đã có trong thư mục này

| File | Nội dung | Trạng thái |
|---|---|---|
| `danh_muc_bai_bao.csv` | 41 tài liệu, 5 nhóm: A (tổng quan), B (đạo hàm cho flavonoid/cao chiết), C (đạo hàm + hóa trắc học/xác thực), D (sắc tố), E (giới hạn/đối chứng). Cột: id, nhom, tac_gia, nam, tieu_de, tap_chi, tap_trang, doi, pmid, pmcid, ghi_chu | Xong. Metadata chủ yếu lấy từ PubMed |
| `references.bib` | Sinh tự động từ CSV | **Cần sửa** (xem mục 4.1) |
| `CHUYEN_GIAO.md` | File này | |

Các mục trong CSV chưa có DOI hoặc chưa xác minh:
- R03 Karpińska 2004 (Talanta 64:801–822) và R04 Talsky 1994 (sách): trích dẫn từ trí nhớ, cần kiểm tra.
- B03, B04 (J AOAC Int), B09 (tiếng Trung), C05 (tiếng Trung), D12 (tiếng Hungary), E01 Hostettmann 1984: chưa có DOI.
- C15 Mahida et al. 2026 (Chemistry Africa 9(6)): chưa xác minh DOI.
- C02 Casoni et al. 2024: DOI `10.1186/s40543-024-00428-2`, lấy từ URL trang Springer.

Các bài truy cập mở đã biết: C02, C08 (PMC7914811), C09 (PMC8777600), D04 (PMC1389882), D07 (PMC2668582), D11 (Optica Express).

---

## 4. Việc còn lại, theo thứ tự ưu tiên

### 4.1. Sửa `references.bib`
Hiện tên tác giả có dạng `Sanchez Rojas F and Bosch Ojeda C`. BibTeX/Zotero sẽ hiểu sai họ và tên. Cần sinh lại theo dạng `Sanchez Rojas, F. and Bosch Ojeda, C.`. Có thể bỏ khóa `pmid`/`pmcid` không chuẩn, hoặc đưa chúng vào `note`. Cách khác: nhập DOI trực tiếp vào Zotero (Add Item by Identifier), để Zotero tự lấy metadata.

### 4.2. Script tải bài báo: `tai_bai_bao.py` (chưa viết)
Đặc tả:
- Đầu vào: `danh_muc_bai_bao.csv`. Tham số `--email` (bắt buộc cho Unpaywall) và `--out pdf/`.
- Với mỗi dòng có DOI, gọi `https://api.unpaywall.org/v2/{doi}?email=...`, lấy `best_oa_location.url_for_pdf`. Nếu không có, thử Europe PMC: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&format=json&resultType=core`, rồi lấy `fullTextUrlList` có `documentStyle == "pdf"` và `availability` là Open access. Nếu dòng có `pmcid`, tải thêm từ `https://europepmc.org/articles/{pmcid}?pdf=render`.
- Đặt tên file `{id}_{tacgia}{nam}.pdf`. Kiểm tra header `%PDF` trước khi lưu. Nghỉ khoảng 1 giây giữa các request. Có tùy chọn `--dry-run`.
- Ghi `ket_qua_tai.csv` (id, doi, trạng thái, nguồn, đường dẫn) và `can_truy_cap_thu_vien.csv` (các bài không có bản mở, kèm link `https://doi.org/{doi}` để truy cập qua thư viện trường).
- **Chỉ tải bản truy cập mở hợp pháp.** Không dùng nguồn vi phạm bản quyền.
- Cách thay thế không cần script: nhập `references.bib` hoặc danh sách DOI vào Zotero, chọn tất cả, rồi dùng "Find Available PDF".

### 4.3. Script phổ đạo hàm Savitzky–Golay + thống kê: `uvvis_derivative.py` (chưa viết)
Đặc tả đã thống nhất:
- **Đầu vào:** CSV dạng rộng (cột 1 là bước sóng, các cột sau là mẫu). Tùy chọn file metadata (`sample,group`). Tùy chọn chuyển vị.
- **Tiền xử lý:**
  - Cắt vùng λ. Nội suy về lưới đều nếu bước đo không đều.
  - Trừ offset nền (tùy chọn).
  - Chuẩn hóa SNV/area/max (tùy chọn).
- **Đạo hàm:**
  - `scipy.signal.savgol_filter(y, window, polyorder, deriv=n, delta=step)`, n = 0–4.
  - Kiểm tra window lẻ, window > polyorder ≥ n.
  - Báo cáo Δλ hiệu dụng = window × step (nm).
- **Đặc trưng:**
  - Tìm cực tiểu của D2 và D4 (tương ứng λmax của dải gốc) bằng `find_peaks` trên −D2, ngưỡng prominence tương đối.
  - Xuất bảng vị trí dải theo mẫu.
  - Ước lượng S/N theo bậc đạo hàm.
- **Thống kê:**
  - PCA: scores, loadings, phương sai giải thích.
  - HCA với khoảng cách 1 − Pearson r, liên kết average (theo Casoni et al. 2024), vẽ dendrogram.
  - Ma trận tương đồng cosin.
  - Nếu có nhóm: Pipeline(PCA → LDA) trong StratifiedKFold hoặc LOO. **PCA phải fit bên trong CV** để tránh rò rỉ dữ liệu. Báo cáo độ chính xác và ma trận nhầm lẫn.
  - So sánh độ chính xác theo bậc 0–4, như Simion & Sârbu 2019.
- **Đầu ra** (`--out`): CSV (phổ đã xử lý, scores, loadings, vị trí dải), PNG (phổ gốc, phổ đạo hàm, score plot, loading plot, dendrogram, biểu đồ so sánh bậc), `summary.json`, `report.md` (ghi đủ tham số để người khác lặp lại).
- **`--demo`:** sinh dữ liệu giả từ các dải Gauss: flavone band I khoảng 335 nm, flavonol khoảng 370 nm, caffeoyl khoảng 325 nm kèm vai 300 nm, band II khoảng 255–270 nm. Thêm nhiễu; 3 nhóm × 8 mẫu. Dùng để kiểm thử, **không phải dữ liệu thật**.
- Mã viết bằng tiếng Anh, tài liệu hướng dẫn bằng tiếng Việt.

### 4.4. Skill kết hợp UV-Vis và NMR (chưa làm)
Nên dùng skill `skill-creator` (anthropic-skills) để dựng đúng cấu trúc. Vị trí đề xuất: `.claude/skills/uvvis-nmr-extract/`.

```
SKILL.md                          quy trình 5 bước: chuẩn bị mẫu → UV bậc 0 + D2 (giả thuyết) → ¹H (kiểu thế) → HSQC (dereplication) → ma trận bằng chứng + mức MSI
scripts/uvvis_derivative.py       từ mục 4.3
scripts/nmr_uv_crosscheck.py      nhận danh sách pic HSQC (δH, δC, loại CH/CH2/CH3) + vị trí dải UV; đối chiếu bảng tra; xuất ma trận bằng chứng
scripts/shy_correlation.py        SHY/STOCSY: tương quan phổ UV đạo hàm với ¹H khi có nhiều mẫu/phân đoạn; chuẩn hóa theo khối trước khi trộn dữ liệu
references/chromophore_nmr_table.md   bảng tra UV ↔ ¹H ↔ HSQC (xem mục 5); mở rộng cho xanthone, coumarin, alkaloid
references/literature.md          tóm tắt có chú giải từ danh_muc_bai_bao.csv + tài liệu NMR (mục 6)
references/reporting_checklist.md tham số bắt buộc phải báo cáo; các lỗi phản biện hay bắt
```

Câu hỏi còn mở (cần hỏi người dùng):
1. Họ thực vật hoặc nhóm chất dự kiến.
2. Dung môi chiết và dung môi NMR (DMSO-d₆ hay CD₃OD).
3. Định dạng file xuất từ máy UV (Shimadzu UVProbe, Agilent Cary, JASCO...).
4. Ngôn ngữ của skill.

---

## 5. Bảng tra chéo UV ↔ NMR đã soạn (giá trị điển hình, cần kiểm tra theo dung môi)

| Nhóm | UV / phổ đạo hàm | ¹H | HSQC δH/δC |
|---|---|---|---|
| Flavone | band I 304–350, band II 250–280 nm | H-3: s, 6,6–6,9 | ~6,7 / 103–105 |
| Flavonol (3-OH tự do) | band I 352–385 nm | không có H-3 | không có CH tại C-3 (~136, C bậc bốn) |
| Flavonol 3-O-glycosid | band I ~350–362 nm (trùng vùng flavone) | anomer 5,2–5,6 | ~5,3–5,5 / 101–104 |
| Isoflavone | band II 250–270 nm mạnh; band I là vai 300–330 nm | H-2: s, 8,0–8,4 | ~8,2 / 152–154 |
| Flavanone | band II 270–295 nm; band I là vai | H-2: dd 5,3–5,5; H-3: hai dd 2,7 và 3,1 | 5,4 / 78–79; CH₂ ~42–43 |
| A-ring 5,7-diOH | | H-6 ~6,2, H-8 ~6,4 (d, J ≈ 2 Hz) | 6,2 / 98–99; 6,4 / 93–94 |
| B-ring thế 4′ | | AA′BB′: ~8,0 (d, 8,8 Hz) và ~6,9 | 8,0 / 129–131; 6,9 / 115 |
| B-ring thế 3′,4′ | band I dịch về bước sóng dài | ABX: 7,5–7,7; 6,9 (d, 8,5 Hz) | 7,6 / 115–116; 7,5 / 120–122 |
| Rhamnose | | CH₃: d, 0,8–1,2 | ~1,0 / 17–18 |
| Caffeoyl/cinnamoyl | ~325 nm + vai ~300 nm | 2 d, J ≈ 16 Hz: ~7,5 và ~6,3 | 7,5 / 145–146; 6,3 / 114–115 |
| Anthocyanin (môi trường acid) | 500–540 nm | H-4: s, ~8,9–9,0 | ~9,0 / 135–137 |
| Carotenoid | 3 đỉnh trong vùng 400–500 nm | olefin 6,1–6,7 | |
| Chlorophyll a | ~430 và ~662 nm | | |

---

## 6. Tài liệu NMR và trộn dữ liệu dùng cho skill (chưa có trong CSV)

| Chủ đề | Tài liệu | DOI |
|---|---|---|
| Dereplication HSQC trên cao thô | NPid, Anal. Chem. 2020 | 10.1021/acs.analchem.9b05363 |
| | HSQCid, Anal. Chem. 2025 | 10.1021/acs.analchem.4c03102 |
| | ReCQC, Anal. Chem. 2026 | 10.1021/acs.analchem.5c05654 |
| | Dereplication với ¹H/HSQC/COSY tối thiểu, Org. Biomol. Chem. 2015 | 10.1039/c5ob01713k |
| | ¹³C dereplication không phân đoạn, J. Nat. Prod. 2017 | 10.1021/acs.jnatprod.6b01063 |
| | UHPLC-PDA-HRMS + HSQC (*Laurencia*), Phytochemistry 2015 | 10.1016/j.phytochem.2014.10.007 |
| | Acid oleanolic/ursolic trong cao bằng HSQC + HMBC, Anal. Chim. Acta 2009 | 10.1016/j.aca.2009.01.021 |
| | *Artemisia annua*: ¹H/TOCSY/HSQC/HMBC, Magn. Reson. Chem. 2020 | 10.1002/mrc.4971 |
| SHY/STOCSY/trộn dữ liệu | SHY, Crockford et al., Anal. Chem. 2006 | 10.1021/ac051444m |
| | DAFdiscovery, Phytochem. Anal. 2023 | 10.1002/pca.3178 |
| | ¹H NMR + UV-Vis, lá atiso, Food Chem. 2022 | 10.1016/j.foodchem.2021.131979 |
| | NMR + UV-Vis trộn mức thấp, *Citrus* Tacle, Antioxidants 2023 | 10.3390/antiox12010002 |
| | ¹H NMR + UV-Vis, phẩm màu Sudan, Talanta 2011 | 10.1016/j.talanta.2011.02.014 |
| | NMR-HetCA, Anal. Chem. 2024 | 10.1021/acs.analchem.4c05080 |
| | HetCA/STOCSY *Artemisia arborescens*, ChemMedChem 2026 | 10.1002/cmdc.70421 |
| Nền tảng (từ trí nhớ, chưa kiểm tra) | Mabry, Markham & Thomas 1970, *The Systematic Identification of Flavonoids*; Sumner et al. 2007, MSI minimum reporting standards | |

---

## 7. Lời nhắc để dán vào phiên Claude Code trên máy

```
Đọc uvvis-dao-ham/CHUYEN_GIAO.md. Tiếp tục theo mục 4, theo thứ tự:
(4.1) sửa references.bib;
(4.2) viết tai_bai_bao.py, chạy với email dhp231089@gmail.com, chỉ tải bản truy cập mở hợp pháp vào uvvis-dao-ham/pdf/, báo cáo bài nào cần truy cập qua thư viện;
(4.3) viết uvvis_derivative.py theo đặc tả, kiểm thử bằng --demo;
(4.4) dùng skill-creator để dựng skill .claude/skills/uvvis-nmr-extract/.
Văn phong học thuật, cấp độ tiến sĩ, chia phần rõ ràng, không hoa mỹ.
Không đưa file PDF có bản quyền lên GitHub (thêm uvvis-dao-ham/pdf/ vào .gitignore).
```
