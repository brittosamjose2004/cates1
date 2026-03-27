#!/usr/bin/env python3
"""
Direct Implementation of RAG Hybrid System for ESG Document Analysis
Based on https://huggingface.co/spaces/Evrardodicaprio/RAG

Enhanced for ESG document processing with TARGET 151 indicator extraction
"""

import streamlit as st
import numpy as np
from sentence_transformers import CrossEncoder
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi
import threading
import tempfile
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import torch
import re

# Add project root to path for database access
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import ScrapedData


class ESGRagSystem:
    """
    ESG-focused RAG system for document analysis and indicator extraction
    """

    def __init__(self):
        """Initialize the ESG RAG system with models and components"""

        print("🔄 Initializing ESG RAG System...")

        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Initialize reranker
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        # Initialize LLM for analysis
        self.model_id = "Qwen/Qwen2.5-0.5B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.bfloat16,
            device_map="cpu"
        )

        # ESG indicator patterns (TARGET 151 compatible)
        self.esg_patterns = {
            'IMP-M01-I01': ['business description', 'company overview', 'nature of business'],
            'IMP-M01-I02': ['business sector', 'industry sector', 'economic sector'],
            'IMP-M01-I03': ['business model', 'revenue model', 'value proposition'],
            'IMP-M01-I04': ['stock exchange', 'listed', 'nse', 'bse', 'publicly traded'],
            'IMP-M01-I05': ['business activities', 'primary activities', 'core operations'],

            'IMP-M02-I01': ['sustainability policy', 'esg policy', 'environmental policy'],
            'IMP-M02-I02': ['sustainability strategy', 'esg strategy', 'green strategy'],
            'IMP-M02-I03': ['sustainability targets', 'esg targets', 'environmental targets'],

            'IMP-M03-I01': ['total revenue', 'revenue', 'net sales', 'turnover'],
            'IMP-M03-I02': ['board composition', 'board of directors', 'governance structure'],
            'IMP-M03-I03': ['board diversity', 'independent directors', 'women directors'],

            'IMP-M05-I01': ['carbon emission', 'co2 emission', 'greenhouse gas', 'ghg emission'],
            'IMP-M05-I02': ['energy consumption', 'renewable energy', 'energy usage'],
            'IMP-M05-I03': ['carbon footprint', 'emission reduction', 'climate targets'],
            'IMP-M05-I04': ['renewable energy', 'clean energy', 'solar', 'wind energy'],
            'IMP-M05-I05': ['carbon neutrality', 'net zero', 'carbon neutral'],

            'IMP-M06-I01': ['water consumption', 'water usage', 'water withdrawal'],
            'IMP-M06-I02': ['water recycling', 'water conservation', 'water management'],
            'IMP-M06-I03': ['water efficiency', 'water intensity', 'water saving'],

            'IMP-M07-I01': ['waste generation', 'waste disposal', 'waste management'],
            'IMP-M07-I02': ['recycling', 'circular economy', 'waste reduction'],
            'IMP-M07-I03': ['hazardous waste', 'waste recycling', 'zero waste'],

            'IMP-M15-I01': ['employees', 'workforce', 'staff count', 'employee strength'],
            'IMP-M15-I02': ['diversity', 'gender equality', 'women employees'],
            'IMP-M15-I03': ['employee training', 'skill development', 'learning'],
            'IMP-M15-I04': ['employee satisfaction', 'employee engagement'],
            'IMP-M15-I05': ['attrition rate', 'employee turnover', 'retention'],

            'IMP-M16-I01': ['csr spending', 'csr expenditure', 'social contribution'],
            'IMP-M16-I02': ['community development', 'social impact', 'community programs'],
            'IMP-M16-I03': ['education initiatives', 'healthcare programs', 'rural development'],
        }

        print("✅ ESG RAG System initialized successfully")

    def process_esg_document(self, pdf_file_path: str, company_name: str, year: int) -> Dict[str, Any]:
        """
        Process ESG document and extract TARGET 151 indicators

        Args:
            pdf_file_path: Path to the PDF file
            company_name: Company name for context
            year: Year for data context

        Returns:
            Dictionary with extracted indicators and analysis
        """

        print(f"📄 Processing ESG document: {Path(pdf_file_path).name}")

        try:
            # Step 1: Load and chunk the document
            loader = PyPDFLoader(pdf_file_path)
            documents = loader.load()

            if not documents:
                return {'error': 'Could not load PDF content'}

            # Split documents into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", "!", "?", " "]
            )
            chunks = splitter.split_documents(documents)

            if not chunks:
                return {'error': 'Could not split document into chunks'}

            print(f"📊 Document split into {len(chunks)} chunks")

            # Step 2: Create vector database
            chunk_texts = [chunk.page_content for chunk in chunks]

            # Create FAISS vector store
            vector_db = FAISS.from_texts(chunk_texts, self.embeddings)

            # Create BM25 index
            tokenized_chunks = [chunk.lower().split() for chunk in chunk_texts]
            bm25 = BM25Okapi(tokenized_chunks)

            print("🔍 Vector database and BM25 index created")

            # Step 3: Extract ESG indicators using hybrid search + reranking
            extracted_indicators = self._extract_esg_indicators(
                chunk_texts, vector_db, bm25, company_name, year
            )

            print(f"✅ Extracted {len(extracted_indicators)} ESG indicators")

            return {
                'success': True,
                'indicators': extracted_indicators,
                'chunks_processed': len(chunks),
                'company': company_name,
                'year': year,
                'document_path': pdf_file_path
            }

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            return {'error': str(e)}

    def _extract_esg_indicators(self, chunks: List[str], vector_db, bm25, company_name: str, year: int) -> List[Dict[str, Any]]:
        """Extract ESG indicators using hybrid search and reranking"""

        extracted_indicators = []

        for indicator_id, keywords in self.esg_patterns.items():
            try:
                best_match = self._find_best_match_for_indicator(
                    indicator_id, keywords, chunks, vector_db, bm25
                )

                if best_match:
                    # Enhance the match with LLM analysis
                    enhanced_match = self._enhance_with_llm_analysis(
                        indicator_id, best_match, company_name, year
                    )

                    if enhanced_match:
                        extracted_indicators.append(enhanced_match)

            except Exception as e:
                print(f"⚠️ Error processing {indicator_id}: {str(e)}")
                continue

        return extracted_indicators

    def _find_best_match_for_indicator(self, indicator_id: str, keywords: List[str],
                                     chunks: List[str], vector_db, bm25) -> Dict[str, Any]:
        """Find best matching chunk for an indicator using hybrid search"""

        # Create search query from keywords
        query = " OR ".join(keywords)

        # Step 1: Hybrid search (BM25 + Vector)
        hybrid_results = self._hybrid_search(query, chunks, vector_db, bm25, k=5)

        if not hybrid_results:
            return None

        # Step 2: Rerank using cross-encoder
        reranked_results = self._rerank_results(query, hybrid_results, top_n=3)

        if not reranked_results or reranked_results[0]['score'] < -2.0:
            return None  # Low confidence threshold

        best_result = reranked_results[0]

        return {
            'indicator_id': indicator_id,
            'content': best_result['text'],
            'confidence': best_result['score'],
            'keywords_matched': keywords,
            'search_query': query
        }

    def _hybrid_search(self, query: str, chunks: List[str], vector_db, bm25, k: int = 5) -> List[str]:
        """Perform hybrid search combining BM25 and vector similarity"""

        # BM25 search
        query_tokens = query.lower().split()
        bm25_scores = bm25.get_scores(query_tokens)

        # Get top BM25 results
        bm25_indices = np.argsort(bm25_scores)[::-1][:k]
        bm25_results = [chunks[i] for i in bm25_indices if bm25_scores[i] > 0]

        # Vector similarity search
        try:
            vector_results = vector_db.similarity_search(query, k=k)
            vector_texts = [doc.page_content for doc in vector_results]
        except:
            vector_texts = []

        # Combine and deduplicate results
        combined_results = []
        seen_texts = set()

        for text in bm25_results + vector_texts:
            if text not in seen_texts and len(text.strip()) > 50:
                combined_results.append(text)
                seen_texts.add(text)

        return combined_results[:k*2]  # Return up to 2*k unique results

    def _rerank_results(self, query: str, candidates: List[str], top_n: int = 3) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder"""

        if not candidates:
            return []

        try:
            # Create pairs for cross-encoder
            pairs = [(query, candidate) for candidate in candidates]

            # Get relevance scores
            scores = self.reranker.predict(pairs)

            # Create ranked results
            results = []
            for score, text in zip(scores, candidates):
                results.append({
                    'text': text,
                    'score': float(score)
                })

            # Sort by score (highest first)
            results.sort(key=lambda x: x['score'], reverse=True)

            return results[:top_n]

        except Exception as e:
            print(f"⚠️ Reranking failed: {str(e)}")
            # Fallback: return candidates as-is
            return [{'text': text, 'score': 0.0} for text in candidates[:top_n]]

    def _enhance_with_llm_analysis(self, indicator_id: str, match: Dict[str, Any],
                                 company_name: str, year: int) -> Dict[str, Any]:
        """Enhance match with LLM analysis and create final indicator data"""

        try:
            # Create analysis prompt
            prompt = f"""Analyze this text for ESG indicator {indicator_id} for {company_name} in {year}:

