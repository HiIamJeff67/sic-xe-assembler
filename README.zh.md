# SIC/XE 組譯器專案

本專案實作一個支援 SIC 與 SIC/XE 架構的雙通道組譯器，提供命令列組譯、物件檔比對、與自動化測試工具。

---

**目錄**

- [功能特色](#功能特色)
- [快速開始](#快速開始)
- [組譯 .asm 檔案](#組譯-asm-檔案)
- [物件檔格式](#物件檔格式)
- [物件檔比對工具](#物件檔比對工具)
- [測試流程](#測試流程)
- [測資模式與設定](#測資模式與設定)
- [常數與限制](#常數與限制)
- [注意事項](#注意事項)

---

## 功能特色

- 支援 SIC 及 SIC/XE 組譯模式
- 命令列組譯與測試
- 整合 pytest 的自動化測試
- 物件檔比對工具
- 測資模式可自訂，測資選擇彈性

---

## 快速開始

### 1. 建立測試環境

- 建立 Python 虛擬環境並安裝依賴：
  ```bash
  ./scripts/setup_test_env.sh
  ```

### 2. 單純組譯 .asm 檔案

- 將某個 .asm 檔案編譯成 .obj：
  ```bash
  python3 assembler.py 路徑/檔名.asm
  ```
- 指定輸出檔名：
  ```bash
  python3 assembler.py 路徑/檔名.asm -o 路徑/輸出.obj
  ```
- 強制 SIC 模式：
  ```bash
  python3 assembler.py 路徑/檔名.asm --sic
  ```

---

## 組譯 .asm 檔案

- 組譯器接受 `.asm` 檔案，產生 `.obj` 物件檔。
- 可用 `-o` 指定輸出檔名，否則預設與來源同名、附檔名為 .obj。
- `--sic` 參數可啟用嚴格 SIC 模式，禁用 SIC/XE 專屬語法與指令。

---

## 物件檔格式

- 物件檔內容依序為：
  - Header (`H`)
  - 一或多個 Text (`T`) 記錄
  - 零或多個 Modification (`M`) 記錄
  - End (`E`)
- 每個 Text 記錄最多 60 個十六進位字元，超過則換新段。
- 範例：
  ```
  HADDEX 001000000015
  T0010001200100C18100F0C10124C0000000003000005
  E001000
  ```

---

## 物件檔比對工具

- 比對兩個物件檔（自動忽略行尾換行）：
  ```bash
  python3 compareobjectcode.py 路徑/產生.obj 路徑/標準.obj
  ```
- 工具會回報第一個差異的行與欄位。

---

## 測試流程

- 所有測資皆放於 `test/` 目錄。
- 執行全部測資：
  ```bash
  ./scripts/run_tests.sh
  ```
- 執行指定測資（可用檔名或名稱）：
  ```bash
  ./scripts/run_tests.sh addexample studentexample
  ./scripts/run_tests.sh addexample.asm textbookexample.obj
  ```
- 測資需有成對的 `.asm`（輸入）與 `.obj`（標準輸出）於 `test/original/` 與 `test/target/`。
- 缺檔時測試會直接報錯並停止。

---

## 測資模式與設定

- 可於 `test/cases.json` 設定各測資模式（SIC 或 SIC/XE）：
  ```json
  {
    "modes": {
      "addexample": "sic",
      "studentexample": "sic",
      "textbookexample": "sic"
    }
  }
  ```
- 未指定時預設為 `sic`，可用 `--default-mode` 覆寫。

---

## 常數與限制

- 記憶體上限：1,048,576 bytes (1M)
- RESB/RESW 最大值：32,767
- Text 記錄長度上限：60 字元
- WORD 範圍：-8,388,608 ~ 8,388,607
- Format 3 immediate：-2,048 ~ 2,047
- Format 4 immediate：-524,288 ~ 524,287
- PC-relative：-2,048 ~ 2,047
- BASE-relative：0 ~ 4,095
- SIC direct：0 ~ 32,767
- SVC：0 ~ 15
- Shift：0 ~ 15

---

## 注意事項

- SIC 模式下，遇到不支援的指令或定址方式會直接報錯。
- 所有路徑皆以專案根目錄為基準。
- 關於組譯器第二階段（Pass 2）的詳細說明，請參考 [pass2.md](pass2.md)。此文件內容由 conversations/generate_pass2_docs/conversation.md 與 Codex 對話協助產生。
- `conversations/` 目錄內皆為我與 Codex 的開發對話紀錄，用於輔助產生說明文件或設計思路，其餘程式與說明皆為本人撰寫。
- 詳細組譯流程與內部邏輯請參考 `pass2.md` 及 `passers/`、`lib/` 目錄下原始碼。
