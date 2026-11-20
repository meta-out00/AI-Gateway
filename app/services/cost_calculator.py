class CostCalculator:
    """
    ตารางคำนวณค่าใช้จ่ายตามจำนวน Token (หน่วย: USD ต่อ 1,000,000 Tokens)
    Format: "model_prefix": (input_price_per_1m, output_price_per_1m)
    """

    PRICING_TABLE: dict[str, tuple[float, float]] = {
        # Google Gemini
        "gemini-flash-lite": (0.075, 0.30),
        "gemini-3.1-flash-lite": (0.075, 0.30),
        "gemini-3.8-flash": (0.15, 0.60),
        "gemini-2.5-flash": (0.15, 0.60),
        "gemini-2.5-pro": (1.25, 10.00),
        # OpenAI
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        # Mock AI (ตั้งราคาจำลองไว้สำหรับทดสอบ Budget Limit โดยไม่เสียเงินจริง)
        "mock-": (1000.0, 2000.0),
    }

    DEFAULT_PRICE: tuple[float, float] = (0.50, 1.50)

    @classmethod
    def get_model_pricing(cls, model_name: str) -> tuple[float, float]:
        normalized = model_name.lower().strip()
        for prefix, prices in cls.PRICING_TABLE.items():
            if normalized.startswith(prefix):
                return prices
        return cls.DEFAULT_PRICE

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        input_price, output_price = cls.get_model_pricing(model_name)
        input_cost = (prompt_tokens / 1_000_000) * input_price
        output_cost = (completion_tokens / 1_000_000) * output_price
        return round(input_cost + output_cost, 8)