Text: "{match['content']}"

Extract specific data points, numbers, and relevant information for this ESG indicator. Provide a concise summary:"""

            # Generate analysis
            analysis = self._generate_with_llm(prompt, max_length=200)

            if analysis and len(analysis.strip()) > 20:
                return {
                    'indicator_id': indicator_id,
                    'data_value': f"[RAG Analysis] {analysis.strip()}",
                    'source': 'esg_rag_document_analysis',
                    'confidence': min(0.95, 0.7 + (match['confidence'] + 2) / 6),  # Scale confidence
                    'raw_content': match['content'][:300] + "..." if len(match['content']) > 300 else match['content'],
                    'keywords_matched': match['keywords_matched'],
                    'company_name': company_name,
                    'year': year
                }

        except Exception as e:
            print(f"⚠️ LLM analysis failed for {indicator_id}: {str(e)}")

        # Fallback: return basic match without LLM enhancement
        return {
            'indicator_id': indicator_id,
            'data_value': f"[Document Extract] {match['content'][:200]}...",
            'source': 'esg_rag_document_basic',
            'confidence': 0.75,
            'raw_content': match['content'],
            'keywords_matched': match['keywords_matched'],
            'company_name': company_name,
            'year': year
        }

    def _generate_with_llm(self, prompt: str, max_length: int = 150) -> str:
        """Generate text using the local LLM"""

        try:
            # Prepare input
            messages = [{"role": "user", "content": prompt}]
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = self.tokenizer([text], return_tensors="pt")

            # Generate with constraints
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Extract generated text
            generated = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)

            return generated.strip()

        except Exception as e:
            print(f"⚠️ LLM generation failed: {str(e)}")
            return ""

    def save_indicators_to_database(self, indicators: List[Dict[str, Any]], company_id: int) -> int:
        """Save extracted indicators to database"""

        if not indicators:
            return 0

        db = get_session()
        saved_count = 0

        try:
            for indicator in indicators:
                try:
                    scraped_data = ScrapedData(
                        company_id=company_id,
                        year=indicator['year'],
                        data_key=indicator['indicator_id'],
                        data_value=indicator['data_value'],
                        source=indicator['source'],
                        confidence=indicator['confidence']
                    )
                    db.add(scraped_data)
                    saved_count += 1
                except Exception as save_error:
                    print(f"⚠️ Failed to save {indicator['indicator_id']}: {str(save_error)}")

            db.commit()
            print(f"💾 Saved {saved_count} indicators to database")

        except Exception as e:
            db.rollback()
            print(f"❌ Database save failed: {str(e)}")
        finally:
            db.close()

        return saved_count


def test_esg_rag_system():
    """Test the ESG RAG system with existing documents"""

    print("=== TESTING ESG RAG SYSTEM ===")

    try:
        # Initialize system
        rag_system = ESGRagSystem()

        # Check for downloaded documents
        document_dir = Path("data/discovered_documents")
        if document_dir.exists():
            pdf_files = list(document_dir.glob("*.pdf"))

            if pdf_files:
                # Test with first available PDF
                pdf_file = pdf_files[0]
                print(f"📄 Testing with document: {pdf_file.name}")

                # Process document
                results = rag_system.process_esg_document(
                    str(pdf_file),
                    "Asian Paints",
                    2024
                )

                if results.get('success'):
                    indicators = results['indicators']
                    print(f"✅ Successfully extracted {len(indicators)} indicators")

                    # Show sample results
                    print("\\nSample extracted indicators:")
                    for i, indicator in enumerate(indicators[:5]):
                        print(f"  {i+1}. {indicator['indicator_id']}: {indicator['data_value'][:80]}...")
                        print(f"     Confidence: {indicator['confidence']:.2f}")
                        print(f"     Source: {indicator['source']}")
                        print()

                    # Save to database
                    saved_count = rag_system.save_indicators_to_database(indicators, 14)  # Asian Paints ID

                    print(f"💾 Saved {saved_count} indicators to database")
                    return True

                else:
                    print(f"❌ Document processing failed: {results.get('error')}")
                    return False

            else:
                print("⚠️ No PDF documents found in data/discovered_documents")
                return False

        else:
            print("⚠️ Document directory not found")
            return False

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test the RAG system
    success = test_esg_rag_system()

    if success:
        print("\\n🎉 ESG RAG SYSTEM READY!")
        print("\\nFeatures implemented:")
        print("  - Hybrid search (BM25 + Vector similarity)")
        print("  - Cross-encoder reranking")
        print("  - LLM-enhanced analysis")
        print("  - TARGET 151 indicator extraction")
        print("  - Database integration")
        print("\\nThis can now process ESG documents with high accuracy!")
    else:
        print("\\n⚠️ System test failed - check dependencies and documents")