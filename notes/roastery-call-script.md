# Roastery Call Script — Saigon Coffee Roastery (defect-lot green beans)

**Who:** Saigon Coffee Roastery — 232/13 Võ Thị Sáu, Q3, TPHCM — hotline **0938.80.83.85**
**Backup call:** A Roaster (advertises sample testing).
**Deadline:** buy before mid-August departure to Boston. Green beans keep for months; defects can't be sourced in the US.
**Mission:** the ONE thing this call must establish — can I get real defect beans? Everything else is bonus.

---

## 0. Intro — rough context & scope (~20 seconds, read aloud)

> "Chào anh/chị, em là **Kiên**, sinh viên ngành kỹ thuật. Em đang làm một **đồ án robot + thị giác máy tính**: dùng camera để **nhận diện hạt cà phê nhân bị lỗi** (hạt đen, hạt nâu, hạt vỡ, hạt sâu), rồi một **cánh tay robot nhỏ gắp hạt lỗi ra** — giống khâu lựa tay nhưng ở quy mô để bàn, mục đích học tập và nghiên cứu thôi, không phải thương mại. Em muốn mua **một lượng nhỏ cà phê nhân xanh robusta** — và đặc biệt em đang tìm **hạt lỗi thật** để dạy cho máy nhận biết. Bên mình giúp em được không ạ?"

*(English: Hi, I'm Kien, an engineering student. I'm building a robotics + computer-vision project: a camera detects defective green coffee beans — black, sour, broken, insect-damaged — and a small robot arm picks the defects out, like hand-sorting at desktop scale. Educational/research, not commercial. I want to buy a small quantity of green robusta, and especially real defect beans to train the system. Can you help?)*

Key framing: **student project, small quantity, learning purpose** — makes the odd request ("I want your rejects") make sense and invites goodwill.

---

## 1. PRIORITY 1 — the core question

> "Bên mình có bán **hạt lỗi / hàng loại ra từ khâu lựa tay** riêng không ạ?"
> *(Do you sell the reject/defect beans separated out during hand-sorting?)*

**If YES, follow up:**
- "Trong đó có những loại lỗi nào — **hạt đen, hạt nâu/chua, hạt sâu, hạt vỡ, hạt mốc**? Trộn chung hay tách riêng được?"
  *(Which defect types — black, sour, insect, broken, moldy? Mixed or separable?)*
- "Giá bao nhiêu, mua tối thiểu bao nhiêu? Em cần khoảng **0,5–1 kg hạt lỗi**."
  *(Price? Minimum? I need ~0.5–1 kg of defects.)*

## 2. PRIORITY 2 — fallback if no defect lot

> "Vậy có loại **nhân xanh chưa phân loại / chưa bắn màu** không ạ?"
> *(Do you have UNSORTED green beans — not yet color-sorted?)*

Unsorted beans contain defects at the real-world rate (~a few %) — actually *better* training data than a pure defect bag. Buy **2 kg** if this is the option.

## 3. PRIORITY 3 — the good beans (species matters!)

- "Em cần **1 kg nhân xanh robusta** (cà phê vối) — KHÔNG phải arabica."
  *(1 kg green ROBUSTA — the dataset gap is robusta; arabica datasets already exist.)*
- "Hạt vùng nào ạ — Đắk Lắk, Lâm Đồng?" *(Origin — goes in the dataset card.)*
- "Sàng bao nhiêu?" *(Screen size — dataset card field, also sets bean-size range for the gripper.)*

## 4. PRIORITY 4 — two free asks worth a lot (in-person, with the manager)

1. > "Em **xem khâu lựa tay** một chút được không ạ? Em muốn hiểu người lựa nhìn vào dấu hiệu gì."
   *(May I watch the hand-sorting? Which visual cues do sorters actually use? Photos of accept/reject piles = labeled ground truth.)*
2. > "Nếu được, nhờ một anh/chị lựa hạt **xem giúp ~100 hạt của em và chỉ hạt nào lỗi** — em xin gửi phí."
   *(Could an experienced sorter label ~100 of my beans defect/OK? I'll pay for the time.)*
   → This turns the dataset from "self-guessed labels" into **"annotations verified by a professional sorter, Saigon Coffee Roastery, HCMC"** — a dataset-card line no US lab can produce.

## 5. PRIORITY 5 — logistics

- "Em **ghé trực tiếp** được không? Mấy giờ tiện ạ?" *(Walk-in hours; ask them to set the bags aside.)*
- "**Độ ẩm** hạt khoảng bao nhiêu? Em cần trữ đến tháng 12." *(Moisture ~12.5% = keeps for months. Ask for airtight bagging.)*
- Boston transport: green (unroasted) beans are generally admissible into the US in checked luggage — **declare on the customs form**.

## 6. If they can't help at all

> "Anh/chị biết **chỗ nào bán nhân xanh số lượng nhỏ, có hàng lỗi** không ạ?"
> *(Referral — roasters know their suppliers. One call becomes a lead list.)*
Then call A Roaster next.

---

## Decision tree — what to buy

| They have | Buy | Notes |
|---|---|---|
| Separated defect lot | 1 kg good robusta + 0.5–1 kg defects | Best case — balanced training data |
| Only unsorted/low-grade | 2 kg unsorted | Realistic defect distribution; hand-label |
| Only sorted clean beans | 1 kg clean + get referral for defects | Broken beans can be DIY'd (snap them); black/sour/insect cannot |

**Budget:** standard grade ~150,000–300,000 ₫/kg (report §5); defect/unsorted lots should be at or below the bottom of that band. Total expected: **≤500,000 ₫**.

## Vocabulary cheat sheet

| Vietnamese | English |
|---|---|
| cà phê nhân xanh | green (unroasted) coffee |
| cà phê vối / cà phê chè | robusta / arabica |
| hạt lỗi, hàng loại | defect beans, rejects |
| hạt đen / hạt nâu, hạt chua / hạt sâu / hạt vỡ / hạt mốc | black / sour / insect-damaged / broken / moldy |
| lựa tay / bắn màu | hand-sorting / color-sorter |
| chưa phân loại | unsorted |
| sàng 16, sàng 18 | screen size 16/18 |
| độ ẩm | moisture content |
