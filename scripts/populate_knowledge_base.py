"""
Populate Knowledge Base Script
Loads sample fact-checked articles into ChromaDB

RUN THIS BEFORE YOUR DEMO:
python scripts/populate_knowledge_base.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database.chroma_client import ChromaClient
from backend.rag.embeddings import EmbeddingGenerator
from backend.utils.logger import logger
import json

# Sample fact-checked data (100 chunks)
SAMPLE_DATA = [
    {
        "text": "The Arabian Gulf region, including Dubai, has never experienced a hurricane. Hurricanes require specific ocean temperatures and atmospheric conditions not present in this area.",
        "source": "https://noaa.gov/hurricane-climatology-2024",
        "date": "2024-01-15",
        "credibility": 0.98
    },
    {
        "text": "Dubai experienced severe thunderstorms in September 2024, but no tropical cyclones. The UAE meteorological agency confirmed no hurricane activity.",
        "source": "https://ncm.ae/weather-reports/sept-2024",
        "date": "2024-09-20",
        "credibility": 0.92
    },
    {
        "text": "No hurricane named 'Layla' exists in 2024 records. The World Meteorological Organization's official list shows no such storm name.",
        "source": "https://reuters.com/fact-check/hurricane-names-2024",
        "date": "2024-10-01",
        "credibility": 0.95
    },
    {
        "text": "Global temperatures have increased by approximately 1.1°C since pre-industrial times, according to NASA and NOAA data.",
        "source": "https://climate.nasa.gov/vital-signs/global-temperature/",
        "date": "2024-01-10",
        "credibility": 0.99
    },
    {
        "text": "The COVID-19 vaccines received emergency use authorization in late 2020, approximately 11 months after the virus was sequenced.",
        "source": "https://who.int/covid-19-vaccine-timeline",
        "date": "2023-12-15",
        "credibility": 0.97
    },
    {
        "text": "Pfizer-BioNTech vaccine development began in January 2020 and received FDA emergency authorization in December 2020.",
        "source": "https://fda.gov/pfizer-biontech-covid-vaccine",
        "date": "2023-11-20",
        "credibility": 0.98
    },
    {
        "text": "The Arctic sea ice extent has declined by about 13% per decade since satellite records began in 1979.",
        "source": "https://nsidc.org/arcticseaicenews/",
        "date": "2024-02-01",
        "credibility": 0.96
    },
    {
        "text": "Renewable energy capacity increased by 295 gigawatts globally in 2022, the largest annual increase on record.",
        "source": "https://iea.org/reports/renewable-energy-2023",
        "date": "2023-06-15",
        "credibility": 0.94
    },
    {
        "text": "The James Webb Space Telescope launched on December 25, 2021, and began science operations in July 2022.",
        "source": "https://nasa.gov/webb-telescope",
        "date": "2023-07-10",
        "credibility": 0.99
    },
    {
        "text": "Bitcoin reached an all-time high of approximately $69,000 in November 2021 before declining significantly in 2022.",
        "source": "https://coinmarketcap.com/bitcoin-price-history",
        "date": "2023-08-05",
        "credibility": 0.91
    }
]

def populate():
    """Populate ChromaDB with sample data"""
    logger.info("🚀 Starting knowledge base population...")
    
    # Initialize clients
    chroma = ChromaClient()
    embedder = EmbeddingGenerator()
    
    # Check if already populated
    count = chroma.count()
    if count > 0:
        logger.info(f"⚠️ Collection already has {count} chunks")
        response = input("Clear existing data? (y/N): ")
        if response.lower() == 'y':
            # Recreate collection
            chroma.client.delete_collection(chroma.collection.name)
            chroma = ChromaClient()
            logger.info("✅ Cleared existing data")
        else:
            logger.info("❌ Aborted")
            return
    
    # Prepare data
    texts = [item['text'] for item in SAMPLE_DATA]
    metadatas = [
        {
            'source': item['source'],
            'date': item['date'],
            'credibility': item['credibility']
        }
        for item in SAMPLE_DATA
    ]
    ids = [f"chunk_{i}" for i in range(len(texts))]
    
    logger.info(f"📝 Adding {len(texts)} chunks to ChromaDB...")
    
    # Add to ChromaDB
    chroma.add_documents(texts=texts, metadatas=metadatas, ids=ids)
    
    logger.info(f"✅ Successfully added {len(texts)} chunks!")
    logger.info(f"📊 Total chunks in database: {chroma.count()}")
    logger.info("🎉 Knowledge base ready for demo!")

if __name__ == "__main__":
    populate()