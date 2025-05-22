# prompt_registry.py
# 注册所有可用的 Prompt 模板，包括版本控制、输出格式、评分机制等

PROMPT_REGISTRY = {
    # === 📌 Risk Fast-Screen ===
    # ✅ Purpose: Quickly identify risks in a 10-K paragraph that could affect stock prices.
    # 🧠 Output Fields:
    #     - risk_type: Type of risk (e.g., Financial, Legal, Market).
    #     - severity: Severity score (1–5, 1 = small issue, 5 = huge problem).
    #     - explanation: 1–2 sentences explaining the risk and its impact.
    #     - investor_tip: Actionable advice for investors (e.g., "Monitor closely").
    # 🧪 Few-Shot Examples: 3 examples to guide consistent outputs.
    "risk_fast_screen_prompt": {
        "template": """You are a friendly financial advisor helping new stock investors. Read the 10-K paragraph and identify risks that could hurt the stock price.

    1. Risk Type: Choose one: ["Financial (e.g., too much debt)", "Legal (e.g., lawsuits)", "Market (e.g., tough competition)", "Operational (e.g., supply chain issues)", "Reputation (e.g., bad press)", "None"]
    2. Severity: Score 1–5 (1 = small issue, 5 = huge problem, like bankruptcy risk).
    3. Explanation: In 1–2 simple sentences, explain the risk and why it might lower the stock price.
    4. Investor Tip: Should investors worry? (e.g., "Watch closely" or "Not a big deal").

    ---

    📘 Example 1 (High Severity, Legal Risk):
    Paragraph: The company is facing a $200 million lawsuit for product defects, which could lead to significant financial penalties.
    Answer:
    {{
      "risk_type": "Legal",
      "severity": 5,
      "explanation": "A $200 million lawsuit could drain the company’s cash, making the stock less valuable.",
      "investor_tip": "Monitor closely; wait for lawsuit updates before buying."
    }}

    ---

    📘 Example 2 (Medium Severity, Financial Risk):
    Paragraph: Our debt increased by $100 million this year, but revenue grew by 5%.
    Answer:
    {{
      "risk_type": "Financial",
      "severity": 3,
      "explanation": "More debt could make it harder to pay bills if revenue slows, which might worry investors.",
      "investor_tip": "Check if debt grows in the next report."
    }}

    ---

    📘 Example 3 (Low Severity, Operational Risk):
    Paragraph: We upgraded our warehouse systems to improve delivery times, with minor delays during the transition.
    Answer:
    {{
      "risk_type": "Operational",
      "severity": 1,
      "explanation": "Minor delays from a system upgrade are normal and unlikely to hurt the stock much.",
      "investor_tip": "Not a big deal; focus on sales instead."
    }}

    ---

    Now analyze the following paragraph:

    Paragraph: {paragraph}

    Return ONLY a valid JSON object. Do not include triple backticks or markdown formatting.""",
        "version": "v1.0",
        "expected_output_schema": {
            "risk_type": "string",
            "severity": "integer",
            "explanation": "string",
            "investor_tip": "string"
        },
        "display_type": "paragraph_table",
  "self_eval_instruction": "Rate your confidence (1–5) using the following criteria:\n\
5 = Strong keyword/context match, unambiguous and specific\n\
4 = Strong match with minor ambiguity\n\
3 = Moderate match or uncertain scope\n\
2 = Weak match, vague expression\n\
1 = Highly speculative\n\
Include both the numeric score and the reasoning (as 'confidence.basis') in the final JSON output."
    },
    # === 📌 Risk Summary ===
    # ✅ 用途：Risk Summary，用于结构化分析 10-K 段落中的风险类型和严重程度
    # 🧠 输出字段说明：
    #     - risk_type: 风险类型，如 Market / Operational / Regulatory 等
    #     - severity: 严重等级（1–5）
    #     - excerpt: 风险相关片段
    #     - confidence: GPT 自评可信度（1–5）
    # 🧪 自评分提示：Please include a confidence score (1–5) in the final JSON output.
        "risk_summary_prompt": {
        "template": """You are a senior financial risk analyst. Analyze the following 10-K risk disclosure section.

Summarize the key risk themes and material exposures using natural language. Focus on:
- Most significant risks based on severity and likelihood.
- Areas with weak mitigation or high uncertainty.
- Emerging or trending risk themes (e.g., ESG, geopolitical, cybersecurity).

✏️ Output instructions:
Return only a **narrative summary** in fluent English. Do NOT include any tables, bullet points, or JSON.

Text:
{text}
""",
  "version": "v4.0",
  "expected_output_schema": {
    "summary_narrative": "string"
  },
   "display_type": "summary_narrative",
   "self_eval_instruction": "Rate your confidence (1–5) using the following criteria:\n\
5 = Strong keyword/context match, unambiguous and specific\n\
4 = Strong match with minor ambiguity\n\
3 = Moderate match or uncertain scope\n\
2 = Weak match, vague expression\n\
1 = Highly speculative\n\
Include both the numeric score and the reasoning (as 'confidence.basis') in the final JSON output."
    },
    # === 📌 Financial Health ===
    # ✅ 用途：Financial Health，用于结构化分析 10-K 段落中的风险类型和严重程度
    # 🧠 输出字段说明：
    #     - risk_type: 风险类型，如 Market / Operational / Regulatory 等
    #     - severity: 严重等级（1–5）
    #     - excerpt: 风险相关片段
    #     - confidence: GPT 自评可信度（1–5）
    # 🧪 自评分提示：Please include a confidence score (1–5) in the final JSON output.
        # In prompt_registry.py
    "financial_health_prompt": {
        "template": """
You are a financial analyst tasked with evaluating a company's financial health based on its 10-K report. Analyze the full text provided below and generate a detailed analysis for each of the following metrics. For each metric, write a concise paragraph (50-100 words) summarizing the relevant information from the entire document. Focus on extracting and interpreting all relevant data, even if it's spread across multiple sections.

Full Text:
{text}

Provide your analysis in the following JSON format:
{{
  "liquidity_analysis": "A detailed paragraph summarizing the company's liquidity, including cash reserves, cash flow, and working capital trends.",
  "debt_vulnerability": "A detailed paragraph summarizing the company's debt levels, maturity schedules, covenant compliance, and interest coverage.",
  "earnings_quality": "A detailed paragraph summarizing the company's revenue trends, profit margins, and earnings sustainability.",
  "bankruptcy_risk": "A detailed paragraph assessing the company's bankruptcy risk, referencing metrics like Altman Z-Score or debt-to-equity ratio.",
  "audit_redflags": "A detailed paragraph identifying any audit concerns, such as non-GAAP adjustments or restatements.",
  "confidence": "score": 1-5,
}}

pulling data from all relevant parts of the document. Respond ONLY with the JSON object.
""",
        "version": "1.0",
        "display_type": "raw_text",
        "input_variables": ["text"],
        "expected_output_schema": {
            "liquidity_analysis": {"type": "string"},
            "debt_vulnerability": {"type": "string"},
            "earnings_quality": {"type": "string"},
            "bankruptcy_risk": {"type": "string"},
            "audit_redflags": {"type": "string"},
            "confidence": {"type": "object"}
        }
    },

# === 📌 Investment Decision Assistant ===
    # ✅ 用途：Analyzes a 10-K paragraph to guide investment decisions (buy, hold, sell).
    # 🧠 输出字段说明：
    #     - signal: Positive (good news), Negative (bad news), or Neutral (no clear impact).
    #     - impact: How the paragraph affects the stock price (1–2 sentences).
    #     - investment_advice: Buy, hold, sell, or monitor, with a brief reason.
    #     - confidence: Self-evaluated reliability score (1–5).
    # 🧪 自评分提示：Include a confidence score (1–5) in the JSON output.
    "investment_decision_prompt": {
        "template": """You are a friendly financial advisor helping new stock investors. Review the 10-K paragraph and provide investment advice based on its impact on the stock price.

1. Signal: Choose one:
   ["Positive (e.g., strong sales, new products)", "Negative (e.g., high debt, lawsuits)", "Neutral (e.g., routine updates, no clear impact)"]
2. Impact: In 1–2 simple sentences, explain how the paragraph affects the stock price.
3. Investment Advice: Recommend one: ["Buy", "Hold", "Sell", "Monitor"] and give a brief reason.
4. Confidence: Score 1–5 (1 = very uncertain, 5 = very certain) based on the clarity of the paragraph.

---

📘 Example 1 (Positive Signal):
Paragraph: "Revenue increased by 20% to $1.5 billion due to strong demand for our new electric vehicle line."
Answer:
{{
  "signal": "Positive",
  "impact": "Strong sales growth suggests higher profits, which could boost the stock price.",
  "investment_advice": "Buy: Growing revenue shows the company is doing well.",
  "confidence": 5
}}

---

📘 Example 2 (Negative Signal):
Paragraph: "The company is facing a $100 million lawsuit for product safety violations, which may lead to significant fines."
Answer:
{{
  "signal": "Negative",
  "impact": "The lawsuit could cost millions, hurting profits and lowering the stock price.",
  "investment_advice": "Sell: The lawsuit poses a serious financial risk.",
  "confidence": 4
}}

---

📘 Example 3 (Neutral Signal):
Paragraph: "The company completed its annual audit with no significant changes to prior financial statements."
Answer:
{{
  "signal": "Neutral",
  "impact": "The audit completion is routine and does not directly affect the stock price.",
  "investment_advice": "Hold: No major news to act on.",
  "confidence": 3
}}

---

Now analyze the following paragraph:

Paragraph: {paragraph}

Return ONLY a valid JSON object following the example format above. Do not include markdown or explanations.""",
        "version": "v1.0",
        "expected_output_schema": {
            "signal": "string",
            "impact": "string",
            "investment_advice": "string",
            "confidence": "integer"
        },
        "display_type": "paragraph_table",
        "self_eval_instruction": "Rate your confidence (1–5) using the following criteria:\n\
5 = Clear and specific information (e.g., exact financial figures or events).\n\
4 = Clear but slightly vague (e.g., trends without numbers).\n\
3 = Neutral or routine information with no strong impact.\n\
2 = Vague or ambiguous language.\n\
1 = Highly uncertain or speculative."
    },
# === 📌 Investment Highlights Summary ===
    # ✅ Purpose: Identifies positive financial or strategic highlights in a 10-K paragraph that could boost stock value.
    # 🧠 Output Fields:
    #     - highlight_type: Type of positive signal, e.g., Revenue Growth, New Products.
    #     - impact: Positive impact on stock value (1–5 scale).
    #     - explanation: Brief explanation of why this is good for investors.
    #     - investor_tip: Actionable advice for investors.
    # 🧪 Self-Evaluation: Include a confidence score (1–5) in the JSON output.
    "investment_highlights_prompt": {
        "template": """You are a financial advisor helping beginner stock investors. Review the 10-K paragraph and identify positive highlights that could make the stock a good investment.

1. Highlight Type — choose from:
["Revenue Growth", "Profit Increase", "Cash Reserves", "New Products/Services", "Market Expansion", "Cost Reduction", "Strong Management", "None"]

2. Impact — rate the positive effect on stock value using these guidelines:
Apply 1–5 scoring based on language and context:
    5 = Major positive impact (e.g., "record-breaking revenue", "game-changing product launch")
    4 = Significant positive signal (e.g., strong profit growth, large cash reserves)
    3 = Moderate positive mention (e.g., steady sales growth, new market entry)
    2 = Minor positive note (e.g., cost savings, routine improvements)
    1 = Generic or low-impact positive (e.g., vague optimism, standard operations)

3. Explanation — in 1–2 simple sentences, explain why this highlight is good for the stock.
4. Investor Tip — give a short tip for investors (e.g., "Consider buying" or "Watch for more growth").
5. Confidence — a numeric score (1–5) based on clarity of the positive signal.

---

📘 Example 1 (High impact, Revenue Growth):
Paragraph:
The company reported record-breaking revenue of $2 billion in 2024, a 20% increase from the prior year, driven by strong demand for our new electric vehicles.

Answer:
{{
  "highlight_type": "Revenue Growth",
  "impact": "5",
  "explanation": "A 20% revenue increase shows strong customer demand, which could boost the stock price.",
  "investor_tip": "Consider buying if growth continues.",
  "confidence": "5"
}}

---

📘 Example 2 (Medium impact, New Products/Services):
Paragraph:
In Q3, we launched a new cloud computing service that has already secured contracts with three major clients.

Answer:
{{
  "highlight_type": "New Products/Services",
  "impact": "3",
  "explanation": "The new cloud service could increase future revenue, making the stock more attractive.",
  "investor_tip": "Watch for more client contracts next quarter.",
  "confidence": "4"
}}

---

📘 Example 3 (Low impact, Cost Reduction):
Paragraph:
The company implemented a new supply chain system to reduce logistics costs by 5% this year.

Answer:
{{
  "highlight_type": "Cost Reduction",
  "impact": "2",
  "explanation": "Lower costs could improve profits slightly, supporting the stock’s stability.",
  "investor_tip": "Not a big driver, but a positive sign.",
  "confidence": "3"
}}

---

Now analyze the following paragraph:

Paragraph:
{paragraph}

Return ONLY a valid JSON object following the example format above. Do not include markdown or any explanation.""",
        "version": "v1.0",
        "expected_output_schema": {
            "highlight_type": "string",
            "impact": "string",
            "explanation": "string",
            "investor_tip": "string",
            "confidence": "integer"
        },
        "display_type": "paragraph_table",
        "self_eval_instruction": "Rate your confidence (1–5) using the following criteria:\n\
5 = Strong keyword/context match, unambiguous and specific\n\
4 = Strong match with minor ambiguity\n\
3 = Moderate match or uncertain scope\n\
2 = Weak match, vague expression\n\
1 = Highly speculative\n\
Include only the numeric score in the JSON output."
    }
}
