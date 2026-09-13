"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        student_match = re.search(r"\bSV\d+\b", prompt, re.IGNORECASE)
        student_id = student_match.group(0).upper() if student_match else ""
        datetime_match = re.search(
            r"\b\d{1,2}:\d{2}(?:\s+ngày)?\s+\d{1,2}/\d{1,2}/\d{4}\b",
            prompt,
            re.IGNORECASE
        )
        datetime_str = (
            re.sub(r"\s+ngày\s+", " ", datetime_match.group(0), flags=re.IGNORECASE)
            if datetime_match else "14:00 15/09/2026"
        )

        observation = None
        observation_prefix = "Observation gần nhất (JSON): "
        for line in reversed(prompt.splitlines()):
            if line.startswith(observation_prefix):
                try:
                    observation = json.loads(line[len(observation_prefix):])
                except json.JSONDecodeError:
                    observation = {"status": "INVALID_OBSERVATION"}
                break

        # Tiếp tục suy luận sau khi MCP Server trả về Observation.
        if observation:
            if observation.get("status") == "NOT_FOUND":
                return {
                    "type": "text",
                    "content": observation.get("message", "Không tìm thấy thông tin sinh viên yêu cầu."),
                    "thought": "Công cụ trả về NOT_FOUND nên tôi phản hồi chính xác và không bịa đặt dữ liệu."
                }

            if "data" in observation:
                data = observation["data"]
                if "đặt lịch" in prompt_lower:
                    return {
                        "type": "tool_call",
                        "tool_name": "schedule_appointment",
                        "arguments": {
                            "student_id": observation.get("student_id", student_id),
                            "datetime_str": datetime_str,
                            "advisor_name": data.get("advisor", "PGS.TS Nguyễn Văn A")
                        },
                        "thought": "Đã tra cứu được cố vấn; tiếp tục gọi schedule_appointment để hoàn tất yêu cầu."
                    }

                return {
                    "type": "text",
                    "content": (
                        f"Kết quả tra cứu cho sinh viên {observation.get('student_id', '')} "
                        f"({data.get('full_name', '')}): Lớp {data.get('class', '')}, "
                        f"GPA: {data.get('gpa', '')}, Email: {data.get('email', '')}, "
                        f"Trạng thái: {data.get('status', '')}, Cố vấn: {data.get('advisor', '')}."
                    ),
                    "thought": "Đã có đủ dữ liệu học vụ để tổng hợp câu trả lời cuối cùng."
                }

            if "message" in observation:
                return {
                    "type": "text",
                    "content": observation["message"],
                    "thought": "Hành động đã hoàn tất; tôi trả lại thông báo xác nhận từ công cụ."
                }

            return {
                "type": "text",
                "content": f"Phản hồi từ công cụ: {json.dumps(observation, ensure_ascii=False)}",
                "thought": "Tổng hợp phản hồi cuối cùng từ Observation."
            }

        # Nhận diện yêu cầu nhiều bước trước khi xử lý yêu cầu một Tool.
        is_multi_step = "đặt lịch" in prompt_lower and (
            "tra cứu" in prompt_lower or "cố vấn học tập" in prompt_lower
        )
        if is_multi_step and student_id:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": "Cần biết cố vấn phụ trách trước khi đặt lịch; tôi tra cứu hồ sơ sinh viên trước."
            }

        if student_id and "đặt lịch" in prompt_lower:
            advisor_name = "TS. Lê Thị B" if "TS. Lê Thị B" in prompt else "PGS.TS Nguyễn Văn A"
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {
                    "student_id": student_id,
                    "datetime_str": datetime_str,
                    "advisor_name": advisor_name
                },
                "thought": f"Người dùng yêu cầu đặt lịch cho {student_id}; tôi gọi schedule_appointment."
            }

        if student_id and "tra cứu" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Người dùng muốn tra cứu thông tin của {student_id}; tôi gọi academic_query."
            }

        return {
            "type": "text",
            "content": "[Mock Agent Response]: Xin chào! Quy chế học vụ VinUni yêu cầu sinh viên tích lũy tối thiểu 120 tín chỉ và duy trì GPA trên 2.0 để tốt nghiệp.",
            "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-3.6-flash"
        try:
            self.min_request_interval = float(
                os.getenv("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", "13")
            )
        except ValueError:
            self.min_request_interval = 13.0
        self._last_request_at = 0.0

    def _respect_rate_limit(self):
        """Giãn cách request để không vượt quota Gemini Free Tier theo phút."""
        elapsed = time.monotonic() - self._last_request_at
        wait_seconds = self.min_request_interval - elapsed
        if self._last_request_at and wait_seconds > 0:
            print(f"⏳ [Gemini Free Tier]: Chờ {wait_seconds:.1f}s trước request tiếp theo...")
            time.sleep(wait_seconds)
        self._last_request_at = time.monotonic()

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            self._respect_rate_limit()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
