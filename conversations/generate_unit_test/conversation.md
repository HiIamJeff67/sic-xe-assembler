# 此檔案紀錄使用 Codex 輔助生成測試 Assembler 用之腳本和程式碼

## 我：

接著我想請你使用一些函式庫或是工具做 unit test，我會給你一些測資，他們放在 test 內，test/original/ 就是輸入的測資，然後 test/target/ 內就是對應期望的輸出，他們的黨名是一一對應的，請你使用一些測試工具，並且讓這個測試工具透過 CLI 操作並且可以輸出最後的對比結果，然後函式庫的初始化需要考量可能會有其他人 clone 這個 project，所以你可能需要一個 venv 還要搭配撰寫一些 scripts 幫助他人初始建置該環境，期望的效果是：
如果有用到外部套件，他可以在 clone 下來後直接跑一個 command 去完成環境建置，然後再透過我們的指令來 run 相對應的測試並且看到所有測試的結果或是他可能想指定測試的檔案有哪些（指定檔名），如果 test/original/ 當中沒有對應檔名的 .asm，或 test/target/ 當中沒有對應檔名的 .obj，那就告知他一下具體是缺了什麼

## Codex：

已完成，你要的測試工具鏈已建好，現在可以：

- 一鍵建置測試環境（`venv` + 套件安裝）
- 用 CLI 跑全部測資
- 指定檔名跑部分測資
- 若 `.asm` / `.obj` 缺檔，直接列出缺哪個檔案

**主要變更**

- 測試執行 CLI 與參數解析：[scripts/run_tests.py](/Users/jeff/Desktop/Projects/sic-xe-assembler/scripts/run_tests.py:9)
- 測試資料配對、檔名正規化、缺檔檢查、mode 載入：[tests/case_loader.py](/Users/jeff/Desktop/Projects/sic-xe-assembler/tests/case_loader.py:90)
- pytest 自訂參數（`--case`、`--default-mode`）與收集期檢查：[tests/conftest.py](/Users/jeff/Desktop/Projects/sic-xe-assembler/tests/conftest.py:8)
- 實際比對測試（呼叫 assembler CLI 產生輸出後與 target 比對）：[tests/test_object_programs.py](/Users/jeff/Desktop/Projects/sic-xe-assembler/tests/test_object_programs.py:9)
- 一鍵環境建置腳本：[scripts/setup_test_env.sh](/Users/jeff/Desktop/Projects/sic-xe-assembler/scripts/setup_test_env.sh:1)
- 測試入口腳本：[scripts/run_tests.sh](/Users/jeff/Desktop/Projects/sic-xe-assembler/scripts/run_tests.sh:1)
- mode 設定檔（可針對 case 指定 `sic`/`sicxe`）：[test/cases.json](/Users/jeff/Desktop/Projects/sic-xe-assembler/test/cases.json:1)
- 測試依賴：[requirements-dev.txt](/Users/jeff/Desktop/Projects/sic-xe-assembler/requirements-dev.txt:1)
- pytest 設定：[pytest.ini](/Users/jeff/Desktop/Projects/sic-xe-assembler/pytest.ini:1)
- 使用說明補到 README：[README.md](/Users/jeff/Desktop/Projects/sic-xe-assembler/README.md:32)

**你可以直接用的指令**

```bash
./scripts/setup_test_env.sh
./scripts/run_tests.sh
./scripts/run_tests.sh addexample studentexample
./scripts/run_tests.sh addexample.asm textbookexample.obj
```

**實測結果**

- `./scripts/run_tests.sh`：3 passed
- `./scripts/run_tests.sh addexample studentexample`：2 passed
- `./scripts/run_tests.sh not_exist_case`：會明確報
  - 缺 `test/original/not_exist_case.asm`
  - 缺 `test/target/not_exist_case.obj`
