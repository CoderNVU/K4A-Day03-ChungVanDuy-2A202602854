# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Chung Văn Duy
> **Mã Sinh Viên / Mã Học viên:** 2A202602854
> **Chủ đề Lựa chọn:** Trợ lý Học vụ & Tra cứu Lịch thi VinUni

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Các yêu cầu phức tạp cần được chia thành nhiều bước nối tiếp, chẳng hạn tra cứu hồ sơ sinh viên, xác định cố vấn phụ trách rồi mới đặt lịch tư vấn. |
| **2. Tool Interaction** | 5 / 5 | Agent phải tương tác với MCP Server để gọi công cụ tra cứu học vụ và công cụ đặt lịch, thay vì chỉ sinh câu trả lời từ kiến thức của mô hình. |
| **3. Dynamic Decision** | 4 / 5 | Công cụ và hành động tiếp theo phụ thuộc vào ý định của người dùng và kết quả trả về từ bước tra cứu trước đó. |
| **4. Long Horizon Goal** | 3 / 5 | Agent cần duy trì mục tiêu xuyên suốt chuỗi tra cứu và đặt lịch, tuy nhiên quy trình hiện tại tương đối ngắn và có phạm vi rõ ràng. |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | Bài toán đạt trên 12/20 và phù hợp để triển khai dưới dạng Agentic System. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

**Cấu hình nghiệm thu:** `GeminiProvider`, model `gemini-3.6-flash`, Native Tool Calling qua `MCPAcademicServer`.

Test suite đã thực thi đủ 5 test case và sinh 10 sự kiện trong `docs/trace_waterfall.json`. Đoạn dưới đây trích nguyên chuỗi TC02 chạy thành công qua Gemini API thật: Gemini quyết định gọi `academic_query`, MCP Server trả Observation và Gemini tổng hợp Final Answer.

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 26020.71
  },
  {
    "step": 2,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Thông tin học vụ của sinh viên SV2026001 đã được tra cứu thành công: Nguyễn Văn An, lớp AI-K4, GPA 3.85, trạng thái Đang học, cố vấn PGS.TS Nguyễn Văn A.",
    "latency_ms": 32341.91
  }
]
```

### Kết quả chi tiết bộ kiểm thử

| Test Case | Kết quả | Chuỗi hành động quan sát được |
| :--- | :---: | :--- |
| TC01 — Direct Query | PASS | Gemini trả lời trực tiếp, không gọi Tool. |
| TC02 — Single Tool Query | PASS | `academic_query` → `SUCCESS` → Final Answer. |
| TC03 — Appointment Booking | PASS | `schedule_appointment` → `SUCCESS` → xác nhận booking. |
| TC04 — Multi-step Reasoning | PASS | `academic_query` → lấy `advisor` → `schedule_appointment` → Final Answer. |
| TC05 — Edge Case | PASS | `academic_query` → `NOT_FOUND` → phản hồi không bịa đặt dữ liệu. |

> **Ghi chú giới hạn môi trường:** Gemini API thật đã được xác nhận hoạt động end-to-end ở TC01 và TC02. Trong toàn bộ suite, 6/10 lượt suy luận dùng Gemini API thật; 4/10 lượt còn lại tự động chuyển sang Mock Offline do Gemini Free Tier trả `429 RESOURCE_EXHAUSTED`. Kết quả Tool Execution và Observation vẫn được thực thi đầy đủ qua MCP Server cục bộ. Giới hạn này thuộc quota của dịch vụ bên ngoài, không phải lỗi của ReAct loop hay MCP dispatcher.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent kết nối, gọi Native Tool Calling thành công qua Gemini API.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

### Tự kiểm tra trước khi nộp

- [x] Bảng Agentic Fit đạt trên ngưỡng phù hợp triển khai Agentic System.
- [x] Hai Tool Schemas khai báo đủ tên, mô tả, kiểu dữ liệu và trường bắt buộc.
- [x] MCP Server đóng gói kết quả theo JSON-RPC 2.0.
- [x] ReAct loop hỗ trợ nhiều vòng và giới hạn tối đa bằng `MAX_ITERATIONS`.
- [x] Test đa bước sử dụng Observation trước làm đầu vào cho hành động tiếp theo.
- [x] Test biên trả `NOT_FOUND` và không bịa đặt dữ liệu.
- [x] Waterfall Trace có Thought, Action, Observation, Final Answer và `latency_ms`.
- [ ] Commit, push repository cá nhân và nộp URL trên LMS VLearn.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
