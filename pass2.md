# passers/passer2.py 詳細說明

這份檔案的核心是 `Passer2` 類別，負責 assembler 的第二階段（Pass 2）：

1. 讀取已經完成 `LOCCTR` 與 symbol table 的程式行（`ParsedLine`）。
2. 根據指令格式與定址模式產生 object code。
3. 組裝成 SIC/XE 的 `H/T/M/E` records。

---

## 1. 類別定位與輸入輸出

`Passer2` 定義在 `passers/passer2.py`，繼承抽象基底 `Passer[list[str]]`。

### 建構子輸入

- `sic_mode: bool`
  - `True` 代表嚴格 SIC 模式（禁止 SIC/XE-only 語法）。
- `lines: list[ParsedLine]`
  - 由 parser 解析、Pass1 已補上 `loc` 的程式行。
- `pass1_result: Pass1Result`
  - 含 `start_address`、`program_length`、`program_name`、`symbol_table`。

### run() 輸出

- `list[str]`
  - 完整 object program records：
    - Header (`H`)
    - Text (`T`)
    - Modification (`M`)
    - End (`E`)

---

## 2. 內部狀態

`Passer2` 在初始化時建立以下重要狀態：

- `base_address`
  - 處理 `BASE` directive 用於 base-relative。
- `execution_address`
  - 預設為 `start_address`，若 `END label` 會改成該 label 地址。
- `modification_records`
  - format-4 非立即值需要加 `M` record。
- `text_records`
  - 暫存累積好的 `(address, hex_data)`。
- `text_start`, `text_data`
  - 目前正在累積中的 T-record 起點與 hex 內容。

---

## 3. run() 主流程

`run()` 逐行掃描 `lines`：

1. `START`
   - 略過（Pass2 不產生 object code）。

2. `END`
   - 若有 operand（`END FIRST`），會解析 symbol 並更新 `execution_address`。
   - 然後結束掃描。

3. opcode / directive 分流
   - 先判斷是否 `+` extended。
   - 若是 opcode：按 format 1 / 2 / 3（含 4）處理。
   - 若是 directive：處理 `WORD/BYTE/RESB/RESW/BASE`。

4. object code 加入當前 T-record
   - 若超過 `TEXT_RECORD_HEX_LIMIT`（60 hex chars）就先 flush。

5. 最後收尾
   - flush 最後一筆 T-record。
   - 依序組 `H -> T* -> M* -> E`。

---

## 4. 數值與符號處理 helpers

### `_normalize_signed_decimal` / `_is_decimal` / `_parse_decimal`

- 把 `+ 1 2`、`-  35` 這種輸入整理成標準十進字串。
- 提供通用十進檢查與轉整數。

### `_resolve_symbol_or_decimal`

- 若 operand 是十進值（且允許）就直接轉數字。
- 否則查 `symbol_table`。
- 失敗會丟 `SymbolResolutionError`。

---

## 5. Directive 轉換

### `WORD`

- `_encode_word_operand`：
  - 必須是十進整數。
  - 檢查範圍 `WORD_MIN ~ WORD_MAX`。
  - 轉成 24-bit hex（6 hex digits）。

### `BYTE`

- `_encode_byte_operand`：
  - `X'..'`：直接用 hex body（長度必須偶數）。
  - `C'..'`：每個字元轉 ASCII hex。

### `RESB / RESW`

- 不產生 object code。
- 會先 `_flush_text_record()`，切斷 T-record。

### `BASE`

- 在 SIC/XE 模式下可用，解析 operand 設定 `base_address`。
- SIC 模式下丟 `SicModeError`。

---

## 6. Format 2 編碼

方法：`_encode_format2_instruction`

主要處理：

- operand 數量檢查（最多 2 個）。
- `SVC` 特規：單一數值 operand，且需在 `SVC_MIN..SVC_MAX`。
- shift 指令（`SHIFTL`, `SHIFTR`）第二欄為位移量，範圍 `SHIFT_MIN..SHIFT_MAX`。
- 其他 format-2 指令：operand 視為 register，查 `REGISTERS`。

---

## 7. Format 3/4 編碼

方法：`_encode_format34_instruction`

### 步驟 A：解讀 addressing mode

- `#`：immediate，設定 `n=0, i=1`
- `@`：indirect，設定 `n=1, i=0`
- 預設 simple：`n=1, i=1`
- 解析 `,X` 決定 index flag `x=1`

### 步驟 B：解析 target

- immediate 且為純數字 -> immediate numeric。
- 否則用 symbol table 解析地址。

### 步驟 C：format 4（extended）

- 使用 20-bit displacement。
- immediate numeric 要過 `FORMAT4_IMMEDIATE_MIN..MAX`。
- 非 immediate 需要加 `M` record：`M{loc+1:06X}05`。

### 步驟 D：format 3

優先順序：

1. immediate numeric：
   - 走 12-bit displacement，檢查 `FORMAT3_IMMEDIATE_MIN..MAX`。
2. SIC/XE PC-relative：
   - `PC_RELATIVE_MIN..MAX`。
3. SIC/XE BASE-relative：
   - `BASE_RELATIVE_MIN..MAX`，需先有 `BASE`。
4. fallback SIC direct（若條件允許）：
   - 15-bit direct，範圍 `SIC_DIRECT_MIN..MAX`。

若都不成立，會拋對應 `AddressingModeError`。

---

## 8. RSUB 特例

在 `run()` 內直接處理：

- `RSUB` 不可帶 operand。
- SIC 模式產生 SIC 對應碼。
- SIC/XE 模式產生 `n/i` 設定後的碼；若 extended 會走 4-byte 版本。

---

## 9. T-record 累積機制

### `_append_object_code`

- 確保 `line.loc` 存在。
- 初次寫入設定 `text_start`。
- 若加入後超過 60 hex chars，先 flush 再開新段。

### `_flush_text_record`

- 把 `(text_start, text_data)` 推入 `text_records`。
- 清空目前累積緩衝。

---

## 10. 最終 record 組裝

`run()` 結尾：

1. Header:
   - `H{program_name(6)}{start_address}{program_length}`
2. Text:
   - 每段 `T{addr}{len}{data}`
3. Modification:
   - 依序加入 `M...`
4. End:
   - `E{execution_address}`

---

## 11. 錯誤設計重點

`Passer2` 會針對錯誤語義丟不同例外類型，便於上層做診斷：

- `SicModeError`: SIC 模式違規
- `RegisterOperandError`: format2 register/operand 問題
- `RangeValidationError`: 數值超範圍
- `SymbolResolutionError`: symbol 或 operand 解析失敗
- `AddressingModeError`: 定址模式不可達/不合法
- `Pass2Error`: 其餘 pass2 邏輯錯誤

這讓 CLI 可以輸出更精確且可定位的訊息。

---

## 12. 整體總結

`Passer2` 的責任是把「語法層的 assembly 表示」轉成「機器可載入的 object records」。
它的核心價值是：

- 把 SIC/XE 的指令格式與定址規則明確化。
- 把 range/symbol/addressing 的失敗點提早、精準地報出。
- 穩定地輸出符合規格的 `H/T/M/E` records。

