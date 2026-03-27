import streamlit as st
import torch
import tempfile
import os
import numpy as np
from threading import Thread

# LLM
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer

# Embedding + Reranker
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder

# Document processing
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# BM25 (recherche par mots-clés)
from rank_bm25 import BM25Okapi

# ==========================================
# ⚡ CONFIG CPU — HuggingFace Spaces gratuit
# ==========================================
# ⚡ CONFIG CPU — à appeler avant tout travail parallèle
try:
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass  # Déjà initialisé par Streamlit au démarrage, on ignore


    
# Mise en page 

st.set_page_config(page_title="RAG Hybride + Reranker", page_icon="🔍", layout="wide")
st.title("🔍 RAG Hybride + Reranker")

# Texte sidebar 

with st.sidebar.expander("⚙️ Comment fonctionne ce système ?", expanded=False):
    st.markdown("""
**Étape 1 — Double recherche (Hybride)**

Quand tu poses une question, deux moteurs de recherche travaillent en parallèle sur tes chunks :

- **BM25** : moteur de mots-clés classique (comme Google années 90). Très fort sur les noms propres, dates, termes exacts. Ultra rapide, zéro modèle IA.
- **FAISS** : recherche vectorielle sémantique. Comprend le sens même si les mots sont différents.

Les deux retournent chacun leurs **top 5 chunks** → on fusionne → **10 chunks candidats**.

---

**Étape 2 — Reranking (Cross-Encoder)**

Un petit modèle (~70M params) lit chaque paire *(question, chunk)* ensemble et lui donne un score de pertinence réel.

Contrairement à l'embedding qui encode question et chunk **séparément**, le cross-encoder les lit **ensemble** → il comprend vraiment la relation entre les deux.

Résultat : on garde les **2 meilleurs chunks** sur les 10.

---

**Étape 3 — Génération**

Le LLM reçoit uniquement ces 2 chunks ultra-pertinents et génère la réponse. Un seul appel LLM, contexte propre = réponse précise et rapide.
    """)

# Chargement une seule fois des modèles ( Embedding + Reranker + LLM + quantization )
@st.cache_resource(show_spinner="Chargement des modèles... (première fois ~2 min)")
def load_models():

    # ⚡ Embedding : MiniLM 120M — rapide et suffisant
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True, 'batch_size': 16}
    )

    # ⚡ Reranker : cross-encoder léger, ~70M params
    # Lit (question + chunk) ensemble → score de pertinence réel
    # Beaucoup plus précis qu'une simple similarité cosine
    reranker = CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_length=512,
        device="cpu"
    )

    # LLM : Qwen 1.5B Instruct
    model_id = "Qwen/Qwen2.5-0.5B-Instruct"  # au lieu de 1.5B
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    

    llm = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,  # ← au lieu de float32
        low_cpu_mem_usage=True
    )
    
    # je sais pas a quoi ca sert 
    # ⚡ Warm-up : JIT-compile les kernels, évite le lag sur la 1ère requête
    dummy = tokenizer("warmup", return_tensors="pt")
    with torch.inference_mode():
        llm.generate(**dummy, max_new_tokens=1, pad_token_id=tokenizer.eos_token_id)

    return embeddings, reranker, tokenizer, llm

embeddings, reranker, tokenizer, llm = load_models()

# Tokens d'arrêt Qwen
EOS_IDS = [tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids("<|im_end|>")]
MAX_TOKENS_ANSWER = 150

