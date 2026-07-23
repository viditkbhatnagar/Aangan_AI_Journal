"""Compare embedding models on Aangan-shaped retrieval, English AND Hindi.

    .venv/bin/python scripts/eval_embeddings.py

Not under tests/: this loads real model weights (hundreds of MB) and must
never run in CI. Each (query -> expected document) pair mimics how the
Companion retrieves family memory; queries deliberately paraphrase rather
than quote. Reports hit@1 / hit@3 per language per model.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

MODELS = [
    "all-MiniLM-L6-v2",
    "paraphrase-multilingual-MiniLM-L12-v2",
]

# Corpus: realistic journal facts/summaries (seed.py-style content).
CORPUS = {
    "en-gift": "Deepa mentioned she would love silver jhumka earrings for her birthday.",
    "en-health": "Mumma's knee pain was worse this morning; the stairs felt difficult.",
    "en-school": "Aditya's daughter scored the winning goal in the school football match.",
    "en-food": "Abhishek is trying to eat less sugar and skipped dessert all week.",
    "en-travel": "Deepa booked train tickets to Jaipur for the family wedding in December.",
    "hi-gift": "दीपा ने कहा कि उसे जन्मदिन पर चाँदी के झुमके बहुत पसंद आएँगे।",
    "hi-health": "आज सुबह मम्मा के घुटने का दर्द बढ़ गया था, सीढ़ियाँ चढ़ना मुश्किल हो रहा था।",
    "hi-school": "आदित्य की बेटी ने स्कूल के फुटबॉल मैच में जीत वाला गोल किया।",
    "hi-food": "अभिषेक चीनी कम खाने की कोशिश कर रहा है, पूरे हफ़्ते मीठा नहीं खाया।",
    "hi-travel": "दीपा ने दिसंबर की पारिवारिक शादी के लिए जयपुर की ट्रेन टिकट बुक कर लीं।",
}

# (language, query, expected corpus key) — paraphrases, incl. cross-lingual
# asks (a Hindi-first elder asking about an English entry and vice versa).
QUERIES = [
    ("en", "What would Deepa want as a birthday present?", "en-gift"),
    ("en", "How is Mumma's leg doing?", "en-health"),
    ("en", "Did anything good happen at school?", "en-school"),
    ("en", "Is Abhishek still avoiding sweets?", "en-food"),
    ("en", "Who arranged the travel for the wedding?", "en-travel"),
    ("hi", "दीपा को तोहफ़े में क्या अच्छा लगेगा?", "hi-gift"),
    ("hi", "मम्मा की तबीयत कैसी है, घुटना कैसा है?", "hi-health"),
    ("hi", "स्कूल में क्या खास हुआ?", "hi-school"),
    ("hi", "क्या अभिषेक अब भी मीठे से दूर है?", "hi-food"),
    ("hi", "शादी के सफ़र का इंतज़ाम किसने किया?", "hi-travel"),
    # cross-lingual: question in one language, memory recorded in the other
    ("xl", "दीपा के जन्मदिन के लिए कौन सा तोहफ़ा ठीक रहेगा?", "en-gift"),
    ("xl", "What did Mumma say about her knee?", "hi-health"),
]


def evaluate(model_name: str) -> dict:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    keys = list(CORPUS.keys())
    doc_vecs = np.array(model.encode([CORPUS[k] for k in keys], normalize_embeddings=True))

    results = {}
    for lang in ("en", "hi", "xl"):
        pairs = [(q, want) for (l, q, want) in QUERIES if l == lang]
        hit1 = hit3 = 0
        for query, want in pairs:
            q_vec = np.array(model.encode([query], normalize_embeddings=True))[0]
            ranked = np.argsort(-(doc_vecs @ q_vec))
            top = [keys[i] for i in ranked[:3]]
            hit1 += top[0] == want
            hit3 += want in top
        results[lang] = {"hit@1": hit1 / len(pairs), "hit@3": hit3 / len(pairs), "n": len(pairs)}
    return results


def main() -> None:
    print(f"{'model':<42} {'lang':<4} {'hit@1':>6} {'hit@3':>6}")
    print("-" * 62)
    for model_name in MODELS:
        results = evaluate(model_name)
        for lang, r in results.items():
            print(f"{model_name:<42} {lang:<4} {r['hit@1']:>6.0%} {r['hit@3']:>6.0%}")
    print(
        "\nxl = cross-lingual (ask in one language about a memory recorded in"
        " the other) — the case a Hindi-first family hits daily."
    )


if __name__ == "__main__":
    main()
