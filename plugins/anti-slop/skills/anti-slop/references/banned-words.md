# Banned Words, Phrases, Openers, and Japanese Tells

Flagged across empirical studies (Carnegie Mellon 2025, Wikipedia Signs of AI Writing, Buffer 52M post analysis) and real code/ticket review logs. Never use any of these. Replace with concrete alternatives or restructure.

---

## 1. Banned English Vocabulary

### High-Telltale Nouns & Adjectives
delve / delves / delving, tapestry, landscape (figurative), testament (e.g. "a testament to"), vibrant, pivotal, crucial, intricate / intricacies, meticulous / meticulously, bolster / bolstered, garner / garnered, underscore / underscores, interplay, multifaceted, nuanced (as filler), foster / fostering, paramount, groundbreaking, cutting-edge, game-changing / game-changer, transformative, revolutionise / revolutionize, seamless / seamlessly, robust (outside hard engineering), comprehensive (describing own work), endeavour / endeavor, aforementioned, harnessing, spearheading, navigating (figurative), showcasing, highlighting, emphasizing, enhancing, unprecedented, remarkable, stunning, profound, epic (non-literal), foundational, holistic, synergistic.

### 2025/2026 Era Additions (Claude 3.5/3.7, GPT-4o/5, Gemini 2.0)
- **align with** (use "match" or "follow")
- **streamline / streamlining** (use "simplify", "cut", or "combine")
- **foster / fostering** (use "build" or "help")
- **holistic** (use "complete" or "whole")
- **spearhead / spearheading** (use "lead" or "start")
- **key takeaway / takeaways** (use "summary" or "points")
- **in terms of** (filler: cut or rephrase)
- **at the heart of** (use "in" or "within")
- **foundational** (use "basic" or "core")
- **seamless integration** (corporate fluff)

---

## 2. Banned English Phrases & Formulaic Structures

- "In today's [adjective] [noun]..." / "In today's fast-paced world..." / "In today's digital age..."
- "It's worth noting that..." / "It's important to note that..."
- "Let's dive in" / "Let's dive deeper" / "Let's delve into"
- "At its core..." / "At the end of the day..." / "In the realm of..." / "When it comes to..."
- "A testament to..."
- "Not just X, but Y" / "It's not just about X — it's about Y"
- "This is where X comes in"
- "Whether you're a [X] or a [Y]..."
- "From X to Y" (sweeping range opener)
- "The bottom line is..." / "Here's the thing..." / "Here's the deal..." / "In a nutshell..."
- "Without further ado..." / "Buckle up"
- "Take it to the next level" / "Unlock the power of..." / "Supercharge your..." / "Elevate your..."
- "Bridge the gap" / "Move the needle"
- "In conclusion" / "Overall," (mechanical paragraph starters)
- "Firstly... Secondly... Thirdly..." (mechanical tripling)
- "I hope this email/message finds you well" / "I hope this helps"
- "Please don't hesitate to reach out" / "Feel free to reach out with questions" / "Let me know if you'd like me to..." / "Happy to dig deeper if useful"
- "This means that..." / "In other words," (hand-holding restatements)
- "I understand your concern/frustration" (generic chatbot empathy)

### Second-Order "Clever Slop" (Writerly tells to avoid)
- Personified artifacts: "the table went", "the architecture wanted"
- Transaction metaphors: "buys a second code path"
- Posture verbs: "sits close enough" (instead of "is")
- Smug compression: "which only bites when you scan"

---

## 3. Banned English Openers

- "Certainly," / "Absolutely," / "Sure,"
- "Great question!" / "That's a great point!"
- "I'd be happy to..." / "As an AI..." / "As a language model..."
- "However, it's important to..."
- "Moreover," / "Furthermore," / "Additionally,"
- "Interestingly," / "Notably," / "Importantly," / "Indeed,"

---

## 4. Japanese AI Slop Lexicon (日本語AIスロップ・典型パターン)

Flagged specifically in TFS / Redmine / SkyPAS_AT developer communications:

### 挨拶・クッション言葉 (Empty Corporate Padding — Cut completely)
- 「ご確認のほどよろしくお願いいたします」
- 「ご査収のほどよろしくお願いいたします」
- 「恐れ入りますが、〜」
- 「幸甚に存じます」
- 「何卒よろしくお願い申し上げます」
- 「お疲れ様です。標題の件につきまして、〜」
*Fix:* State the fact or question immediately. No polite throat-clearing.

### 接続詞の機械的連鎖 (Formulaic AI Conjunction Chains)
- 「また、」「さらに、」「加えて、」「一方で、」「なお、」「総じて、」
*Fix:* Do not link every sentence with transition words. Let periods end thoughts cleanly.

### 曖昧・官僚的AI動詞 (Vague/Bureaucratic Verbs)
- 「推進する」「寄与する」「図る」
- 「実施してまいります」「注力してまいります」「検討を重ねて」
- 「言わずもがな」「〜に他なりません」
*Fix:* Use concrete actions: 「〜を作成した」「〜を修正した」「〜を削除した」.

### AI特有の結び・推量 (Speculative Conclusion Tails)
- 「〜と言えるでしょう」
- 「〜が期待されます」
- 「〜重要なポイントです」
- 「〜と考えられます」
*Fix:* State the verified result: 「〜を確認した」「〜で動作した」.

### 文体混在と体言止めの連続 (Register Mixing & Staccato Nouns)
- Do NOT mix 敬体 (です・ます), 常体 (だ・である), and 体言止め in one ticket or document.
- Do NOT chain 5+ verbless nouns in a row (e.g. 「エラーなし。ログ記録なし。再現不可。」).
*Fix:* Consistent 常体 past tense: 「エラーは出ていない。ログにも記録されなかった。20回試行したが再現しなかった。」.

---

## 5. Channel-Specific Rules

### PR Descriptions & Git Commits
- **No consequence-selling tails:** `, ensuring X` / `, so you can't lock yourself out` / `, which means Y`. State the condition and outcome; drop the sales pitch.
- **No totalizing claims:** `all of it`, `fully covered`, `every change on the branch`.
- **No housekeeping announcements:** `Description rewritten for clarity` / `Updated the description` / `Cleaned this up`.
- **No AI attribution trailers:** `Co-Authored-By: Claude`, `Generated with Claude Code`, `Assisted-by:`.
- **Commit body:** Plain language describing behavior, no laundry list of changed line numbers.

### Ticket / Issue Responses (Redmine, TFS)
- **No standalone section label:** `Repro` or `Repro:`. Use `Steps:` or numbered steps directly.
- **Review thread replies:** Exactly one sentence giving the reason. No bullet points, no apology, no thank you.

### Code Comments
- **No spec/ticket references:** No `仕様書`, `SDF_`, ticket `#` in comments (keep in git commit message).
- **No code narration:** No `// loop through items` above `foreach`. Only explain non-obvious *why*.