# ==========================================
# SESSION STATE   je sais pas ce que ca fait 
# ==========================================
for key, default in [
    ("vector_db", None),
    ("bm25", None),
    ("chunks_text", None),
    ("current_file_name", None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Partie Upload du PDF 
uploaded_file = st.sidebar.file_uploader("📂 Déposez votre PDF", type=["pdf"])

if uploaded_file is None:
    for key in ["vector_db", "bm25", "chunks_text", "current_file_name"]:
        st.session_state[key] = None


# ca fait le chunking ?? 
elif uploaded_file is not None:
    if st.session_state.current_file_name != uploaded_file.name:
        for key in ["vector_db", "bm25", "chunks_text"]:
            st.session_state[key] = None
        st.session_state.current_file_name = uploaded_file.name

    if st.session_state.vector_db is None:
        with st.spinner("Indexation du document... ⏳"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                temp_path = tmp.name

            loader = PyPDFLoader(temp_path)
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=200,           # ⚡ overlap réduit = moins de tokens dupliqués
                separators=["\n\n", "\n", ".", "!", "?", " "]
            ).split_documents(loader.load())
            os.remove(temp_path)

            # --- Index FAISS (recherche sémantique) ---
            st.session_state.vector_db = FAISS.from_documents(chunks, embeddings)

            # --- Index BM25 (recherche mots-clés) ---
            # BM25 travaille sur des tokens simples (split sur espaces)
            texts = [c.page_content for c in chunks]
            tokenized = [t.lower().split() for t in texts]
            st.session_state.bm25        = BM25Okapi(tokenized)
            st.session_state.chunks_text = texts   # texte brut pour BM25

            st.sidebar.success(f"✅ '{uploaded_file.name}' indexé ({len(chunks)} chunks)")




# Fonctions

def hybrid_search(question: str, k: int = 10) -> list[str]:
    """
    Recherche hybride : BM25 + FAISS → fusion des résultats.

    Pourquoi k=5 chacun ?
    On récupère volontairement large (10 candidats au total)
    car le reranker va ensuite trier et garder les vrais meilleurs.
    BM25 attrape ce que FAISS rate (termes exacts) et vice versa.
    """
    question_lower = question.lower()

    # -- BM25 : score par fréquence de termes --
    bm25_scores = st.session_state.bm25.get_scores(question_lower.split())
    top_bm25_idx = np.argsort(bm25_scores)[::-1][:k]
    bm25_results = [st.session_state.chunks_text[i] for i in top_bm25_idx]

    # -- FAISS : score par similarité sémantique --
    faiss_docs   = st.session_state.vector_db.similarity_search(question, k=k)
    faiss_results = [d.page_content for d in faiss_docs]

    # -- Fusion avec dédoublonnage --
    seen  = set()
    merged = []
    for text in bm25_results + faiss_results:
        if text not in seen:
            seen.add(text)
            merged.append(text)

    return merged  # jusqu'à 10 chunks uniques


def rerank(question: str, candidates: list[str], top_n: int = 2):
    pairs  = [(question, chunk) for chunk in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(scores, candidates), reverse=True)
    best_score = ranked[0][0]
    best_chunks = [chunk for _, chunk in ranked[:top_n]]
    return best_chunks, float(best_score)


def build_prompt(system: str, user: str) -> str:
    return (
        f"<|im_start|>system\n{system}\n<|im_end|>\n"
        f"<|im_start|>user\n{user}\n<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def stream_llm(prompt: str, placeholder) -> str:
    """Génération streamée avec curseur animé."""
    inputs   = tokenizer(prompt, return_tensors="pt")
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True
    )

    def _generate():
        with torch.inference_mode():
            llm.generate(
                **inputs,
                streamer=streamer,
                max_new_tokens=MAX_TOKENS_ANSWER,
                do_sample=False,
                repetition_penalty=1.3,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=EOS_IDS
            )

    Thread(target=_generate).start()

    full_text = ""
    for token in streamer:
        full_text += token
        placeholder.markdown(full_text + "▌")
    placeholder.markdown(full_text)
    return full_text

def clean_chunk(text: str) -> str:
    """Signale les chunks tronqués plutôt que de les envoyer bruts."""
    text = text.strip()
    # Si le chunk commence par une minuscule → phrase tronquée
    if text and text[0].islower():
        text = "(...) " + text
    return text

# ==========================================
# INTERFACE PRINCIPALE
# ==========================================
if st.session_state.vector_db is not None:

    question = st.text_input(
        "Posez votre question :",
        placeholder="Poser une question"
    )

    if st.button("Lancer l'Analyse", type="primary") and question:
        st.markdown("---")

        # --- ÉTAPE 1 : RECHERCHE HYBRIDE ---
        with st.spinner("🔎 Recherche hybride (BM25 + vectorielle)..."):
            candidates = hybrid_search(question, k=5)

        # Affichage debug optionnel
        with st.expander(f"📚 {len(candidates)} chunks candidats récupérés (avant reranking)"):
            for i, c in enumerate(candidates):
                st.caption(f"**Chunk {i+1}** : {c[:150]}...")

        # --- ÉTAPE 2 : RERANKING ---
        with st.spinner("⚖️ Reranking (sélection des 2 meilleurs chunks)..."):
            best_chunks, confidence = rerank(question, candidates, top_n=2)

        st.caption(f"Score de pertinence : `{confidence:.2f}`")
        
        if confidence < -2.0:  # score très négatif = rien de pertinent
            st.warning("❌ Aucun passage pertinent trouvé pour cette question.")
            st.stop()

        with st.expander("✅ 2 chunks retenus après reranking"):
            for i, c in enumerate(best_chunks):
                st.info(f"**Chunk {i+1}** : {c}")

        # --- ÉTAPE 3 : GÉNÉRATION LLM ---
        context = "\n\n".join([clean_chunk(c) for c in best_chunks])
        prompt  = build_prompt(
            system=(
                "Tu es un extracteur de faits. "
                "RÈGLE ABSOLUE : ta réponse doit être une phrase courte et factuelle. "
                "RÈGLE ABSOLUE : utilise UNIQUEMENT les chiffres et faits présents dans le contexte. "
                "RÈGLE ABSOLUE : ne génère jamais d'URLs, d'emails, de menus ou de listes de langues. "
                "Si le contexte contient '(...)' c'est une phrase incomplète, reconstitue le sens. "
                "Si tu ne trouves pas la réponse : 'Information introuvable.'"
            ),
            user=f"CONTEXTE :\n{context}\n\nQUESTION : {question}"
        )
        

        st.markdown("### 🎯 Réponse :")
        placeholder = st.empty()
        stream_llm(prompt, placeholder)

else:
    st.info("⬅️ Déposez un fichier PDF dans la barre latérale pour commencer.")